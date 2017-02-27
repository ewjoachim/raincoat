from raincoat import main, __main__


def test_cli(cli_runner, mocker, match):

    raincoat = mocker.patch("raincoat.raincoat")

    match.other_version = "2.0.0"
    raincoat.return_value = [
        "Oh :("
    ]
    result = cli_runner.invoke(main, ["--no-color"])
    exc = result.exception

    if exc and not isinstance(exc, SystemExit):
        raise exc

    assert result.output == ("Oh :(\n")
    assert result.exit_code == 1


def test_cli_path(cli_runner, mocker, match):

    raincoat = mocker.patch("raincoat.raincoat")

    cli_runner.invoke(main, ["tests", "raincoat", "--exclude=*.py"])

    assert raincoat.mock_calls[0] == (
        mocker.call.raincoat(path="tests", exclude=("*.py",), color=False))

    assert raincoat.mock_calls[2] == (
        mocker.call.raincoat(path="raincoat", exclude=("*.py",), color=False))


# Yeah, I realize how ridiculous it can be, but eh.
def test_main_imported(mocker):
    main = mocker.patch("raincoat.__main__.main")
    __main__.launch("bla")
    assert main.mock_calls == []


def test_main_executed(mocker):
    main = mocker.patch("raincoat.__main__.main")
    __main__.launch("__main__")
    assert main.mock_calls == [mocker.call()]
