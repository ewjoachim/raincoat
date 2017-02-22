import os
import re

import requests
import six

from raincoat.match import Match, NotMatching
from raincoat import source


def get_merge_commit_sha1(ticket, session):

    # This is an adaptation of
    # https://github.com/django/code.djangoproject.com/blob/
    # cad96e2d980fc0453b34dd3d17ce6cb895e1aa89/trac-env/htdocs/
    # tickethacks.js#L99-L209

    # This is definitely the place where we could USE raincoat
    # ... But there's not yet raincoat comments for github
    # and this code is not released in PyPI
    ticket = int(ticket)
    pr_title_patterns = ["#{} ", "#{},", "#{}:", "#{})"]
    url = "https://api.github.com/search/issues?q="
    args = "repo:django/django+state:closed+in:title+type:pr+"
    args += "+".join(pattern.format(ticket)
                     for pattern in pr_title_patterns)
    response = session.get(
        url + six.moves.urllib.parse.quote(args, safe="+:"))
    response.raise_for_status()
    search_results = response.json()

    merged_regex = re.compile(r'(?:merged|fixed) in \b([0-9a-f]{6,40})\b')

    for pr in search_results["items"]:
        number = pr["number"]

        if number == ticket:
            # skip this element if PR id == ticket id
            continue

        merged = session.get(
            "https://api.github.com/repos/django/django/pulls/{}/merge"
            .format(number)).status_code == 204

        if merged:
            response = session.get(
                    "https://api.github.com/repos/django/django/pulls/{}"
                    .format(number))
            response.raise_for_status()
            pr_details = response.json()

            return pr_details["merge_commit_sha"]

        # Check if the PR was merged manually
        response = session.get(
            "https://api.github.com/repos/django/django/issues/{}/comments"
            .format(number))
        response.raise_for_status()
        comments = response.json()
        for comment in comments:
            merged_in = merged_regex.search(comment["body"])
            if merged_in:
                return merged_in.group(1)


def is_commit_in_version(commit, version, session):
    url = (
        "https://api.github.com/repos/django/django/compare/{}...{}"
        "".format(commit, version))
    response = session.get(url)
    response.raise_for_status()
    diff = response.json()
    return not diff.get("status") == "diverged"


class DjangoChecker(object):

    def get_match_info(self, matches):
        info = {}
        for match in matches:
            info.setdefault(match.ticket, []).append(match)
        return info

    def check(self, matches):
        __, django_version = source.get_current_or_latest_version("django")

        match_info = self.get_match_info(matches)

        return self.check_matches(match_info, django_version)

    def get_session(self, token=None):
        session = requests.Session()
        if token:
            session.auth = tuple(token.split(":"))
        return session

    def check_matches(self, match_info, django_version):
        with self.get_session(os.getenv("RAINCOAT_GITHUB_TOKEN")) as session:
            for ticket, ticket_matches in match_info.items():
                sha1 = get_merge_commit_sha1(ticket, session)
                if sha1:
                    if is_commit_in_version(sha1, django_version, session):
                        for match in ticket_matches:
                            yield (
                                "Ticket #{} has been merged in Django {}"
                                .format(ticket, django_version),
                                match)


class DjangoMatch(Match):
    checker = DjangoChecker
    match_type = "django"
    ticket_regex = re.compile(r'^#?(\d+)$')

    def __init__(self, filename, lineno, ticket):
        super(DjangoMatch, self).__init__(filename, lineno)

        try:
            regex_match = self.ticket_regex.match(ticket)
            self.ticket = int(regex_match.group(1).strip())
        except (AttributeError, TypeError):
            raise NotMatching

    def __str__(self):
        return (
            "Django ticket #{match.ticket} "
            "(from {match.filename}:{match.lineno})".format(match=self))
