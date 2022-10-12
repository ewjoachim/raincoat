from __future__ import annotations

import contextlib
import logging
import os
import sys

import click

from raincoat import __version__, glue, utils

logger = logging.getLogger(__name__)

PROGRAM_NAME = "raincoat"
ENV_PREFIX = PROGRAM_NAME.upper()

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "auto_envvar_prefix": ENV_PREFIX,
}


def get_log_level(verbosity: int) -> int:
    """
    Given the number of repetitions of the flag -v,
    returns the desired log level
    """
    return {0: logging.INFO, 1: logging.DEBUG}.get(min((1, verbosity)), 0)


def click_set_verbosity(ctx: click.Context, param: click.Parameter, value: int) -> int:
    set_verbosity(verbosity=value)
    return value


def set_verbosity(verbosity: int) -> None:
    level = get_log_level(verbosity=verbosity)
    logging.basicConfig(level=level)
    level_name = logging.getLevelName(level)
    logger.debug(
        f"Log level set to {level_name}",
        extra={"action": "set_log_level", "value": level_name},
    )


@contextlib.contextmanager
def handle_errors():
    try:
        yield
    except Exception as exc:
        logger.debug("Exception details:", exc_info=exc)
        messages = [str(e) for e in utils.causes(exc)]
        raise click.ClickException("\n".join(e for e in messages if e))


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("path", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-e",
    "--exclude",
    multiple=True,
    help="Files and folders to exclude (e.g. 'test_*')",
)
@click.option(
    "-c/-nc",
    "--color/--no-color",
    default=None,
    help="Should output be colorized ? (default : yes for TTYs)",
)
@click.option(
    "-v",
    "--verbose",
    is_eager=True,
    callback=click_set_verbosity,
    count=True,
    help="Use multiple times to increase verbosity",
)
@click.version_option(__version__, "-V", "--version", prog_name=PROGRAM_NAME)
@handle_errors()
def cli(path, exclude, color, **kwargs):
    """
    Analyze your code to find outdated copy-pasted snippets.
    "Raincoat has you covered when your code is not DRY."

    Full documentation at http://raincoat.readthedocs.io/en/latest/
    """
    if not path:
        path = ["."]

    if color is None:
        color = sys.stdout.isatty()

    errors = (
        error_match
        for element in path
        for error_match in glue.raincoat(path=element, exclude=exclude, color=color)
    )
    has_errors = False
    for line in errors:
        has_errors = True
        click.echo(line)
    if has_errors:
        raise click.Abort("Inconsistencies were found.")


def main():
    # https://click.palletsprojects.com/en/7.x/python3/
    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")

    return cli()
