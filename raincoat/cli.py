from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import sys

from . import raincoat
from . import settings as settings_module

logger = logging.getLogger(__name__)


def get_log_level(verbosity: int) -> int:
    """
    Given the number of repetitions of the flag -v,
    returns the desired log level
    """
    return {0: logging.INFO, 1: logging.DEBUG}.get(min((1, verbosity)), 0)


def setup_logging(verbosity: int) -> None:
    level = get_log_level(verbosity=verbosity)
    logging.basicConfig(level=level)
    level_name = logging.getLevelName(level)
    logger.debug(
        f"Log level set to {level_name}",
        extra={"action": "set_log_level", "value": level_name},
    )


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
        default=pathlib.Path("raincoat.toml"),
        help="Path to the raincoat.toml config file (default: raincoat.toml if it exists or pyproject.toml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update version numbers in raincoat.toml after verifying changes",
    )
    update_parser.add_argument(
        "--check-for-updates",
        action="store_true",
        help="Fail if there are new updates available, even if code is unchanged",
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        help="Force update version in TOML config file even if code has changed. "
        "Exit code will still be 1 if code has changed.",
    )
    update_parser.add_argument(
        "manual_checks",
        nargs="*",
        metavar="CHECK_NAME=VERSION",
        help=(
            "Optional list of check names to manally update. "
            "Use this for check that don't have an updater set. "
            "If set, only these checks will be updated."
        ),
    )

    return parser


async def cli(argv) -> int:
    # Parse all arguments
    args = get_argument_parser().parse_args(argv)
    setup_logging(args.verbose)  # Note: there's a typo in the function name

    config_path = args.config
    if not config_path.exists():
        config_path = pathlib.Path("pyproject.toml")
    if not config_path.exists():
        logger.error(
            "Configuration file not found: %s. "
            "Please create a raincoat.toml or pyproject.toml file, or specify a different path with --config.",
            config_path,
        )
        return 1

    settings = settings_module.load_from_toml_file(config_path=config_path)

    manual_checks = None
    if args.manual:
        manual_checks = dict(name.split("=") for name in args.manual)

    exit_code = 0
    updates = {}
    async for result in raincoat.update(
        checks=settings.checks,
        manual_checks=manual_checks,
    ):
        name = result.check.name
        if not result.has_new_version:
            logger.info(f"{name}: ✅ No new version available")
        elif result.diff is None:
            if args.check_for_updates:
                logger.error(f"{name}: ❌ New version {result.new_version} available")
                exit_code = 1
            else:
                logger.info(
                    f"{name}: ✅ New version {result.new_version} available, no diff."
                )
                updates[name] = result.new_version
        else:
            exit_code = 1
            if args.force:
                logger.info(
                    f"{name}: ❌ New version {result.new_version} available, "
                    "with diff detected. Proceeding with update due to --force."
                )
                updates[name] = result.new_version
            else:
                logger.error(
                    f"{name}: ❌ New version {result.new_version} available, "
                    "with diff detected. Please update manually once changes are verified, or use --force to update anyway."
                )
            exit_code = 1

    if updates:
        settings_module.update_versions(settings=settings, updates=updates)
        logger.info(
            f"✨ Updated versions in {config_path.name}: "
            f"{(', '.join(f'{name}={version}' for name, version in updates.items()))}",
        )

    return exit_code


def run_cli():
    sys.exit(asyncio.run(cli(sys.argv[1:])))
