from __future__ import annotations

import argparse
import logging
import pathlib
import sys
import textwrap

from raincoat import exceptions, types

from . import raincoat
from . import settings as settings_module

logger = logging.getLogger(__name__)


def get_log_level(verbosity: int) -> int:
    """
    Given the number of repetitions of the flag -v,
    returns the desired log level
    """
    mapping = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    return mapping.get(min((max(mapping), verbosity)), 0)


def setup_logging(verbosity: int) -> None:
    level = get_log_level(verbosity=verbosity)
    logging.basicConfig(level=level)
    level_name = logging.getLevelName(level)
    logger.debug(f"Log level set to {level_name}")


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Raincoat has you covered when you can't stay DRY. "
        "Track and update copied code from third-party sources.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=None,
        help="Path to the raincoat.toml config file (default: raincoat.toml if it "
        "exists or pyproject.toml). If neither exists, only read inline comments.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Command to run",
    )

    check = subparsers.add_parser(
        "check",
        help="Update checks, fail if the code has changed. "
        "When the updater reports a new version, the check command updates the "
        "configuration to the new version. "
        "If there's a diff detected, it keeps the old version as 'old_version=...'. "
        "By default, the check command includes only internal updaters. ",
    )
    check.add_argument(
        "--with-external",
        action="store_true",
        help="If set, also check external updaters.",
    )
    check.add_argument(
        "--manual",
        action="append",
        dest="checks",
        metavar="CHECK_NAME[=VERSION]",
        type=make_manual_updates,
        help=(
            "Limit to the specified check. "
            "If a version is provided, updater will be skipped (if there's one). "
            "This is the main way to update checks that don't have an updater. "
            "Option may be provided mutile times."
        ),
    )
    check.add_argument(
        "--no-fail-if-diff",
        dest="fail_if_diff",
        action="store_false",
        default=True,
        help=(
            "If set, and the checks find a new version with diff, they will be "
            "updated but the command won't fail."
        ),
    )
    check.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help=(
            "Files to check. If not specified, all files in the current directory are "
            "checked."
        ),
    )

    fix = subparsers.add_parser(
        "fix",
        help="Remove the 'old_version' attribute from checks that have it set. "
        "You should only run this command *after* you have verified the diff using the "
        "check command and made the relevant changes to your code.",
    )
    fix.add_argument(
        "checks",
        nargs="*",
        metavar="CHECK",
        help="The checks to fix (by default: all checks)",
    )

    return parser


def make_manual_updates(value: str):
    name, *version = value.split("=", maxsplit=1)
    return types.ManualUpdate(name=name, version=version[0] if version else None)


def find_config(
    manual_config: pathlib.Path | None,
) -> pathlib.Path | None:
    if manual_config:
        return manual_config

    cwd = pathlib.Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (pyproject := (parent / "pyproject.toml")).exists():
            return pyproject
        if (raincoat := (parent / "raincoat.toml")).exists():
            return raincoat

    return None


