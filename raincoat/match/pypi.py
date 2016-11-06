import contextlib
import itertools
import re

from raincoat import source
from raincoat import parse
from raincoat.match import Checker, NotMatching
from raincoat.match import Match
from raincoat.utils import Cleaner


class PyPIChecker(Checker):
    @staticmethod
    def version_key(match):
        return (match.package, match.version)

    @staticmethod
    def path_key(match):
        return match.path

    @classmethod
    def complete_key(cls, match):
        return cls.version_key(match) + (cls.path_key(match),)

    def __init__(self):
        self.errors = []
        self.cleaner = None

    @contextlib.contextmanager
    def cleaner_ctx(self):
        with Cleaner() as cleaner:
            self.cleaner = cleaner
            yield self.cleaner

    def check(self, matches):
        """
        Main entrypoint
        """
        matches = sorted(matches, key=self.complete_key)

        with self.cleaner_ctx():
            # In order to minimize useless computation, we'll analyze
            # all the match for a given package at the same time.
            for (package, version), matches_package in itertools.groupby(
                    matches, key=self.version_key):

                self.check_package(package, version, list(matches_package))

        return self.errors

    def check_package(self, package, version, matches_package):
        """
        For a given package, extract the sources and call compare_contents
        """
        installed, current_version = (
            source.get_current_or_latest_version(package))

        # If we're comparing the same version, let's not
        # waste time and resources.
        if current_version == version:
            return

        for match in matches_package:
            match.other_version = current_version

        # Get the list of files for this package
        # that we'll want to check. We only check those.
        files = set(match.path for match in matches_package)

        # If the package is installed, we'll use its source.
        # Otherwise, we'll download it.
        if not installed:
            current_path = self.cleaner.mkdir()
            source.download_package(package, current_version, current_path)
            current_content = source.open_downloaded(
                current_path, files, package)
        else:
            current_path = source.get_current_path(package)
            current_content = source.open_installed(current_path, files)

        # For the package pointed by the Raincoat comment, we'll always have to
        # download it.
        matched_path = self.cleaner.mkdir()
        source.download_package(package, version, matched_path)
        match_content = source.open_downloaded(matched_path, files, package)

        # fast escape strategy
        if match_content == current_content:
            return

        self.compare_contents(match_content, current_content, matches_package)

    def compare_contents(self, match_content, current_content, matches):
        """
        For 2 sets of source code, compare them, and if there might
        be something different, call compare_files
        """
        match_keys = frozenset(match_content)
        current_keys = frozenset(current_content)

        # Missing files in matched (should not exist)
        unexpectedly_missing = current_keys - match_keys
        if unexpectedly_missing:
            raise ValueError(
                "Raincoat was misconfigured. The following files "
                "do not exist on the package : {}. Offending Raincoat "
                "comments are located here : {}".format(
                    ", ".join(unexpectedly_missing),
                    # TODO : refine the next line.
                    ", ".join(str(match) for match in matches)))

        # Missing files in current
        disappeared_files = match_keys - current_keys
        for file in disappeared_files:
            for match in matches:
                if match.path == file:
                    self.add_error(
                        "File {} has disappeared".format(file), match)

        common_keys = match_keys & current_keys

        for path, path_matches in itertools.groupby(matches, self.path_key):
            if path not in common_keys:
                continue
            match_source = match_content[path]
            current_source = current_content[path]

            # fast escape strategy
            if match_source == current_source:
                continue

            self.compare_files(
                match_source, current_source, list(path_matches))

    def compare_files(self, match_source, current_source, matches):
        """
        For 2 sources of the same file, compare the part that we're
        intereted in and add errors only if those parts are different.
        """
        elements = {match.element for match in matches}
        match_elements = dict(parse.find_elements(match_source, elements))
        current_elements = dict(parse.find_elements(
            current_source, elements))

        match_keys = frozenset(match_elements)
        current_keys = frozenset(current_elements)

        # Missing functions/classes in matched (should not exist)
        unexpectedly_missing = current_keys - match_keys
        if unexpectedly_missing:
            raise ValueError(
                "Raincoat was misconfigured. The following elements "
                "do not exist in the file : {}. Offending Raincoat "
                "comments are located here : {}".format(
                    ", ".join(unexpectedly_missing),
                    # TODO : refine the next line.
                    ", ".join(str(match) for match in matches)))

        # Missing functions/classes in current
        disappeared_elements = match_keys - current_keys
        for element in disappeared_elements:
            for match in matches:
                if match.element == element:
                    self.add_error(
                        "Code object {} has disappeared"
                        "".format(element), match)

        common_keys = match_keys & current_keys

        for match in matches:
            if match.element not in common_keys:
                continue

            match_block = match_elements[match.element]
            current_block = current_elements[match.element]
            match.check(
                checker=self,
                match_block=match_block,
                current_block=current_block)


class PyPIMatch(Match):

    def __init__(self, filename, lineno, package, path, element=None):
        super(PyPIMatch, self).__init__(filename, lineno)

        try:
            self.package, self.version = package.strip().split("==")
        except ValueError:
            raise NotMatching
        self.path = path.strip()
        self.element = element.strip() if element else None

        # This may be filled manually later.
        self.other_version = None

    def __str__(self):
        return (
            "{match.package} == {match.version}{vs_match} "
            "@ {match.path}:{element} "
            "(from {match.filename}:{match.lineno})".format(
                match=self,
                vs_match=" vs {}".format(self.other_version)
                         if self.other_version else "",
                element=self.element or "whole module"))
    checker = PyPIChecker
    match_type = "pypi"
