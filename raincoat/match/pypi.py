from collections import namedtuple

from raincoat import source
from raincoat.match import NotMatching
from raincoat.match.python import PythonChecker, PythonMatch
from raincoat.utils import Cleaner


PyPIKey = namedtuple("PyPIKey", "package version installed")


class PyPIChecker(PythonChecker):

    def current_source_key(self, match):
        installed, version = source.get_current_or_latest_version(
            match.package)
        pypi_key = PyPIKey(match.package, version, installed)
        match.other_version = version
        return pypi_key

    def match_source_key(self, match):
        pypi_key = PyPIKey(match.package, match.version, installed=False)
        return pypi_key

    def get_source(self, key, files):
        if key.installed:
            path = source.get_current_path(key.package)
            return source.open_installed(path, files)
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
                         if self.other_version else "",
                element=self.element or "whole module"))

    def format_line(self, line, color, i):
        line = super(PyPIMatch, self).format_line(line, color, i)
        if line[0] in "+-@":
            line = color["diff" + line[0]](line)

        return line

    checker = PyPIChecker
    match_type = "pypi"
