import pytest

from raincoat import match as match_module


@pytest.fixture
def basic_match():
    return match_module.Match(filename="yay.py", lineno=12)


def test_str_match(basic_match):
    assert str(basic_match) == "Match in yay.py:12"


def test_match_from_comment(match):
    with pytest.raises(match_module.NotMatching):
        assert match_module.match_from_comment(
            "# Raincoat: bla", filename="yay.py", lineno=12) == match


def test_check_matches(mocker, match):
    mocker.patch("raincoat.match.pypi.PyPIChecker.check",
                 return_value=[1])

    list(match_module.check_matches({"pypi": [match]}))


def test_check_matches_no_checker(mocker):
    class Unfinished(match_module.Match):
        match_type = "unfinished"

    match = Unfinished("yay.py", 12)

    match_module.match_types["unfinished"] = Unfinished
    try:
        with pytest.raises(NotImplementedError):
            list(match_module.check_matches({"unfinished": [match]}))

    finally:
        match_module.match_types.pop("unfinished")


def test_fill_match_types_no_match_type(mocker):
    class Unfinished(match_module.Match):
        pass

    with pytest.raises(NotImplementedError,
                       message="Unfinished has no match_type"):
        match_module.fill_match_types(match_module.match_types, [Unfinished])


def test_format_line_first(match, color):
    assert match.format_line("haha", color, 0) == "message" "haha" "neutral"


def test_format_line_not_first(match, color):
    assert match.format_line("haha", color, 1) == "haha"


def test_format(match, color):
    assert match.format("haha", color) == (
        "match" "umbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)" "neutral\n"
        "message" "haha" "neutral\n")


def test_format_empty(match, color):
    assert match.format("", color) == (
        "matchumbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)" "neutral\n")


def test_format_space(match, color):
    assert match.format("haha\n   \nhehe", color) == (
        "match" "umbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)" "neutral\n"
        "message" "haha" "neutral\n"
        "hehe\n")
