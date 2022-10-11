from __future__ import annotations

from collections import namedtuple

from raincoat import source
from raincoat.match import NotMatching
from raincoat.match.python import PythonChecker, PythonMatch

PyGithubKey = namedtuple("PyGithubKey", "repo commit")


class PyGithubChecker(PythonChecker):
    def __init__(self, *args, **kwargs):
        super(PyGithubChecker, self).__init__(*args, **kwargs)
        self.branch_commit_cache = {}

    def current_source_key(self, match):
        branch_key = (match.repo, match.branch)
        if branch_key in self.branch_commit_cache:
            key = self.branch_commit_cache[branch_key]
            match.branch_commit = key.commit
            return key

        commit = source.get_branch_commit(match.repo, match.branch)
        github_key = PyGithubKey(repo=match.repo, commit=commit)

        self.branch_commit_cache[(match.repo, match.branch)] = github_key
        match.branch_commit = commit[:8]

        return github_key

    def match_source_key(self, match):
        return PyGithubKey(repo=match.repo, commit=match.commit)

    def get_source(self, key, files):
        return source.download_files_from_repo(
            repo=key.repo, commit=key.commit, files=files
        )


class PyGithubMatch(PythonMatch):
    def __init__(self, filename, lineno, repo, path, element="", branch="master"):
        try:
            self.repo, self.commit = repo.strip().split("@")
        except ValueError:
            raise NotMatching
        self.path = path.strip()
        self.element = element.strip()
        self.branch = branch

        # This may be filled manually later.
        self.branch_commit = None

        super(PyGithubMatch, self).__init__(filename, lineno)

    def __str__(self):
        return (
            "{match.repo}@{match.commit} vs {match.branch} branch"
            "{branch_commit} at {match.path}:{element} "
            "(from {match.filename}:{match.lineno})".format(
                match=self,
                branch_commit=" ({})".format(self.branch_commit)
                if self.branch_commit
                else "",
                element=self.element or "whole module",
            )
        )

    checker = PyGithubChecker
