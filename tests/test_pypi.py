import pytest

from raincoat.match import pypi


@pytest.fixture
def match_info(match):
    return pypi.PyPIChecker().get_match_info([match])


def test_match_str(match):
    assert(
        str(match) ==
        "umbrella == 3.2 @ path/to/file.py:MyClass (from filename:12)")


def test_match_str_other_version(match):
    match.other_version = "3.4"
    assert(
        str(match) ==
        "umbrella == 3.2 vs 3.4 @ path/to/file.py:MyClass (from filename:12)")


def test_format_diff_plus(color, match):
    assert match.format_line("+aaa", color, 3) == "diff+" "+aaa" "neutral"


def test_format_diff_minus(color, match):
    assert match.format_line("-aaa", color, 3) == "diff-" "-aaa" "neutral"


def test_format_diff_at(color, match):
    assert match.format_line("@aaa", color, 3) == "diff@" "@aaa" "neutral"


def test_format_not_diff(color, match):
    assert match.format_line("aaa", color, 3) == "aaa"


def test_wrong_package_format():
    with pytest.raises(pypi.NotMatching):
        pypi.PyPIMatch("a", 12, "pytest", "path", "element")


def test_current_source_key(mocker, match):
    mocker.patch(
        "raincoat.match.pypi.source.get_current_or_latest_version",
        return_value=(True, "3.4"))

    assert pypi.PyPIChecker().current_source_key(match) == (
        "umbrella", "3.4", True)

    assert match.other_version == "3.4"


def test_match_source_key(match):

    assert pypi.PyPIChecker().match_source_key(match) == (
        "umbrella", "3.2", False)


def test_get_source_installed(mocker):
    source = mocker.patch("raincoat.match.pypi.source")
    source.get_current_path.return_value = "yay/"
    source.open_installed.return_value = {"file_1.py": ["yay"]}

    result = pypi.PyPIChecker().get_source(
        key=pypi.PyPIKey("umbrella", "3.4", True), files=["file_1.py"])

    assert result == {"file_1.py": ["yay"]}
    assert source.get_current_path.mock_calls == [mocker.call("umbrella")]
    assert source.open_installed.mock_calls == [
        mocker.call('yay/', ['file_1.py'])]


def test_get_source_downloaded(mocker):
    source = mocker.patch("raincoat.match.pypi.source")
    source.open_downloaded.return_value = {"file_1.py": ["yay"]}
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")

    result = pypi.PyPIChecker().get_source(
        key=pypi.PyPIKey("umbrella", "3.4", False), files=["file_1.py"])

    assert result == {"file_1.py": ["yay"]}
    assert source.download_package.mock_calls == [
        mocker.call('umbrella', '3.4', '/tmp/clean')]
    assert source.open_downloaded.mock_calls == [
        mocker.call('/tmp/clean', ['file_1.py'])]
