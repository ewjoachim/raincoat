from __future__ import annotations

import difflib
import logging
from collections.abc import Generator

from raincoat import settings as settings_module

from . import types

logger = logging.getLogger(__name__)


def default_diff_function(*, ref: str, new: str) -> str | None:
    """
    The default diff plugin that simply compares two strings.

    Parameters
    ----------
    ref:
        The reference code
    new:
        The new code

    Returns
    -------
    str | None
        A unified diff if the strings are different, None if they're identical
    """
    if ref == new:
        return None

    diff = difflib.unified_diff(
        ref.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile="ref",
        tofile="new",
    )
    return "".join(diff)


def check_single(
    check: types.Check,
    manual_version: str | None = None,
) -> types.CheckResult:
    # Get the latest version from the updater
    old_version = check.version
    if manual_version:
        new_version = manual_version
        logger.debug(f"Version for check {check.name} set manually to {new_version}")

    elif check.old_version:
        old_version = check.old_version
        new_version = check.version

    elif check.updater:
        updater_input = {
            **check.source.config,  # Base config from source
            **check.updater.config,  # Updater config overrides
        }
        try:
            new_version = check.updater.function(**updater_input)
        except Exception as exc:
            logger.debug("Exception", exc_info=True)
            logger.error(
                f'Exception while running updater plugin "{check.updater.name}" for '
                f'"{check.name}": {exc}'
            )
            return types.CheckResult(
                check=check,
                error=types.CheckError(plugin_type="updater", error=str(exc)),
            )
    else:
        logger.debug(
            f"No updater configured for check {check.name}, skipping version check"
        )
        return types.CheckResult(
            check=check,
            skipped=types.SkippedReason.NO_UPDATER,
        )

    # Skip if version hasn't changed
    if old_version == new_version:
        logger.debug(f"Check {check.name} is up to date (version {new_version})")
        return types.CheckResult(check=check)

    # Get both versions of the code
    logger.debug(f"Fetching code for version {old_version}")
    try:
        ref_code = check.source.function(version=old_version, **check.source.config)
    except Exception as exc:
        logger.debug("Exception", exc_info=True)
        logger.error(
            f'Exception while running source plugin "{check.source.name}" for '
            f'"{check.name}" with version "{old_version}": {exc}'
        )
        return types.CheckResult(
            check=check, error=types.CheckError(plugin_type="source", error=str(exc))
        )
    logger.debug(f"Fetching code for version {new_version}")
    try:
        new_code = check.source.function(
            version=new_version,
            **check.source.config,
        )
    except Exception as exc:
        # If fetching new code fails, treat it as removed
        logger.debug("Exception", exc_info=True)
        logger.error(
            f'Exception while running source plugin "{check.source.name}" for '
            f'"{check.name}" with version "{new_version}": {exc} '
            "(assuming this means the code has disappeared)"
        )
        new_code = ""

    # Compare the code
    if check.diff:
        try:
            diff = check.diff.function(ref=ref_code, new=new_code, **check.diff.config)
        except Exception as exc:
            logger.debug("Exception", exc_info=True)
            logger.error(
                f'Exception while running diff plugin "{check.diff.name}" for '
                f'"{check.name}" with version "{old_version}": {exc}'
            )
            return types.CheckResult(
                check=check,
                error=types.CheckError(plugin_type="diff", error=str(exc)),
            )

    else:
        diff = default_diff_function(
            ref=ref_code,
            new=new_code,
        )

    return types.CheckResult(
        check=check,
        new_version=new_version,
        diff=diff,
    )


def check(
    *,
    checks: dict[str, types.Check],
    manual_updates: list[types.ManualUpdate] | None = None,
    include_external_updaters: bool = True,
) -> Generator[types.CheckResult]:
    """
    Update version numbers in raincoat.toml after verifying changes.

    Parameters
    ----------
    checks : dict[str, types.Check]
        Mapping of checks to update. (name -> Check)
    manual_checks : dict[str, str] | None
        Optional mapping of check names to versions for manual updates.
    """

    manual_mapping = {e.name: e.version for e in manual_updates or []}
    if manual_updates:
        check_names = manual_mapping.keys()
    else:
        check_names = checks.keys()

    for check_name, check in checks.items():
        if check_name not in check_names:
            continue

        if not include_external_updaters and check.updater and check.updater.external:
            yield types.CheckResult(
                check=check, skipped=types.SkippedReason.EXTERNAL_UPDATER
            )
            continue

        try:
            yield check_single(
                check=check, manual_version=manual_mapping.get(check_name)
            )
        except Exception as exc:
            error = str(exc)
            logger.debug("Exception", exc_info=True)
            logger.error(f'Error updating check "{check_name}": {error}')
            yield types.CheckResult(
                check=check,
                error=types.CheckError(error=error),
            )
            continue


def generate_update_instructions(
    check_result: types.CheckResult,
) -> types.UpdateInstructions:
    # UpdateInstructions and CheckResults do look a lot alike, but
    # they're different enough that it's easier to make separate objects.

    name = check_result.check.name
    update_instruction = types.UpdateInstructions(name=name)
    if check_result.error:
        return update_instruction

    if check_result.new_version is None:
        return update_instruction

    if check_result.diff is None and not check_result.check.update_if_no_diff:
        return update_instruction

    update_instruction.set_new_version = check_result.new_version

    if check_result.diff is None:
        return update_instruction

    update_instruction.set_old_version = check_result.check.version

    return update_instruction


def run_check_and_update(
    settings: types.Settings,
    manual_updates: list[types.ManualUpdate] | None = None,
    with_external: bool = False,
    reporter: types.CheckReporter | None = None,
) -> None:
    update_instructions: list[types.UpdateInstructions] = []
    for check_result in check(
        checks=settings.checks,
        manual_updates=manual_updates or [],
        include_external_updaters=with_external,
    ):
        if reporter:
            reporter.on_check_result(check_result)
        update_instruction = generate_update_instructions(check_result=check_result)
        update_instructions.append(update_instruction)

    for update_result in sorted(
        settings_module.update(
            settings=settings,
            update_instructions=update_instructions,
        ),
        key=lambda e: e.path,
    ):
        if reporter:
            reporter.on_update_result(update_result)


def run_fix(
    settings: types.Settings,
    checks: list[str],
    reporter: types.FixReporter | None = None,
) -> None:
    updates: list[types.UpdateInstructions] = []
    if not checks:
        checks = list(settings.checks)

    for check_name in checks:
        updates.append(types.UpdateInstructions(name=check_name, fix=True))

    for update_result in settings_module.update(
        settings=settings, update_instructions=updates
    ):
        if reporter:
            reporter.on_fix(update_result)
