from __future__ import annotations

import pytest

from raincoat.match import pygithub


@pytest.fixture
def pygithub_match():
    return pygithub.PyGithubMatch(
        repo="python/cpython@abc123",
        path="Lib/this.py",
        element="s",
        branch="3.6",
        filename="filename",
        lineno=12,
    )


def test_match_str(pygithub_match):
    assert (
        str(pygithub_match) == "python/cpython@abc123 vs 3.6 branch at Lib/this.py:s "
        "(from filename:12)"
    )


def test_match_str_other_version(pygithub_match):
    pygithub_match.branch_commit = "fed987"
    assert (
        str(pygithub_match)
        == "python/cpython@abc123 vs 3.6 branch (fed987) at Lib/this.py:s "
        "(from filename:12)"
    )


def test_wrong_package_format():
    with pytest.raises(pygithub.NotMatching):
        pygithub.PyGithubMatch(filename="a", lineno=12, repo="bla", path="path")


def test_current_source_key(mocker, pygithub_match):
    mocker.patch("raincoat.source.get_branch_commit", return_value="aaabbbcccdddeeefff")

    assert pygithub.PyGithubChecker().current_source_key(pygithub_match) == (
        "python/cpython",
        "aaabbbcccdddeeefff",
    )

    assert pygithub_match.branch_commit == "aaabbbcc"


def test_current_source_key_cache(mocker, pygithub_match):
    get_branch_commit = mocker.patch(
        "raincoat.source.get_branch_commit", return_value="aaabbbcccdddeeefff"
    )

    checker = pygithub.PyGithubChecker()
    a = checker.current_source_key(pygithub_match)
    assert len(get_branch_commit.mock_calls) == 1

    get_branch_commit.reset_mock()

    b = checker.current_source_key(pygithub_match)

    assert get_branch_commit.mock_calls == []
    assert a == b


def test_match_source_key(pygithub_match):
    assert pygithub.PyGithubChecker().match_source_key(pygithub_match) == (
        "python/cpython",
        "abc123",
    )


def test_get_source_installed(mocker):
    download = mocker.patch(
        "raincoat.match.pypi.source.download_files_from_repo",
        return_value={"file_1.py": ["yay"]},
    )

    result = pygithub.PyGithubChecker().get_source(
        key=pygithub.PyGithubKey("python/cpython", "123abc"), files=["file_1.py"]
    )

    assert result == {"file_1.py": ["yay"]}
    assert download.mock_calls == [
        mocker.call(repo="python/cpython", commit="123abc", files=["file_1.py"])
    ]
