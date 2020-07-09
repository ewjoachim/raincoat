from itertools import count

import pytest

from raincoat import constants
from raincoat.match import python


def test_group_composite():
    result = python.group_composite(
        [("a", "b", "c"), ("a", "b", "d"), ("a", "c", "d"), ("b", "b", "c")]
    )

    assert result == {"a": {"b": ["c", "d"], "c": ["d"]}, "b": {"b": ["c"]}}


class Checker(python.PythonChecker):
    def match_source_key(self, match):
        return "a"

    def current_source_key(self, match):
        return "b"

    def get_source(self, key, files):
        return {file: [key + file] for file in files}


class CheckerNotFound(Checker):
    def get_source(self, key, files):
        return {file: constants.FILE_NOT_FOUND for file in files}


class Match(python.PythonMatch):
    def __init__(self, path, element):
        self.path = path
        self.element = element


@pytest.fixture
def python_match():
    return Match("path1.py", "element1")


@pytest.fixture
def python_match2():
    return Match("path2.py", "element2")


def sources(file_source, element_names):
    for name in element_names:
        yield name, ["{} in {}".format(name, "".join(file_source))]


def test_check(mocker, python_match, python_match2):
    mocker.patch("raincoat.match.python.parse.find_elements", side_effect=sources)

    result = list(Checker().check([python_match, python_match2]))

    assert result == [
        (
            "Code is different:\n"
            "--- path1.py\n"
            "+++ path1.py\n"
            "@@ -1 +1 @@\n"
            "-element1 in apath1.py\n"
            "+element1 in bpath1.py",
            python_match,
        ),
        (
            "Code is different:\n"
            "--- path2.py\n"
            "+++ path2.py\n"
            "@@ -1 +1 @@\n"
            "-element2 in apath2.py\n"
            "+element2 in bpath2.py",
            python_match2,
        ),
    ]


def test_get_source_keys(python_match, python_match2):
    assert list(Checker().get_source_keys([python_match, python_match2])) == [
        ("a", "path1.py", "element1"),
        ("b", "path1.py", "element1"),
        ("a", "path2.py", "element2"),
        ("b", "path2.py", "element2"),
    ]


def test_get_elements(mocker):
    mocker.patch(
        "raincoat.match.python.parse.find_elements",
        return_value=[("element1", "source_element_1")],
    )

    result = Checker().get_elements(source_keys=[("a", "path1.py", "element1")])

    assert dict(result) == {("a", "path1.py", "element1"): "source_element_1"}


def test_get_elements_file_not_found(mocker):
    mocker.patch(
        "raincoat.match.python.parse.find_elements",
        return_value=[("element1", "source_element_1")],
    )

    result = CheckerNotFound().get_elements(source_keys=[("a", "path1.py", "element1")])

    assert dict(result) == {("a", "path1.py", "element1"): constants.FILE_NOT_FOUND}


def test_run_matches(python_match):
    all_kwargs = []

    counter = count()

    class NoRun(Checker):
        def run_match(self, **kwargs):
            all_kwargs.append(kwargs)
            return next(counter)

    elements = {("a", "path1.py", "element1"): "i", ("b", "path1.py", "element1"): "j"}

    assert list(NoRun().run_matches([python_match], elements)) == [0]

    assert len(all_kwargs) == 1
    assert all_kwargs[0] == {
        "match": python_match,
        "match_element": "i",
        "current_element": "j",
    }


def test_run_matches_identical(python_match):
    class NoRun(Checker):
        def run_match(self, **kwargs):
            raise AssertionError("should not be there")

    elements = {("a", "path1.py", "element1"): "i", ("b", "path1.py", "element1"): "i"}

    assert list(NoRun().run_matches([python_match], elements)) == []


def test_run_matches_identical_file_not_found(python_match):
    all_kwargs = []

    counter = count()

    class NoRun(Checker):
        def run_match(self, **kwargs):
            all_kwargs.append(kwargs)
            return next(counter)

    elements = {
        ("a", "path1.py", "element1"): constants.FILE_NOT_FOUND,
        ("b", "path1.py", "element1"): constants.FILE_NOT_FOUND,
    }

    assert list(NoRun().run_matches([python_match], elements)) == [0]


def test_run_matches_identical_element_not_found(python_match):
    all_kwargs = []

    counter = count()

    class NoRun(Checker):
        def run_match(self, **kwargs):
            all_kwargs.append(kwargs)
            return next(counter)

    elements = {
        ("a", "path1.py", "element1"): constants.FILE_NOT_FOUND,
        ("b", "path1.py", "element1"): constants.FILE_NOT_FOUND,
    }

    assert list(NoRun().run_matches([python_match], elements)) == [0]


def test_run_match(python_match):

    result = Checker().run_match(
        match=python_match, match_element=["element a"], current_element=["element b"]
    )

    assert result == (
        "Code is different:\n"
        "--- path1.py\n"
        "+++ path1.py\n"
        "@@ -1 +1 @@\n"
        "-element a\n"
        "+element b",
        python_match,
    )


def test_run_match_file_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=constants.FILE_NOT_FOUND,
        current_element=["element b"],
    )

    assert result == (
        "Invalid Raincoat PyPI comment : path1.py does not exist",
        python_match,
    )


def test_run_match_element_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=constants.ELEMENT_NOT_FOUND,
        current_element=["element b"],
    )

    assert result == (
        "Invalid Raincoat PyPI comment : element1 does not exist in path1.py",
        python_match,
    )


def test_run_match_current_file_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=["element a"],
        current_element=constants.FILE_NOT_FOUND,
    )

    assert result == ("File path1.py disappeared", python_match)


def test_run_match_current_element_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=["element a"],
        current_element=constants.ELEMENT_NOT_FOUND,
    )

    assert result == ("Element element1 disappeared from path1.py", python_match)


def test_run_match_both_files_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=constants.FILE_NOT_FOUND,
        current_element=constants.FILE_NOT_FOUND,
    )

    assert result == (
        "Invalid Raincoat PyPI comment : path1.py does not exist",
        python_match,
    )


def test_run_match_both_elements_not_found(python_match):

    result = Checker().run_match(
        match=python_match,
        match_element=constants.ELEMENT_NOT_FOUND,
        current_element=constants.ELEMENT_NOT_FOUND,
    )

    assert result == (
        "Invalid Raincoat PyPI comment : element1 does not exist in path1.py",
        python_match,
    )


def test_current_source_key():
    with pytest.raises(NotImplementedError):
        python.PythonChecker().current_source_key(0)


def test_match_source_key():
    with pytest.raises(NotImplementedError):
        python.PythonChecker().match_source_key(0)


def test_get_source():
    with pytest.raises(NotImplementedError):
        python.PythonChecker().get_source(0, 1)


def test_format_diff_plus(color, python_match):
    val = python_match.format_line("+aaa", color, 3)
    assert val == "diff+" "+aaa" "neutral"


def test_format_diff_minus(color, python_match):
    val = python_match.format_line("-aaa", color, 3)
    assert val == "diff-" "-aaa" "neutral"


def test_format_diff_at(color, python_match):
    val = python_match.format_line("@aaa", color, 3)
    assert val == "diff@" "@aaa" "neutral"


def test_format_not_diff(color, python_match):
    val = python_match.format_line("aaa", color, 3)
    assert val == "aaa"
