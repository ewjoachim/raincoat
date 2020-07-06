import pytest

from raincoat import __version__, cli


@pytest.fixture
def entrypoint(cli_runner):
    def ep(args=""):
        return cli_runner.invoke(cli.cli, args.split(), catch_exceptions=False)

    return ep


def test_cli(entrypoint):
    result = entrypoint()
    # assuming subcommand is required
    assert result.output.startswith("Usage:")


def test_version(entrypoint):
    result = entrypoint("--version")

    assert result.output.strip() == f"{cli.PROGRAM_NAME}, version {__version__}"
