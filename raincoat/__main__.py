from __future__ import annotations

from . import cli


def main(name, run=cli.run_cli):
    if name == "__main__":
        run()


main(__name__)
