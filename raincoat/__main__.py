from __future__ import annotations

from raincoat import cli


def main(name):
    # The curse of 100% coverage
    if name == "__main__":
        cli.cli()


main(__name__)
