import itertools
import shutil
import tempfile
import difflib

from raincoat import grep
from raincoat import source
from raincoat import parse


class Raincoat(object):

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
            for (package, version), matches_package in itertools.groupby(matches, key=self.version_key):

                self.check_package(package, version, list(matches_package))
        finally:
            self._clean()

    def check_package(self, package, version, matches_package):
        installed, current_version = source.get_current_or_latest_version(package)
        if current_version == version:
            return

        for match in matches_package:
            match.other_version = current_version

        files = set(match.path for match in matches_package)

        if not installed:
            current_path = tempfile.mkdtemp()
            self._add_to_clean(current_path)
            source.download_package(package, current_version, current_path)
            current_content = source.open_downloaded(current_path, files, package)
        else:
            current_path = source.get_current_path(package)
            current_content = source.open_installed(current_path, files)

        matched_path = tempfile.mkdtemp()
        self._add_to_clean(matched_path)
        source.download_package(package, version, matched_path)
        match_content = source.open_downloaded(matched_path, files, package)
        self.compare_contents(match_content, current_content, matches_package)

    def compare_contents(self, match_content, current_content, matches):
        match_keys = frozenset(match_content)
        current_keys = frozenset(current_content)

        # Missing files in match (should not exist)
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

            if match_source == current_source:
                continue

            self.compare_files(match_source, current_source, list(path_matches))

    def compare_files(self, match_source, current_source, matches):
        code_objects = {match.code_object for match in matches}
        match_objects = dict(parse.find_objects(match_source, code_objects))
        current_objects = dict(parse.find_objects(current_source, code_objects))

        match_keys = frozenset(match_objects)
        current_keys = frozenset(current_objects)

        # Missing files in match (should not exist)
        unexpectedly_missing = current_keys - match_keys
        if unexpectedly_missing:
            raise ValueError(
                "Raincoat was misconfigured. The following code objects "
                "do not exist in the file : {}. Offending Raincoat "
                "comments are located here : {}".format(
                    ", ".join(unexpectedly_missing),
                    # TODO : refine the next line.
                    ", ".join(str(match) for match in matches)))

        # Missing files in current
        disappeared_objects = match_keys - current_keys
        for code_object in disappeared_objects:
            for match in matches:
                if match.code_object == code_object:
                    self.add_error(
                        "Code object {} has disappeared".format(code_object), match)

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
                self.add_error("Code is different : {}".format(diff), match)

    def _add_to_clean(self, dirname):
        self.to_clean.add(dirname)

    def _clean(self):
        for dir_to_clean in self.to_clean:
            shutil.rmtree(dir_to_clean)
