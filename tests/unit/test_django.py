from __future__ import annotations

import pytest

from raincoat.match import NotMatching, django


@pytest.fixture
def fixed_match():
    return django.DjangoMatch(filename="bla.py", lineno=12, ticket="#26976")


@pytest.fixture
def not_fixed_match():
    return django.DjangoMatch(filename="bla.py", lineno=12, ticket="#27754")


def test_django_string(fixed_match):
    assert str(fixed_match) == "Django ticket #26976 (from bla.py:12)"


def test_ticket_no_pound():
    assert django.DjangoMatch(filename="bla.py", lineno=12, ticket="26976")


def test_ticket_not_a_number():
    with pytest.raises(NotMatching):
        django.DjangoMatch(filename="bla.py", lineno=12, ticket="#269sdf76")


def test_is_commit_in_version_no(mocker):
    session = mocker.MagicMock()
    session.get.return_value.json.return_value = {"status": "diverged"}

    assert not django.is_commit_in_version("abcdef", "1.9", session)

    assert session.mock_calls[0] == mocker.call.get(
        "https://api.github.com/repos/django/django/" "compare/abcdef...1.9"
    )


def test_is_commit_in_version_yes(mocker):
    assert django.is_commit_in_version("abcdef", "1.9", mocker.MagicMock())


django_repo = "https://api.github.com/repos/django/django"


def test_get_merge_commit_sha1(mocker):
    session = mocker.MagicMock()

    session.get.return_value.status_code = 204
    session.get.return_value.json.side_effect = [
        {"items": [{"number": 1234}]},
        {"merge_commit_sha": "deadbeef"},
    ]

    assert django.get_merge_commit_sha1(26976, session) == "deadbeef"
    query = (
        "repo:django%2Fdjango+state:closed+in:title+"
        "type:pr+%2326976%20+%2326976%2C+%2326976:+%2326976%29"
    )

    assert session.get.call_args_list == [
        mocker.call("https://api.github.com/search/issues?q=" + query),
        mocker.call(django_repo + "/pulls/1234/merge"),
        mocker.call(django_repo + "/pulls/1234"),
    ]


def test_get_merge_commit_sha1_manually_merged(mocker):
    session = mocker.MagicMock()

    session.get.return_value.status_code = 200
    session.get.return_value.json.side_effect = [
        {"items": [{"number": 1234}]},
        [{"body": "merged in baadf00d"}],
    ]

    assert django.get_merge_commit_sha1(26976, session) == "baadf00d"
    query = (
        "repo:django%2Fdjango+state:closed+in:title+"
        "type:pr+%2326976%20+%2326976%2C+%2326976:+%2326976%29"
    )

    assert session.get.call_args_list == [
        mocker.call("https://api.github.com/search/issues?q=" + query),
        mocker.call(django_repo + "/pulls/1234/merge"),
        mocker.call(django_repo + "/issues/1234/comments"),
    ]


def test_get_merge_commit_sha1_not_merged(mocker):
    session = mocker.MagicMock()

    session.get.return_value.status_code = 200
    session.get.return_value.json.side_effect = [
        {"items": [{"number": 1234}]},
        [{"body": "yay"}],
    ]

    assert django.get_merge_commit_sha1(26976, session) is None
    query = (
        "repo:django%2Fdjango+state:closed+in:title+"
        "type:pr+%2326976%20+%2326976%2C+%2326976:+%2326976%29"
    )

    assert session.get.call_args_list == [
        mocker.call("https://api.github.com/search/issues?q=" + query),
        mocker.call(django_repo + "/pulls/1234/merge"),
        mocker.call(django_repo + "/issues/1234/comments"),
    ]


def test_get_merge_commit_sha1_same_number(mocker):
    session = mocker.MagicMock()

    session.get.return_value.status_code = 200
    session.get.return_value.json.side_effect = [
        {"items": [{"number": 26976}]},
        [{"body": "merged in 01020304"}],
    ]

    assert django.get_merge_commit_sha1(26976, session) is None
    query = (
        "repo:django%2Fdjango+state:closed+in:title+"
        "type:pr+%2326976%20+%2326976%2C+%2326976:+%2326976%29"
    )

    assert session.get.call_args_list == [
        mocker.call("https://api.github.com/search/issues?q=" + query),
    ]


def test_get_match_info(fixed_match, not_fixed_match):
    assert django.DjangoChecker().get_match_info(
        [fixed_match, fixed_match, not_fixed_match]
    ) == {27754: [not_fixed_match], 26976: [fixed_match, fixed_match]}


def test_check_matches(mocker, fixed_match):
    mocker.patch("raincoat.match.django.get_merge_commit_sha1", return_value="123")
    mocker.patch("raincoat.match.django.is_commit_in_version", return_value=True)

    result = list(django.DjangoChecker().check_matches({26976: [fixed_match]}, "1.9"))
    assert result == [("Ticket #26976 has been merged in Django 1.9", fixed_match)]


def test_check_matches_no_pr(mocker, fixed_match):
    mocker.patch("raincoat.match.django.get_merge_commit_sha1", return_value=None)

    result = list(django.DjangoChecker().check_matches({26976: [fixed_match]}, "1.9"))
    assert result == []


def test_check_matches_not_merged(mocker, fixed_match):
    mocker.patch("raincoat.match.django.get_merge_commit_sha1", return_value="123")
    mocker.patch("raincoat.match.django.is_commit_in_version", return_value=False)

    result = list(django.DjangoChecker().check_matches({26976: [fixed_match]}, "1.9"))
    assert result == []


def test_check(mocker, fixed_match):
    mocker.patch("raincoat.match.django.get_merge_commit_sha1", return_value="123")
    mocker.patch("raincoat.match.django.is_commit_in_version", return_value=True)
    mocker.patch(
        "raincoat.match.django.source.get_current_or_latest_version",
        return_value=(True, "1.9"),
    )

    result = list(django.DjangoChecker().check([fixed_match]))

    assert result == [("Ticket #26976 has been merged in Django 1.9", fixed_match)]
