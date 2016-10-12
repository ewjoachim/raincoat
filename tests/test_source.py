from raincoat import source


def test_source_tarball(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    # Does not provide a wheel
    source.download_package("fr2csv==1.0.1", install_dir.strpath)

    source_code = source.open_downloaded(install_dir.strpath, "fr2csv/__init__.py")

    lines = source_code.splitlines()
    assert len(lines) == 101
    assert lines[44] == "class AgnosticReader(object):"


def test_source_wheel(tmpdir):
    install_dir = tmpdir.mkdir("install_dir")

    # Does not provide a wheel
    source.download_package("six==1.10.0", install_dir.strpath)

    source_code = source.open_downloaded(install_dir.strpath, "six.py")

    lines = source_code.splitlines()
    assert len(lines) == 868
    assert lines[0] == '"""Utilities for writing code that runs on Python 2 and 3"""'
