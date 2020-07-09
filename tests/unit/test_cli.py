import logging

import click
import pytest

from raincoat import cli, exceptions


@pytest.mark.parametrize(
    "verbosity, log_level", [(0, "INFO"), (1, "DEBUG"), (2, "DEBUG")]
)
def test_get_log_level(verbosity, log_level):
    assert cli.get_log_level(verbosity=verbosity) == getattr(logging, log_level)


def test_set_verbosity(mocker, caplog):
    config = mocker.patch("logging.basicConfig")

    caplog.set_level("DEBUG")

    cli.set_verbosity(1)

    config.assert_called_once_with(level=logging.DEBUG)
    records = [record for record in caplog.records if record.action == "set_log_level"]
    assert len(records) == 1
    assert records[0].value == "DEBUG"


@pytest.mark.parametrize(
    "raised, expected",
    [
        # Package exception are caught
        (exceptions.RaincoatException, click.ClickException),
        # Other exceptions are not
        (ValueError, ValueError),
    ],
)
def test_handle_errors(raised, expected):
    @cli.handle_errors()
    def raise_exc():
        raise exceptions.RaincoatException("foo") from IndexError("bar")

    with pytest.raises(click.ClickException) as exc:
        raise_exc()

    assert str(exc.value) == "foo\nbar"


def test_handle_errors_no_error():
    @cli.handle_errors()
    def raise_exc():
        assert True

    raise_exc()


def test_main(mocker):

    environ = mocker.patch("os.environ", {"LANG": "fr-FR.UTF-8"})
    mocker.patch("raincoat.cli.cli")
    cli.main()

    assert environ == {"LANG": "fr-FR.UTF-8", "LC_ALL": "C.UTF-8"}


def test_cli(cli_runner, mocker, match):

    raincoat = mocker.patch("raincoat.glue.raincoat")

    match.other_version = "2.0.0"
    raincoat.return_value = ["Oh :("]
    result = cli_runner.invoke(cli.cli, ["--no-color"])
    exc = result.exception

    if exc and not isinstance(exc, SystemExit):
        raise exc

    assert result.output == ("Oh :(\nError: Inconsistencies were found.\n")
    assert result.exit_code == 1


def test_cli_path(cli_runner, mocker, match):

    raincoat = mocker.patch("raincoat.glue.raincoat")

    cli_runner.invoke(cli.cli, ["tests", "raincoat", "--exclude=*.py"])

    assert raincoat.mock_calls[0] == (
        mocker.call.raincoat(path="tests", exclude=("*.py",), color=False)
    )

    assert raincoat.mock_calls[2] == (
        mocker.call.raincoat(path="raincoat", exclude=("*.py",), color=False)
    )
