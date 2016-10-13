import os
import shutil

import mock
import pytest

from raincoat import source


def test_source_tarball(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    pip = mocker.patch("pip.main")

    def simulate_download(*args):
        filename = "fr2csv-1.0.1.tar.gz"
        shutil.copyfile(
            os.path.join(os.path.dirname(__file__),
                         "samples", filename),
            os.path.join(install_dir.strpath, filename))
        return 0

    pip.side_effect = simulate_download

    # Does not provide a wheel
    source.download_package("fr2csv", "1.0.1", install_dir.strpath)

    assert pip.mock_calls == [mock.call([
        "download", "--no-deps", "-d", install_dir.strpath, "fr2csv==1.0.1"])]

    source_code = source.open_downloaded(
        install_dir.strpath, ["fr2csv/__init__.py"], "fr2csv")

    lines = source_code["fr2csv/__init__.py"].splitlines()
    assert len(lines) == 101
    assert lines[44] == "class AgnosticReader(object):"


def test_source_wheel(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    pip = mocker.patch("pip.main")

    def simulate_download(*args):
        filename = "six-1.10.0-py2.py3-none-any.whl"
        shutil.copyfile(
            os.path.join(os.path.dirname(__file__),
                         "samples", filename),
            os.path.join(install_dir.strpath, filename))
        return 0

    pip.side_effect = simulate_download

    # Provides a wheel
    source.download_package("six", "1.10.0", install_dir.strpath)

    source_code = source.open_downloaded(
        install_dir.strpath, ["six.py"], "six")

    lines = source_code["six.py"].splitlines()
    assert len(lines) == 868
    assert lines[0] == '"""Utilities for writing code that runs on Python 2 and 3"""'


def test_current_version():
    assert source.get_current_or_latest_version("pytest") == (True, "3.0.3")


def test_latest_version(mocker):
    get = mocker.patch("requests.get")
    get.return_value.json.return_value = {"info": {"version": "1.0.1"}}
    assert source.get_current_or_latest_version("fr2csv") == (False, "1.0.1")


def test_get_current_path():
    assert source.get_current_path("pytest").endswith("site-packages")


def test_open_installed():
    print(source.open_installed(
        source.get_current_path("pytest"),
        ["pytest.py"]))


def test_unrecognized_format(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    install_dir.join("bla.txt").write("yay")

    with pytest.raises(NotImplementedError):
        source.open_downloaded(install_dir.strpath, [], "bla")


def test_pip_error(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    pip = mocker.patch("pip.main")

    pip.return_value = 1

    with pytest.raises(ValueError):
        source.download_package("fr2csv", "1.0.1", install_dir.strpath)


def test_file_not_found(tmpdir, mocker):
    install_dir = tmpdir.mkdir("install_dir")

    pip = mocker.patch("pip.main")

    def simulate_download(*args):
        filename = "fr2csv-1.0.1.tar.gz"
        shutil.copyfile(
            os.path.join(os.path.dirname(__file__),
                         "samples", filename),
            os.path.join(install_dir.strpath, filename))
        return 0

    pip.side_effect = simulate_download

    # Does not provide a wheel
    source.download_package("fr2csv", "1.0.1", install_dir.strpath)

    assert pip.mock_calls == [mock.call([
        "download", "--no-deps", "-d", install_dir.strpath, "fr2csv==1.0.1"])]

    with pytest.raises(ValueError):
        source.open_downloaded(
            install_dir.strpath, ["fr2csv/bla.py"], "fr2csv")
