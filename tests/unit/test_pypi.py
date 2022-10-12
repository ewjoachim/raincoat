from __future__ import annotations

import pytest

from raincoat.match import pypi


def test_match_str(match):
    assert str(match) == "umbrella == 3.2 @ path/to/file.py:MyClass (from filename:12)"


def test_match_str_other_version(match):
    match.other_version = "3.4"
    assert (
        str(match)
        == "umbrella == 3.2 vs 3.4 @ path/to/file.py:MyClass (from filename:12)"
    )


def test_wrong_package_format():
    with pytest.raises(pypi.NotMatching):
        pypi.PyPIMatch("a", 12, "pytest", "path", "element")


def test_current_source_key(mocker, match):
    mocker.patch(
        "raincoat.source.get_current_or_latest_version", return_value=(True, "3.8")
    )

    assert pypi.PyPIChecker().current_source_key(match) == ("umbrella", "3.8", True)

    assert match.other_version == "3.8"


def test_current_source_key_cache(mocker, match):
    get_version = mocker.patch(
        "raincoat.match.pypi.source.get_current_or_latest_version",
        return_value=(True, "3.7"),
    )

    checker = pypi.PyPIChecker()
    a = checker.current_source_key(match)
    assert len(get_version.mock_calls) == 1

    get_version.reset_mock()

    b = checker.current_source_key(match)

    assert get_version.mock_calls == []
    assert a == b


def test_match_source_key(match):

    assert pypi.PyPIChecker().match_source_key(match) == ("umbrella", "3.2", False)


def test_get_source_installed(mocker):
    path = mocker.Mock()
    path.read_text.return_value = ["yay"]

    gdf = mocker.patch(
        "raincoat.source.get_distributed_files", return_value={"file_1.py": path}
    )

    result = pypi.PyPIChecker().get_source(
        key=pypi.PyPIKey("umbrella", "3.4", True), files=["file_1.py"]
    )

    assert result == {"file_1.py": ["yay"]}
    gdf.assert_called_with("umbrella")


def test_get_source_downloaded(mocker):
    source = mocker.patch("raincoat.match.pypi.source")
    source.open_downloaded.return_value = {"file_1.py": ["yay"]}
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir", return_value="/tmp/clean")

    result = pypi.PyPIChecker().get_source(
        key=pypi.PyPIKey("umbrella", "3.4", False), files=["file_1.py"]
    )

    assert result == {"file_1.py": ["yay"]}
    assert source.download_package.mock_calls == [
        mocker.call("umbrella", "3.4", "/tmp/clean")
    ]
    assert source.open_downloaded.mock_calls == [
        mocker.call("/tmp/clean", ["file_1.py"])
    ]
