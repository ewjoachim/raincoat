"""
Raincoat has you covered when you code is not dry.

Project homepage is https://github.com/novafloss/raincoat/

Documentation available at
http://raincoat.readthedocs.io/en/latest/?badge=latest

Done with :heart: by Joachim "ewjoachim" Jablon, with support
from Smart Impulse and PeopleDoc

Thank you for using this package !

MIT License - Copyright (c) 2016, Joachim Jablon
Full license text available at
https://github.com/novafloss/raincoat/blob/master/LICENSE

up up down down left right left right b a
"""

from __future__ import absolute_import

import sys

import click

from .glue import raincoat


CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


def print_version(ctx, __, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo("Raincoat version {}".format(__version__))
    ctx.exit()


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path', nargs=-1, type=click.Path(exists=True))
@click.option('-e', '--exclude', multiple=True,
              help="Files and folders to exclude (e.g. 'test_*')")
@click.option('-c/-nc', '--color/--no-color', default=None,
              help="Should output be colorized ? (default : yes for TTYs)")
@click.option('--version', '-v', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def main(path, exclude=None, color=True):
    """
    Analyze your code to find outdated copy-pasted snippets.
    "Raincoat has you covered when your code is not DRY."

    Full documentation at http://raincoat.readthedocs.io/en/latest/
    """
    if not path:
        path = ["."]

    if color is None:
        color = sys.stdout.isatty()

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


def _extract_version(package_name):
    try:
        import pkg_resources
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        from setuptools.config import read_configuration
        from os import path as _p
        _conf = read_configuration(
            _p.join(_p.dirname(_p.dirname(__file__)),
                    "setup.cfg"))
        return _conf["metadata"]["version"]


__version__ = _extract_version("raincoat")
