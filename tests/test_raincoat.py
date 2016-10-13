import pytest

import mock

from raincoat.raincoat import Raincoat
from raincoat.grep import Match


default_kwargs = {
    "package": "umbrella",
    "version": "1.0.0",
    "filename": "file.py",
    "lineno": 23,
    "path": "a/b.py",
    "code_object": None,
}


def get_match(**kwargs):
    match_kwargs = default_kwargs.copy()
    match_kwargs.update(kwargs)
    return Match(**match_kwargs)


def test_compare_files_identical():
    raincoat = Raincoat()

    func_a = """
def a():
    return 1
    """
    raincoat.compare_files(
        func_a, func_a, [get_match(code_object="a")])

    assert raincoat.errors == []


def test_compare_files_different_but_elsewhere():
    raincoat = Raincoat()

    func_a = """# A
def a():
    return 1
    """
    func_b = """# B
def a():
    return 1
    """

    raincoat.compare_files(
        func_a, func_b, [get_match(code_object="a")])

    assert raincoat.errors == []


def test_compare_files_different():
    raincoat = Raincoat()

    func_a = """
def a():
    return 1
    """
    func_b = """
def a():
    return 2
    """
    raincoat.compare_files(
        func_a, func_b, [get_match(code_object="a")])

    assert len(raincoat.errors) == 1
    assert raincoat.errors[0][0].startswith("Code is different")


def test_compare_files_missing_match():
    raincoat = Raincoat()

    func_a = """
    """
    func_b = """
def a():
    return 2
    """

    with pytest.raises(ValueError):
        raincoat.compare_files(
            func_a, func_b, [get_match(code_object="a")])


def test_compare_files_missing_current():
    raincoat = Raincoat()

    func_a = """
def a():
    return 2
    """
    func_b = """
    """

    raincoat.compare_files(
        func_a, func_b, [get_match(code_object="a")])

    assert len(raincoat.errors) == 1
    assert raincoat.errors[0][0].startswith("Code object a has disappeared")


def test_compare_contents_identical(mocker):
    compare_files = mocker.patch("raincoat.raincoat.Raincoat.compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code"}

    raincoat.compare_contents(
        contents_a, contents_a, [get_match(path="file_a.py")])

    assert len(raincoat.errors) == 0
    assert compare_files.mock_calls == []


def test_compare_contents_different_code(mocker):
    compare_files = mocker.patch("raincoat.raincoat.Raincoat.compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code_a"}
    contents_b = {"file_a.py": "code_b"}

    match = get_match(path="file_a.py")
    raincoat.compare_contents(
        contents_a, contents_b, [match])

    assert len(raincoat.errors) == 0
    assert compare_files.mock_calls == [mock.call("code_a", "code_b", [match])]


def test_compare_contents_missing_current(mocker):
    compare_files = mocker.patch("raincoat.raincoat.Raincoat.compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code", "file_b.py": "code"}
    contents_b = {"file_a.py": "code"}

    raincoat.compare_contents(
        contents_a, contents_b, [get_match(path="file_b.py")])

    assert len(raincoat.errors) == 1
    assert raincoat.errors[0][0].startswith("File file_b.py has disappeared")
    assert compare_files.mock_calls == []


def test_compare_contents_missing_match(mocker):
    mocker.patch("raincoat.raincoat.Raincoat.compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code"}
    contents_b = {"file_a.py": "code", "file_b.py": "code"}

    with pytest.raises(ValueError):
        raincoat.compare_contents(
            contents_a, contents_b, [get_match(path="file_b.py")])


def test_check_package_identical_version(mocker):
    compare_content = mocker.patch("raincoat.raincoat.Raincoat.compare_contents")

    version = mocker.patch("raincoat.source.get_current_or_latest_version")
    version.return_value = (True, "1.2.3")

    raincoat = Raincoat()

    raincoat.check_package("umbrella", "1.2.3", [get_match()])

    assert len(raincoat.errors) == 0
    assert compare_content.mock_calls == []


def test_check_package_installed(mocker):
    compare_content = mocker.patch("raincoat.raincoat.Raincoat.compare_contents")

    source = mocker.patch("raincoat.raincoat.source")

    source.get_current_or_latest_version.return_value = (True, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code"}

    raincoat = Raincoat()

    raincoat.check_package("umbrella", "1.2.2", [get_match()])

    assert len(source.download_package.mock_calls) == 1
    assert len(source.open_downloaded.mock_calls) == 1
    assert len(source.open_installed.mock_calls) == 1
    assert len(raincoat.errors) == 0
    assert compare_content.mock_calls == []


def test_check_package_installed_no_fast_escape(mocker):
    compare_content = mocker.patch("raincoat.raincoat.Raincoat.compare_contents")

    source = mocker.patch("raincoat.raincoat.source")

    source.get_current_or_latest_version.return_value = (True, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code2"}

    raincoat = Raincoat()
    match = get_match()
    raincoat.check_package("umbrella", "1.2.2", [match])

    assert len(source.download_package.mock_calls) == 1
    assert len(source.open_downloaded.mock_calls) == 1
    assert len(source.open_installed.mock_calls) == 1
    assert len(raincoat.errors) == 0
    assert compare_content.mock_calls == [mock.call(
        {"file_a.py": "code"}, {"file_a.py": "code2"}, [match])]


def test_check_package_not_installed(mocker):
    compare_content = mocker.patch("raincoat.raincoat.Raincoat.compare_contents")

    source = mocker.patch("raincoat.raincoat.source")

    source.get_current_or_latest_version.return_value = (False, "1.2.3")
    source.open_downloaded.return_value = {"file_a.py": "code"}
    source.open_installed.return_value = {"file_a.py": "code"}

    raincoat = Raincoat()

    raincoat.check_package("umbrella", "1.2.2", [get_match()])

    assert len(source.download_package.mock_calls) == 2
    assert len(source.open_downloaded.mock_calls) == 2
    assert len(source.open_installed.mock_calls) == 0
    assert len(raincoat.errors) == 0
    assert compare_content.mock_calls == []


def test_raincoat(mocker):
    check_package = mocker.patch("raincoat.raincoat.Raincoat.check_package")
    shutil = mocker.patch("raincoat.raincoat.shutil")

    matches_mock = mocker.patch("raincoat.grep.find_in_dir")
    matches = [
        get_match(package="a", path="a"),
        get_match(package="b"),
        get_match(package="a", path="b"),
    ]

    matches_mock.return_value = matches

    raincoat = Raincoat()

    def add_clean(*args):
        raincoat._add_to_clean("bla")

    check_package.side_effect = add_clean

    raincoat.raincoat(".")

    assert check_package.mock_calls == [
        mock.call("a", "1.0.0", [matches[0], matches[2]]),
        mock.call("b", "1.0.0", [matches[1]]),
    ]

    assert shutil.rmtree.mock_calls == [mock.call("bla")]
