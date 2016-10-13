from __future__ import absolute_import

import sys

import click

from raincoat.raincoat import Raincoat

__version__ = "0.2.0"


@click.command()
@click.option('--path', default=".", help='Path to analyze (default.')
def main(path):
    inst = Raincoat()

    inst.raincoat(path)

    for error, match in inst.errors:
        code_object = match.code_object or "whole module"
        click.echo(
            "{match.package} == {match.version} vs {match.other_version} "
            "@ {match.path}:{code_object} "
            "(from {match.filename}:{match.lineno})".format(
                match=match, code_object=code_object))
        click.echo(error)
        click.echo()

    sys.exit(len(inst.errors))
