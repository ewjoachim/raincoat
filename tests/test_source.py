from raincoat import source


def test_source_tarball(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    # Does not provide a wheel
    source.download_package("fr2csv", "1.0.1", install_dir.strpath)

    source_code = source.open_downloaded(
        install_dir.strpath, ["fr2csv/__init__.py"], "fr2csv")

    lines = source_code["fr2csv/__init__.py"].splitlines()
    assert len(lines) == 101
    assert lines[44] == "class AgnosticReader(object):"


def test_source_wheel(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    # Does not provide a wheel
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