class CLIReporter:
    def __init__(self, fail_if_diff: bool = True, verbosity: int = 0):
        self.fail_if_diff = fail_if_diff
        self.exit_code = 0
        self.previous_path: pathlib.Path | None = None
        self.verbosity = verbosity

    def print(
        self,
        message,
        *,
        verbosity: int = 0,
        path: pathlib.Path,
        check_name: str,
    ):
        if self.verbosity < verbosity:
            return

        if path != self.previous_path:
            self.previous_path = path
            print(f"{path}:")

        print(f"   {check_name}: {message}")

    def on_check_result(self, result: types.CheckResult):
        name = result.check.name

        if result.error:
            self.exit_code = 1
            if result.error.plugin_type == "other":
                error_text = "Unexpected Raincoat Error"
            else:
                error_text = f"Error in {result.error.plugin_type} plugin"

            self.print(
                f"{error_text} (for traceback, use -vv): {result.error.error}",
                path=result.check.path,
                check_name=name,
            )

            return

        if result.skipped == types.SkippedReason.NO_UPDATER:
            self.print(
                "No updater defined, this check can only be updated manually "
                '("raincoat check --manual")',
                verbosity=1,
                path=result.check.path,
                check_name=name,
            )
            return
        if result.skipped == types.SkippedReason.EXTERNAL_UPDATER:
            self.print(
                "Updater didn't run because it checks for external resources, "
                'and this is disabled unless "--with-external" is used',
                verbosity=1,
                path=result.check.path,
                check_name=name,
            )
            return

        if result.new_version is None:
            self.print(
                "No new version detected",
                verbosity=1,
                path=result.check.path,
                check_name=name,
            )
            return

        if result.diff is None and not result.check.update_if_no_diff:
            self.print(
                "New version detected, but it has no diff, and "
                '"update_if_no_diff" is True, skipping the update',
                verbosity=1,
                path=result.check.path,
                check_name=name,
            )
            return

        if result.diff is None:
            self.print(
                f'New version "{result.new_version}" available, no diff. '
                "Updating raincoat configuration.",
                verbosity=0,
                path=result.check.path,
                check_name=name,
            )
            return

        if self.fail_if_diff:
            self.exit_code = 1

        self.print(
            f"""New version "{result.new_version}" available, with diff detected. Please check the diff with `raincoat check` then use `raincoat fix`.

   Diff:
{textwrap.indent(result.diff.strip(), "   ")}""",
            verbosity=0,
            path=result.check.path,
            check_name=name,
        )

    def on_update_result(self, result: types.UpdateResult):
        if not result.old_version and not result.new_version:
            self.print(
                "Nothing to report",
                verbosity=2,
                check_name=result.name,
                path=result.path,
            )
            return

        if result.old_version:
            if result.new_version is None:
                raise exceptions.InconsistentState(name=result.name)
            self.print(
                f'diff between "{result.old_version}" and "{result.new_version}"',
                verbosity=0,
                check_name=result.name,
                path=result.path,
            )
            return

        self.print(
            f'updated to "{result.new_version}" (without diff)',
            verbosity=0,
            check_name=result.name,
            path=result.path,
        )
        return

    def on_fix(self, result: types.UpdateResult):
        self.print(
            f'validated version "{result.new_version}"',
            verbosity=0,
            check_name=result.name,
            path=result.path,
        )


def cli_check(
    settings: types.Settings,
    manual_updates: list[types.ManualUpdate] | None = None,
    with_external: bool = False,
    fail_if_diff: bool = True,
    verbosity: int = 0,
) -> int:
    reporter = CLIReporter(fail_if_diff=fail_if_diff, verbosity=verbosity)
    raincoat.run_check_and_update(
        settings=settings,
        manual_updates=manual_updates,
        with_external=with_external,
        reporter=reporter,
    )
    return reporter.exit_code


def cli_fix(
    settings: types.Settings,
    checks: list[str],
    verbosity: int = 0,
) -> int:
    raincoat.run_fix(
        settings=settings, checks=checks, reporter=CLIReporter(verbosity=verbosity)
    )
    return 0


def cli(argv, additional_plugins: types.AdditionalPlugins | None = None) -> int:
    args = get_argument_parser().parse_args(argv)
    setup_logging(args.verbose)

    config_path = find_config(args.config)

    settings = settings_module.load_from_toml_file_and_comments(
        config_path=config_path,
        root_dir=pathlib.Path("."),
        # files is only defined for command `check` (to help pre-commit)
        files=getattr(args, "files", None),
        additional_plugins=additional_plugins,
    )

    if args.command in "check":
        return cli_check(
            settings=settings,
            manual_updates=args.checks,
            with_external=args.with_external,
            fail_if_diff=args.fail_if_diff,
            verbosity=args.verbose,
        )

    assert args.command == "fix"
    return cli_fix(
        settings=settings,
        checks=args.checks,
        verbosity=args.verbose,
    )


def run_cli(func=cli, argv=sys.argv[1:]):
    sys.exit(func(argv))
