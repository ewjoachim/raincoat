from __future__ import absolute_import

import sys

import click

from raincoat.raincoat import Raincoat

__version__ = "0.6.0"

CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path', nargs=-1, type=click.Path(exists=True))
@click.option('--exclude', '-e', multiple=True,
              help="Files and folders to exclude (e.g. 'test_*')")
def main(path, exclude=None):
    """
    Analyze your code to find outdated copy-pasted snippets.
    "Raincoat has you covered when your code is not DRY."

    Full documentation at http://raincoat.readthedocs.io/en/latest/
    """
    raincoat = Raincoat()
    if not path:
        path = ["."]

    errors = list(error_match
                  for element in path
                  for error_match in raincoat.raincoat(path=element,
                                                       exclude=exclude))
    for error, match in errors:
        click.echo(match)
        click.echo(error)
        click.echo()

    sys.exit(int(bool(errors)))
