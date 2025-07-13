from __future__ import annotations

import argparse
import logging
import sys

from . import raincoat

logger = logging.getLogger(__name__)


def get_log_level(verbosity: int) -> int:
    """
    Given the number of repetitions of the flag -v,
    returns the desired log level
    """
    return {0: logging.INFO, 1: logging.DEBUG}.get(min((1, verbosity)), 0)


def seetup_logging(verbosity: int) -> None:
    level = get_log_level(verbosity=verbosity)
    logging.basicConfig(level=level)
    level_name = logging.getLevelName(level)
    logger.debug(
        f"Log level set to {level_name}",
        extra={"action": "set_log_level", "value": level_name},
    )


def get_argument_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(
        description="TODO",
    )

    return arg_parser


def cli(argv) -> int:
    logging.basicConfig(
        level=get_log_level(argv.count("-v")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Parse all arguments
    arg_parser = get_argument_parser()
    arg_parser.parse_args(argv)

    asyncio.run(raincoat.run())

    return 0


def run_cli():
    sys.exit(cli(sys.argv[1:]))
