from __future__ import annotations

from collections import namedtuple

from raincoat import source
from raincoat.match import NotMatching
from raincoat.match.python import PythonChecker, PythonMatch
from raincoat.utils import Cleaner

PyPIKey = namedtuple("PyPIKey", "package version installed")


class PyPIChecker(PythonChecker):
    def __init__(self, *args, **kwargs):
        super(PyPIChecker, self).__init__(*args, **kwargs)
        self.package_cache = {}

    def current_source_key(self, match):
        if match.package in self.package_cache:
            key = self.package_cache[match.package]
            match.other_version = key.version
            return key

        installed, version = source.get_current_or_latest_version(match.package)
        pypi_key = PyPIKey(match.package, version, installed)

        self.package_cache[match.package] = pypi_key
        match.other_version = version

        return pypi_key

    def match_source_key(self, match):
        return PyPIKey(match.package, match.version, installed=False)

    def get_source(self, key, files):
        if key.installed:
            all_files = source.get_distributed_files(key.package)
            return source.open_installed(all_files, files_to_open=files)
        else:
            with Cleaner() as cleaner:
                path = cleaner.mkdir()
                source.download_package(key.package, key.version, path)
                return source.open_downloaded(path, files)


class PyPIMatch(PythonMatch):
    def __init__(self, filename, lineno, package, path, element=""):
        try:
            self.package, self.version = package.strip().split("==")
        except ValueError:
            raise NotMatching
        self.path = path.strip()
        self.element = element.strip()

        # This may be filled manually later.
        self.other_version = None

        super(PyPIMatch, self).__init__(filename, lineno)

    def __str__(self):
        return (
            "{match.package} == {match.version}{vs_match} "
            "@ {match.path}:{element} "
            "(from {match.filename}:{match.lineno})".format(
                match=self,
                vs_match=" vs {}".format(self.other_version)
                if self.other_version
                else "",
                element=self.element or "whole module",
            )
        )

    checker = PyPIChecker
