from __future__ import absolute_import

import sys

import click

from raincoat.raincoat import Raincoat


@click.command()
@click.option('--path', default=".", help='Path to analyze (default.')
def main(path):
    inst = Raincoat()

    inst.raincoat(path)

    for match, error in inst.errors:
        print(
            "{match.package} == {match.version} vs {match.other_version} "
            "@ {match.path}:{match.code_object} "
            "(from {match.filename}:{match.lineno})".format(match=match))
        print(error)

    sys.exit(len(inst.errors))
