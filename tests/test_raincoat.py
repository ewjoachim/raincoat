from raincoat.raincoat import Raincoat


def test_raincoat(mocker, match, match_module):
    find_in_dir = mocker.patch("raincoat.grep.find_in_dir")
    check_matches = mocker.patch("raincoat.raincoat.check_matches")

    find_in_dir.return_value = [match, match_module]

    raincoat = Raincoat()

    # Asserts are made in the check_matches method
    list(raincoat.raincoat("."))

    assert (
        check_matches.mock_calls[0] ==
        mocker.call({'pypi': [match, match_module]}))
