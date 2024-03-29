from __future__ import annotations

import os
import pathlib

import pytest

from raincoat import source


def test_open_in_tarball():
    file_path = os.path.join(
        os.path.dirname(__file__), "samples", "fr2csv-1.0.1.tar.gz"
    )

    source_code = source.open_in_tarball(file_path, ["fr2csv/__init__.py"])

    lines = source_code["fr2csv/__init__.py"].splitlines()
    assert len(lines) == 101
    assert lines[44] == "class AgnosticReader(object):"


def test_open_in_wheel():
    file_path = os.path.join(
        os.path.dirname(__file__), "samples", "six-1.10.0-py2.py3-none-any.whl"
    )

    source_code = source.open_in_wheel(file_path, ["six.py"])

    lines = source_code["six.py"].splitlines()
    assert len(lines) == 868
    assert lines[0] == (
        '"""Utilities for writing code ' 'that runs on Python 2 and 3"""'
    )


def test_download_package(mocker):
    pip = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))

    source.download_package("fr2csv", "1.0.1", "/tmp/clean/")

    assert pip.mock_calls == [
        mocker.call(
            ["pip", "download", "--no-deps", "-d", "/tmp/clean/", "fr2csv==1.0.1"]
        )
    ]


def test_open_downloaded_wheel(mocker):
    mocker.patch("os.listdir", return_value=["a.whl"])
    tb = mocker.patch("raincoat.source.open_in_tarball")
    whl = mocker.patch("raincoat.source.open_in_wheel")

    source.open_downloaded("b", ["yay.py"])

    assert tb.mock_calls == []
    assert whl.mock_calls == [mocker.call("b/a.whl", ["yay.py"])]


def test_open_downloaded_tarball(mocker):
    mocker.patch("os.listdir", return_value=["a.tar.gz"])
    tb = mocker.patch("raincoat.source.open_in_tarball")
    whl = mocker.patch("raincoat.source.open_in_wheel")

    source.open_downloaded("b", ["yay.py"])

    assert whl.mock_calls == []
    assert tb.mock_calls == [mocker.call("b/a.tar.gz", ["yay.py"])]


def test_current_version(mocker):
    # The path for this patch is very strange but in the raincoat.source module,
    # importlib_metadata may be either the package importlib_metadata or
    # importlib.metadata from the standard lib depending on the python version
    mocker.patch("raincoat.source.importlib_metadata.version", return_value="1.2.3")
    assert source.get_current_or_latest_version("pytest") == (True, "1.2.3")


def test_latest_version(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {"releases": {"1.0.0": None, "1.0.1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_latest_version_no_prerelease(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {"releases": {"1.0.1": None, "1.0.2a1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_latest_version_invalid(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {"releases": {"1.0.1": None, "1.0.2rc1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_get_distributed_files():
    pathname = "pytest/__init__.py"
    path = pathlib.Path(pathname)

    assert source.get_distributed_files("pytest")[pathname] == path


def test_open_installed():
    source_dict = source.open_installed(
        source.get_distributed_files("pytest"), ["pytest/__init__.py"]
    )
    assert len(source_dict) == 1
    assert "pytest/__init__.py" in source_dict
    assert ("pytest: unit and functional testing with Python.") in source_dict[
        "pytest/__init__.py"
    ]


def test_unrecognized_format(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    install_dir.join("bla.txt").write("yay")

    with pytest.raises(NotImplementedError):
        source.open_downloaded(install_dir.strpath, [])


def test_pip_error(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    mocker.patch(
        "subprocess.run", return_value=mocker.Mock(returncode=1, stdout=b"Foo")
    )

    with pytest.raises(ValueError) as exc_info:
        source.download_package("fr2csv", "1.0.1", install_dir.strpath)

    assert str(exc_info.value) == "Error while fetching fr2csv==1.0.1 via pip: Foo"


def test_file_not_found_tarball(tmpdir, mocker):
    file_path = os.path.join(
        os.path.dirname(__file__), "samples", "fr2csv-1.0.1.tar.gz"
    )

    result = source.open_in_tarball(file_path, ["fr2csv/bla.py"])

    assert result == {"fr2csv/bla.py": source.FILE_NOT_FOUND}


def test_file_not_found_wheel(tmpdir, mocker):
    file_path = os.path.join(
        os.path.dirname(__file__), "samples", "six-1.10.0-py2.py3-none-any.whl"
    )

    result = source.open_in_wheel(file_path, ["six/bla.py"])

    assert result == {"six/bla.py": source.FILE_NOT_FOUND}


def test_file_not_found_installed(tmpdir, mocker):
    result = source.open_installed(source.get_distributed_files("pytest"), ["bla.py"])

    assert result == {"bla.py": source.FILE_NOT_FOUND}


def test_get_branch_commit(mocker):
    get_session = mocker.patch("raincoat.github_utils.get_session")
    get = get_session.return_value.__enter__.return_value.get
    response = get.return_value
    response.json.return_value = {"commit": {"sha": "123321"}}

    assert source.get_branch_commit("a/b", "bla") == "123321"
    assert get.mock_calls[0] == mocker.call(
        "https://api.github.com/repos/a/b/branches/bla"
    )


def test_download_files_from_repo(mocker):
    get_session = mocker.patch("raincoat.github_utils.get_session")
    get = get_session.return_value.__enter__.return_value.get
    response = get.return_value
    response.status_code = 200
    response.text = "bla"

    result = source.download_files_from_repo("a/b", "123321", ["f.py"])

    assert result == {"f.py": "bla"}
    assert get.mock_calls[0] == mocker.call(
        "https://raw.githubusercontent.com/a/b/123321/f.py"
    )


def test_download_files_from_repo_not_found(mocker):
    get_session = mocker.patch("raincoat.github_utils.get_session")
    get = get_session.return_value.__enter__.return_value.get
    response = get.return_value
    response.status_code = 404

    result = source.download_files_from_repo("a/b", "123321", ["f.py"])

    assert result == {"f.py": source.FILE_NOT_FOUND}
