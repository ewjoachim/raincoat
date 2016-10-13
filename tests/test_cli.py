from raincoat import main

from .test_raincoat import get_match


def test_cli(cli_runner, mocker):

    raincoat_class = mocker.patch("raincoat.Raincoat")

    raincoat = raincoat_class.return_value

    def add_errors(*args):
        match = get_match()
        match.other_version = "2.0.0"
        raincoat.errors = [
            ("Oh :(", match)
        ]

    raincoat.raincoat.side_effect = add_errors
    result = cli_runner.invoke(main)
    assert result.output == ("umbrella == 1.0.0 vs 2.0.0 @ "
                             "a/b.py:whole module (from file.py:23)\n"
                             "Oh :(\n\n")
    assert result.exit_code == 1
