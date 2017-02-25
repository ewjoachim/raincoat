from __future__ import absolute_import

import sys

import click

from .glue import raincoat

__version__ = "0.6.0"

CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path', nargs=-1, type=click.Path(exists=True))
@click.option('--exclude', '-e', multiple=True,
              help="Files and folders to exclude (e.g. 'test_*')")
@click.option('-c/-nc', '--color/--no-color', default=True,
              help="Should output be colorized ? (default : yes)")
def main(path, exclude=None, color=True):
    """
    Analyze your code to find outdated copy-pasted snippets.
    "Raincoat has you covered when your code is not DRY."

    Full documentation at http://raincoat.readthedocs.io/en/latest/
    """
    if not path:
        path = ["."]

    errors = (error_match
              for element in path
              for error_match in raincoat(path=element,
                                          exclude=exclude,
                                          color=color))
    has_errors = False
    for line in errors:
        has_errors = True
        click.echo(line)

    sys.exit(int(has_errors))
