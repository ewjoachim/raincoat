import pytest

import mock

from raincoat.match import Match
from raincoat.match.pypi import PyPIChecker


default_kwargs = {
    "match_type": "pypi",
    "package": "umbrella==1.0.0",
    "filename": "file.py",
    "lineno": 23,
    "path": "a/b.py",
    "element": None,
}


def get_match(**kwargs):
    match_kwargs = default_kwargs.copy()
    match_kwargs.update(kwargs)
    return Match.from_comment(**match_kwargs)


def test_compare_files_identical():
    checker = PyPIChecker()

    func_a = """
def a():
    return 1
    """
    checker.compare_files(
        func_a, func_a, [get_match(element="a")])

    assert checker.errors == []


def test_compare_files_different_but_elsewhere():
    checker = PyPIChecker()

    func_a = """# A
def a():
    return 1
    """
    func_b = """# B
def a():
    return 1
    """

    checker.compare_files(
        func_a, func_b, [get_match(element="a")])

    assert checker.errors == []


def test_compare_files_different():
    checker = PyPIChecker()

    func_a = """
def a():
    return 1
    """
    func_b = """
def a():
    return 2
    """
    checker.compare_files(
        func_a, func_b, [get_match(element="a")])

    assert len(checker.errors) == 1
    assert checker.errors[0][0].startswith("Code is different")


def test_compare_files_missing_match():
    checker = PyPIChecker()

    func_a = """
    """
    func_b = """
def a():
    return 2
    """

    with pytest.raises(ValueError):
        checker.compare_files(
            func_a, func_b, [get_match(element="a")])


def test_compare_files_missing_current():
    checker = PyPIChecker()

    func_a = """
def a():
    return 2
    """
    func_b = """
    """

    checker.compare_files(
        func_a, func_b, [get_match(element="a")])

    assert len(checker.errors) == 1
    assert checker.errors[0][0].startswith("Code object a has disappeared")


def test_compare_contents_identical(mocker):
    compare_files = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_files")
    checker = PyPIChecker()

    contents_a = {"file_a.py": "code"}

    checker.compare_contents(
        contents_a, contents_a, [get_match(path="file_a.py")])

    assert len(checker.errors) == 0
    assert compare_files.mock_calls == []


def test_compare_contents_different_code(mocker):
    compare_files = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_files")
    checker = PyPIChecker()

    contents_a = {"file_a.py": "code_a"}
    contents_b = {"file_a.py": "code_b"}

    match = get_match(path="file_a.py")
    checker.compare_contents(
        contents_a, contents_b, [match])

    assert len(checker.errors) == 0
    assert compare_files.mock_calls == [mock.call("code_a", "code_b", [match])]


def test_compare_contents_missing_current(mocker):
    compare_files = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_files")
    checker = PyPIChecker()

    contents_a = {"file_a.py": "code", "file_b.py": "code"}
    contents_b = {"file_a.py": "code"}

    checker.compare_contents(
        contents_a, contents_b, [get_match(path="file_b.py")])

    assert len(checker.errors) == 1
    assert checker.errors[0][0].startswith("File file_b.py has disappeared")
    assert compare_files.mock_calls == []


def test_compare_contents_missing_match(mocker):
    mocker.patch("raincoat.match.pypi.PyPIChecker.compare_files")
    checker = PyPIChecker()

    contents_a = {"file_a.py": "code"}
    contents_b = {"file_a.py": "code", "file_b.py": "code"}

    with pytest.raises(ValueError):
        checker.compare_contents(
            contents_a, contents_b, [get_match(path="file_b.py")])


def test_check_package_identical_version(mocker):
    compare_content = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_contents")

    version = mocker.patch("raincoat.source.get_current_or_latest_version")
    version.return_value = (True, "1.2.3")

    checker = PyPIChecker()

    checker.check_package("umbrella", "1.2.3", [get_match()])

    assert len(checker.errors) == 0
    assert compare_content.mock_calls == []


def test_check_package_installed(mocker):
    compare_content = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_contents")

    source = mocker.patch("raincoat.match.pypi.source")

    source.get_current_or_latest_version.return_value = (True, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code"}

    checker = PyPIChecker()

    with checker.cleaner_ctx():
        checker.check_package("umbrella", "1.2.2", [get_match()])

    assert len(source.download_package.mock_calls) == 1
    assert len(source.open_downloaded.mock_calls) == 1
    assert len(source.open_installed.mock_calls) == 1
    assert len(checker.errors) == 0
    assert compare_content.mock_calls == []


def test_check_package_installed_no_fast_escape(mocker):
    compare_content = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_contents")

    source = mocker.patch("raincoat.match.pypi.source")

    source.get_current_or_latest_version.return_value = (True, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code2"}

    match = get_match()

    checker = PyPIChecker()
    with checker.cleaner_ctx():
        checker.check_package("umbrella", "1.2.2", [match])

    assert len(source.download_package.mock_calls) == 1
    assert len(source.open_downloaded.mock_calls) == 1
    assert len(source.open_installed.mock_calls) == 1
    assert len(checker.errors) == 0
    assert compare_content.mock_calls == [mock.call(
        {"file_a.py": "code"}, {"file_a.py": "code2"}, [match])]


def test_checker_check(mocker):
    check_package = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.check_package")

    matches = [
        get_match(package="a==1.0.0", path="a"),
        get_match(package="b==1.0.0"),
        get_match(package="a==1.0.0", path="b"),
    ]
    match1, match2, match3 = matches

    checker = PyPIChecker()
    checker.check(matches)

    assert len(check_package.mock_calls) == 2
    assert check_package.mock_calls == [
        mock.call("a", "1.0.0", [match1, match3]),
        mock.call("b", "1.0.0", [match2]),
    ]


def test_check_package_not_installed(mocker):
    compare_content = mocker.patch(
        "raincoat.match.pypi.PyPIChecker.compare_contents")

    source = mocker.patch("raincoat.match.pypi.source")

    source.get_current_or_latest_version.return_value = (False, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code"}

    checker = PyPIChecker()

    with checker.cleaner_ctx():
        checker.check_package("umbrella", "1.2.2", [get_match()])

    assert len(source.download_package.mock_calls) == 2
    assert len(source.open_downloaded.mock_calls) == 2
    assert len(source.open_installed.mock_calls) == 0
    assert len(checker.errors) == 0
    assert compare_content.mock_calls == []


def test_misconfigured_match():
    class SubClass(Match):
        pass

    with pytest.raises(NotImplementedError):
        SubClass.check_matches([])


def test_match_check_matches():

    class SubClass(Match):
        checker = mock.Mock()

    SubClass.check_matches([])

    assert SubClass.checker.mock_calls == [
        mock.call(), mock.call().check([])]
