import pytest

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


def test_compare_files_identical():
    raincoat = Raincoat()

    func_a = """
def a():
    return 1
    """
    kwargs = default_kwargs.copy()
    kwargs.update(
        {"code_object": "a"})
    raincoat.compare_files(
        func_a, func_a, [Match(**kwargs)])

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
    kwargs = default_kwargs.copy()
    kwargs.update(
        {"code_object": "a"})
    raincoat.compare_files(
        func_a, func_b, [Match(**kwargs)])

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
    kwargs = default_kwargs.copy()
    kwargs.update(
        {"code_object": "a"})
    raincoat.compare_files(
        func_a, func_b, [Match(**kwargs)])

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
    kwargs = default_kwargs.copy()
    kwargs.update(
        {"code_object": "a"})

    with pytest.raises(ValueError):
        raincoat.compare_files(
            func_a, func_b, [Match(**kwargs)])


def test_compare_files_missing_current():
    raincoat = Raincoat()

    func_a = """
def a():
    return 2
    """
    func_b = """
    """
    kwargs = default_kwargs.copy()
    kwargs.update(
        {"code_object": "a"})

    raincoat.compare_files(
        func_a, func_b, [Match(**kwargs)])

    assert len(raincoat.errors) == 1
    assert raincoat.errors[0][0].startswith("Code object a has disappeared")


def test_compare_contents_identical(mocker):
    compare_files = mocker.patch.object(Raincoat, "compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code"}

    kwargs = default_kwargs.copy()
    kwargs.update(
        {"path": "file_a.py"})

    raincoat.compare_contents(
        contents_a, contents_a, [Match(**kwargs)])

    assert len(raincoat.errors) == 0


def test_compare_contents_missing_current(mocker):
    compare_files = mocker.patch.object(Raincoat, "compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code", "file_b.py": "code"}
    contents_b = {"file_a.py": "code"}

    kwargs = default_kwargs.copy()
    kwargs.update(
        {"path": "file_b.py"})

    raincoat.compare_contents(
        contents_a, contents_b, [Match(**kwargs)])

    assert len(raincoat.errors) == 1
    assert raincoat.errors[0][0].startswith("File file_b.py has disappeared")
    assert compare_files.mock_calls == []


def test_compare_contents_missing_match(mocker):
    mocker.patch.object(Raincoat, "compare_files")
    raincoat = Raincoat()

    contents_a = {"file_a.py": "code"}
    contents_b = {"file_a.py": "code", "file_b.py": "code"}

    kwargs = default_kwargs.copy()
    kwargs.update(
        {"path": "file_b.py"})

    with pytest.raises(ValueError):
        raincoat.compare_contents(
            contents_a, contents_b, [Match(**kwargs)])

def test_check_package(mocker):
    assert False
