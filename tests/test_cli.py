from raincoat import main


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
