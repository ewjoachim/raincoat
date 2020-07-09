import pytest
import importlib_metadata

from raincoat import match as match_module


@pytest.fixture
def basic_match():
    return match_module.Match(filename="yay.py", lineno=12)


def test_str_match(basic_match):
    assert str(basic_match) == "Match in yay.py:12"


def test_match_from_comment(match):
    with pytest.raises(match_module.NotMatching):
        assert (
            match_module.match_from_comment(
                "# Raincoat: bla", filename="yay.py", lineno=12
            )
            == match
        )


def test_check_matches(mocker, match):
    mocker.patch("raincoat.match.pypi.PyPIChecker.check", return_value=[1])
    mocker.patch("raincoat.match.match_types", {"pypi": match.__class__})

    assert list(match_module.check_matches({"pypi": [match]})) == [1]


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


def test_compute_match_types(mocker):
    gme = mocker.patch("raincoat.match.get_match_entrypoints")

    class MatchFactory(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return self.name

    MatchA, MatchB = MatchFactory("A"), MatchFactory("B")

    entry_a, entry_b = gme.return_value = [
        importlib_metadata.EntryPoint(name="a", value="aaa", group=""),
        importlib_metadata.EntryPoint(name="b", value="bbb", group=""),
    ]
    entry_a.load = lambda: MatchA
    entry_b.load = lambda: MatchB

    assert match_module.compute_match_types() == {"a": MatchA, "b": MatchB}
    assert MatchA.match_type == "a"
    assert MatchB.match_type == "b"


def test_compute_match_types_duplicate(mocker, caplog):
    iep = mocker.patch("raincoat.match.get_match_entrypoints")

    class MatchFactory(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return self.name

    MatchA, MatchB = MatchFactory("A"), MatchFactory("B")

    entry_a, entry_b = iep.return_value = [
        importlib_metadata.EntryPoint(name="a", value="aaa", group=""),
        importlib_metadata.EntryPoint(name="a", value="bbb", group=""),
    ]
    entry_a.load = lambda: MatchA
    entry_b.load = lambda: MatchB

    assert match_module.compute_match_types() == {"a": MatchA}

    assert (
        "Several classes registered for the match type a" in caplog.records[0].message
    )
    assert "B will be ignored" in caplog.records[0].message
    assert "A will be used" in caplog.records[0].message


def test_format_line_first(match, color):
    assert match.format_line("haha", color, 0) == "message" "haha" "neutral"


def test_format_line_not_first(match, color):
    assert match.format_line("haha", color, 1) == "haha"


def test_format(match, color):
    assert match.format("haha", color) == (
        "match"
        "umbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)"
        "neutral\n"
        "message"
        "haha"
        "neutral\n"
    )


def test_format_empty(match, color):
    assert match.format("", color) == (
        "matchumbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)"
        "neutral\n"
    )


def test_format_space(match, color):
    assert match.format("haha\n   \nhehe", color) == (
        "match"
        "umbrella == 3.2 @ path/to/file.py:MyClass "
        "(from filename:12)"
        "neutral\n"
        "message"
        "haha"
        "neutral\n"
        "hehe\n"
    )
