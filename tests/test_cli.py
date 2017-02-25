from raincoat import main, __main__


def test_cli(cli_runner, mocker, match):

    raincoat_class = mocker.patch("raincoat.Raincoat")

    raincoat = raincoat_class.return_value

    match.other_version = "2.0.0"
    raincoat.raincoat.return_value = [
        ("Oh :(", match)
    ]
    result = cli_runner.invoke(main)
    assert result.output == ("umbrella == 3.2 vs 2.0.0 @ "
                             "path/to/file.py:MyClass (from filename:12)\n"
                             "Oh :(\n\n")
    assert result.exit_code == 1


def test_cli_path(cli_runner, mocker, match):

    raincoat_class = mocker.patch("raincoat.Raincoat")

    print(cli_runner.invoke(main, ["tests", "raincoat", "--exclude=*.py"]))
    assert raincoat_class.return_value.mock_calls[0] == (
        mocker.call.raincoat(path="tests", exclude=("*.py",)))

    assert raincoat_class.return_value.mock_calls[2] == (
        mocker.call.raincoat(path="raincoat", exclude=("*.py",)))


# Yeah, I realize how ridiculous it can be, but eh.
def test_main_imported(mocker):
    main = mocker.patch("raincoat.__main__.main")
    __main__.launch("bla")
    assert main.mock_calls == []


def test_main_executed(mocker):
    main = mocker.patch("raincoat.__main__.main")
    __main__.launch("__main__")
    assert main.mock_calls == [mocker.call()]
