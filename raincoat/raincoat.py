from __future__ import annotations

import difflib
import logging
from collections.abc import AsyncGenerator

from . import types

logger = logging.getLogger(__name__)


async def update(
    *,
    checks: dict[str, types.Check],
    manual_checks: dict[str, str] | None = None,
) -> AsyncGenerator[types.UpdateResult]:
    """
    Update version numbers in raincoat.toml after verifying changes.

    Parameters
    ----------
    checks : dict[str, types.Check]
        Mapping of checks to update. (name -> Check)
    manual_checks : dict[str, str] | None
        Optional mapping of check names to versions for manual updates.
    """
    manual_checks = manual_checks or {}

    if manual_checks:
        check_names = manual_checks.keys()
    else:
        check_names = checks.keys()

    # First collect all updates (without applying them yet)
    for check_name, check in checks.items():
        if check_name not in check_names:
            continue

        try:
            yield await update_check(
                check=check,
                manual_version=manual_checks.get(check_name),
            )
        except Exception as exc:
            logger.exception(f"Error updating check {check_name}: {exc}")
            continue


async def update_check(
    check: types.Check,
    manual_version: str | None = None,
) -> types.UpdateResult:
    """
    Update a single check and return the result.

    Parameters
    ----------
    check : types.Check
        The check to update.
    manual_version : str | None
        Optional manual version to set instead of checking for updates.

    Returns
    -------
    types.UpdateResult
        The result of the update operation.
    """

    # Get the latest version from the updater
    if manual_version:
        new_version = manual_version
        logger.debug(f"Version for check {check.name} set manually to {new_version}")

    elif check.updater:
        new_version = await check.updater.function(
            **{
                **check.source.config,  # Base config from source
                **check.updater.config,  # Updater config overrides
            }
        )
    else:
        logger.debug(
            f"No updater configured for check {check.name}, skipping version check"
        )
        return types.UpdateResult(
            check=check,
            new_version=check.version,
            diff=None,
        )

    # Skip if version hasn't changed
    if new_version == check.version:
        logger.debug(f"Check {check.name} is up to date (version {check.version})")
        return types.UpdateResult(
            check=check,
            new_version=new_version,
            diff=None,
        )

    # Get both versions of the code
    logger.debug(f"Fetching code for version {check.version}")
    ref_code = await check.source.function(
        version=check.version,
        **check.source.config,
    )

    logger.debug(f"Fetching code for version {new_version}")
    try:
        new_code = await check.source.function(
            version=new_version,
            **check.source.config,
        )
    except Exception as exc:
        # If fetching new code fails, treat it as removed
        logger.error(
            f"Failed to fetch new code for check '{check.name}' version '{new_version}': {exc}"
        )
        new_code = ""

    # Compare the code
    if check.diff:
        diff = await check.diff.function(
            ref=ref_code,
            new=new_code,
            **check.diff.config,
        )
    else:
        diff = await default_diff_function(
            ref=ref_code,
            new=new_code,
        )

    return types.UpdateResult(
        check=check,
        new_version=new_version,
        diff=diff,
    )


async def default_diff_function(*, ref: str, new: str) -> str | None:
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
