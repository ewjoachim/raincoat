from __future__ import absolute_import

import sys

import click

from raincoat.raincoat import Raincoat

__version__ = "0.6.0"

CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}

def main(path):
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path', nargs=-1, type=click.Path(exists=True))
    """
    Analyze your code to find outdated copy-pasted snippets.
    "Raincoat has you covered when your code is not DRY."

    Full documentation at http://raincoat.readthedocs.io/en/latest/
    """
    raincoat = Raincoat()
    if not path:
        path = ["."]

    errors = list(raincoat.raincoat(path=element) for element in path)
    for error, match in errors:
        click.echo(match)
        click.echo(error)
        click.echo()

    sys.exit(int(bool(errors)))
