from __future__ import absolute_import

import sys

import click

from raincoat.raincoat import Raincoat

__version__ = "0.6.0"


@click.command()
@click.option('--path', default=".", help='Path to analyze (default is "." )')
def main(path):
    raincoat = Raincoat()

    errors = list(raincoat.raincoat(path=path))
    for error, match in errors:
        click.echo(match)
        click.echo(error)
        click.echo()

    sys.exit(int(bool(errors)))
