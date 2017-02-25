from raincoat.glue import raincoat


def test_raincoat(mocker, match, match_module):
    mocker.patch("raincoat.grep.find_in_dir",
                 return_value=[match, match_module])
    check_matches = mocker.patch("raincoat.glue.check_matches",
                                 return_value=[("bla", match)])

    # Asserts are made in the check_matches method
    assert list(raincoat(".")) == [
        'umbrella == 3.2 @ path/to/file.py:MyClass (from filename:12)\n'
        'bla\n']

    assert (
        check_matches.mock_calls[0] ==
        mocker.call({'pypi': [match, match_module]}))
