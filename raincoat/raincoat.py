from __future__ import absolute_import

import itertools
import shutil
import tempfile
import difflib

from raincoat import grep
from raincoat import source
from raincoat import parse


class Raincoat(object):
    """
    Responsible for gluing together all the parts of the package.
    Raincoat.raincoat is the entrypoint that receives a path and
    will:
     - Find all the Raincoat comments
     - Compute the list of packages we need to check
     - For each package
        - get the 2 compared versions (download in a temp folder)
        - extract the necessary files from the source code
        - Extract the necessary fonctions, methods and classes
          from those files
        - Compare that
        - Add errors to self.errors when appropriate.
        - Delete the temp folders

    """
    # In large parts of this class, the terms "match" and "current"
    # are frequently used to designate the version of the code that
    # matches the Raincoat: comment pattern and the current version
    # of the code (or the latest one if the package is not installed)

    def __init__(self):
        self.to_clean = set()
        self.errors = []

    def add_error(self, error, match):
        self.errors.append((error, match))

    @staticmethod
    def version_key(match):
        return (match.package, match.version)

    @staticmethod
    def path_key(match):
        return match.path

    @classmethod
    def complete_key(cls, match):
        return cls.version_key(match) + (cls.path_key(match),)

    def raincoat(self, path):
        """
        Main entrypoint
        """
        matches = sorted(grep.find_in_dir(path), key=self.complete_key)

        try:
            # In order to minimize useless computation, we'll analyze
            # all the match for a given package at the same time.
            for (package, version), matches_package in itertools.groupby(
                    matches, key=self.version_key):

                self.check_package(package, version, list(matches_package))
        finally:
            self._clean()

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
            current_path = tempfile.mkdtemp()
            self._add_to_clean(current_path)
            source.download_package(package, current_version, current_path)
            current_content = source.open_downloaded(
                current_path, files, package)
        else:
            current_path = source.get_current_path(package)
            current_content = source.open_installed(current_path, files)

        # For the package pointed by the Raincoat comment, we'll always have to
        # download it.
        matched_path = tempfile.mkdtemp()
        self._add_to_clean(matched_path)
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
            if match_block != current_block:
                diff = "\n".join(difflib.ndiff(
                    match_block,
                    current_block))
                self.add_error("Code is different : \n{}".format(diff), match)

    def _add_to_clean(self, dirname):
        self.to_clean.add(dirname)

    def _clean(self):
        for dir_to_clean in self.to_clean:
            shutil.rmtree(dir_to_clean)
