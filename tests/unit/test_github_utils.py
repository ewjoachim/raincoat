from __future__ import annotations

from raincoat import github_utils


def test_get_session(mocker):
    mocker.patch("os.getenv", return_value="a:b")
    assert github_utils.get_session().auth == ("a", "b")


def test_get_session_no_token(mocker):
    mocker.patch("os.getenv", return_value=None)
    assert github_utils.get_session().auth is None
