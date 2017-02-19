import difflib

from raincoat import parse, source
from raincoat.match import Match, NotMatching
from raincoat.utils import Cleaner


class PyPIChecker(object):

    def check(self, matches):
        """
        Main entrypoint
        """
        match_info = self.get_match_info(matches)

        packages = dict(self.get_packages(
            match_info=match_info))

        return self.compare_packages(packages, match_info)

    def get_match_info(self, matches):
        match_info = {}
        for match in matches:
            (match_info
             .setdefault((match.package, match.version), {})
             .setdefault(match.path, {})
             .setdefault(match.element, [])
             .append(match))
        return match_info

    def get_packages(self, match_info):

        # In order to minimize useless computation, we'll analyze
        # all the match for a given package at the same time.

        current_packages = {}

        for (package, version), package_info in sorted(match_info.items()):

            current_source = None
            try:
                current_source, current_version = current_packages[package]
            except KeyError:
                installed, current_version = (
                    source.get_current_or_latest_version(package))

            # If we're comparing the same version, let's not
            # waste time and resources.
            if current_version == version:
                continue

            files = list(package_info)

            match_source = self.download_package(
                package, version, files)

            if not current_source:
                if installed:
                    current_source = self.retrieve_installed_package(
                        package, files)
                else:
                    current_source = self.download_package(
                        package, current_version, files)

                current_packages[package] = (current_source, current_version)

            if match_source == current_source:
                continue

            self.mark_other_version(match_info, current_version)

            yield (package, version), (match_source, current_source)

    def download_package(self, package, version, files):
        with Cleaner() as cleaner:
            path = cleaner.mkdir()
            source.download_package(package, version, path)
            return source.open_downloaded(path, files, package)

    def retrieve_installed_package(self, package, files):
        path = source.get_current_path(package)
        return source.open_installed(path, files)

    def mark_other_version(self, info, version):
        for match in self.get_all_matches(info):
            match.other_version = version

    def compare_packages(self, packages, match_info):
        for package_key, (match_source, current_source) in packages.items():
            package_info = match_info[package_key]
            package_name, package_version = package_key
            files = dict(self.get_differences(
                match_dict=match_source,
                current_dict=current_source))

            for path, (match_file, current_file) in files.items():
                file_info = package_info[path]
                if match_file is None:
                    for match in self.get_all_matches(file_info):
                        yield ("Invalid Raincoat PyPI comment : {} does not "
                               "exist in {}=={}"
                               .format(path, package_name, package_version),
                               match)
                    continue

                if current_file is None:
                    for match in self.get_all_matches(file_info):
                        yield ("File {} disappeared from {}"
                               .format(path, package_name),
                               match)
                    continue

                names = list(file_info)
                match_elements = dict(
                    parse.find_elements(match_file, names))
                current_elements = dict(
                    parse.find_elements(current_file, names))

                elements = dict(self.get_differences(
                    match_dict=match_elements,
                    current_dict=current_elements))

                if None in file_info:
                    for match in file_info[None]:
                        yield self.compare_blocks(
                            match=match,
                            match_block=match_file.splitlines(),
                            current_block=current_file.splitlines(),
                            path=path)

                for name, (match_block, current_block) in elements.items():
                    if not name:
                        continue

                    block_info = file_info[name]
                    if match_block is None:
                        for match in block_info:
                            yield ("Invalid Raincoat PyPI comment : {} does "
                                   "not exist in {} in {}=={}"
                                   .format(name, path, package_name,
                                           package_version),
                                   match)
                        continue

                    if current_block is None:
                        for match in block_info:
                            yield ("{} disappeared from {} in {}"
                                   .format(name, path, package_name),
                                   match)
                        continue

                    for match in block_info:
                        yield self.compare_blocks(
                            match=match,
                            match_block=match_block,
                            current_block=current_block,
                            path=path)

    def get_all_matches(self, info):
        """
        Recursively yields all matches in the given nested dict.
        """
        for element in info.values():
            if isinstance(element, dict):
                for match in self.get_all_matches(element):
                    yield match
            else:
                for match in element:
                    yield match

    def get_differences(self, match_dict, current_dict):
        """
        Returns the keys for which values in the 2 dicts are
        different, and the said values.
        """
        match_keys = frozenset(match_dict)
        current_keys = frozenset(current_dict)

        all_keys = match_keys | current_keys

        for key in all_keys:
            match_value = match_dict.get(key)
            current_value = current_dict.get(key)

            if match_value == current_value:
                continue

            yield(key, (match_value, current_value))

    def compare_blocks(self, match, match_block, current_block, path):
        """
        Compares the matched code against the current code
        """

        diff = "\n".join(difflib.unified_diff(
            match_block,
            current_block,
            fromfile=path, tofile=path,
            lineterm=""))
        return "Code is different:\n{}".format(diff), match


class PyPIMatch(Match):

    def __init__(self, filename, lineno, package, path, element=None):
        try:
            self.package, self.version = package.strip().split("==")
        except ValueError:
            raise NotMatching
        self.path = path.strip()
        self.element = element.strip() if element else None

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
    checker = PyPIChecker
    match_type = "pypi"
