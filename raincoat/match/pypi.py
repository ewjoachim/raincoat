import contextlib
import itertools
import re

from raincoat import source
from raincoat import parse
from raincoat.match import Checker
from raincoat.match import Match
from raincoat.match import RegexMatchMixin
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
        code_objects = {match.code_object for match in matches}
        match_objects = dict(parse.find_objects(match_source, code_objects))
        current_objects = dict(parse.find_objects(
            current_source, code_objects))

        match_keys = frozenset(match_objects)
        current_keys = frozenset(current_objects)

        # Missing functions/classes in matched (should not exist)
        unexpectedly_missing = current_keys - match_keys
        if unexpectedly_missing:
            raise ValueError(
                "Raincoat was misconfigured. The following code objects "
                "do not exist in the file : {}. Offending Raincoat "
                "comments are located here : {}".format(
                    ", ".join(unexpectedly_missing),
                    # TODO : refine the next line.
                    ", ".join(str(match) for match in matches)))

        # Missing functions/classes in current
        disappeared_objects = match_keys - current_keys
        for code_object in disappeared_objects:
            for match in matches:
                if match.code_object == code_object:
                    self.add_error(
                        "Code object {} has disappeared"
                        "".format(code_object), match)

        common_keys = match_keys & current_keys

        for match in matches:
            if match.code_object not in common_keys:
                continue

            match_block = match_objects[match.code_object]
            current_block = current_objects[match.code_object]
            match.check(
                checker=self,
                match_block=match_block,
                current_block=current_block)


class PyPIMatch(RegexMatchMixin, Match):

    regex = re.compile(
        r'package "(?P<package>[^=]+)==(?P<version>[^"]+)" '
        'path "(?P<path>[^"]+)"'
        '(?: "(?P<code_object>[^"]+)")?')

    checker = PyPIChecker
