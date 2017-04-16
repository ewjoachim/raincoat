import os

import mock
import pytest

from raincoat import source


def test_open_in_tarball():

    file_path = os.path.join(os.path.dirname(__file__),
                             "samples", "fr2csv-1.0.1.tar.gz")

    source_code = source.open_in_tarball(
        file_path, ["fr2csv/__init__.py"])

    lines = source_code["fr2csv/__init__.py"].splitlines()
    assert len(lines) == 101
    assert lines[44] == "class AgnosticReader(object):"


def test_open_in_wheel():
    file_path = os.path.join(os.path.dirname(__file__),
                             "samples", "six-1.10.0-py2.py3-none-any.whl")

    source_code = source.open_in_wheel(
        file_path, ["six.py"])

    lines = source_code["six.py"].splitlines()
    assert len(lines) == 868
    assert lines[0] == ('"""Utilities for writing code '
                        'that runs on Python 2 and 3"""')


def test_download_package(mocker):
    pip = mocker.patch("pip.main", return_value=0)

    source.download_package("fr2csv", "1.0.1", "/tmp/clean/")

    assert pip.mock_calls == [mock.call([
        "download", "--no-deps", "-d", "/tmp/clean/", "fr2csv==1.0.1"])]


def test_open_downloaded_wheel(mocker):
    mocker.patch("os.listdir", return_value=["a.whl"])
    tb = mocker.patch("raincoat.source.open_in_tarball")
    whl = mocker.patch("raincoat.source.open_in_wheel")

    source.open_downloaded("b", ["yay.py"])

    assert tb.mock_calls == []
    assert whl.mock_calls == [mock.call("b/a.whl", ["yay.py"])]


def test_open_downloaded_tarball(mocker):
    mocker.patch("os.listdir", return_value=["a.tar.gz"])
    tb = mocker.patch("raincoat.source.open_in_tarball")
    whl = mocker.patch("raincoat.source.open_in_wheel")

    source.open_downloaded("b", ["yay.py"])

    assert whl.mock_calls == []
    assert tb.mock_calls == [mock.call("b/a.tar.gz", ["yay.py"])]


def test_current_version(mocker):
    dist = mocker.patch("raincoat.source.pkg_resources.get_distribution")()
    dist.version = "1.2.3"
    assert source.get_current_or_latest_version("pytest") == (True, "1.2.3")


def test_latest_version(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {
        "releases": {"1.0.0": None, "1.0.1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_latest_version_no_prerelease(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {
        "releases": {"1.0.1": None, "1.0.2a1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_latest_version_invalid(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {
        "releases": {"1.0.1": None, "1.0.2rc1": None}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_get_current_path():
    assert source.get_current_path("pytest").endswith("site-packages")


def test_open_installed():
    source_dict = source.open_installed(
        source.get_current_path("pytest"), ["pytest.py"])
    assert len(source_dict) == 1
    assert "pytest.py" in source_dict
    assert ("pytest: unit and functional "
            "testing with Python.\n") in source_dict["pytest.py"]


def test_unrecognized_format(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    install_dir.join("bla.txt").write("yay")

    with pytest.raises(NotImplementedError):
        source.open_downloaded(install_dir.strpath, [])


def test_pip_error(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    mocker.patch("pip.main", return_value=1)

    with pytest.raises(ValueError):
        source.download_package("fr2csv", "1.0.1", install_dir.strpath)


def test_file_not_found_tarball(tmpdir, mocker):
    file_path = os.path.join(os.path.dirname(__file__),
                             "samples", "fr2csv-1.0.1.tar.gz")

    result = source.open_in_tarball(
        file_path, ["fr2csv/bla.py"])

    assert result == {"fr2csv/bla.py": source.FILE_NOT_FOUND}


def test_file_not_found_wheel(tmpdir, mocker):
    file_path = os.path.join(os.path.dirname(__file__),
                             "samples", "six-1.10.0-py2.py3-none-any.whl")

    result = source.open_in_wheel(
        file_path, ["six/bla.py"])

    assert result == {"six/bla.py": source.FILE_NOT_FOUND}


def test_file_not_found_installed(tmpdir, mocker):

    result = source.open_installed(
        source.get_current_path("pytest"), ["bla.py"])

    assert result == {"bla.py": source.FILE_NOT_FOUND}
