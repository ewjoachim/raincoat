from __future__ import annotations

import difflib
from collections import OrderedDict
from itertools import groupby
from operator import itemgetter

from raincoat import constants, parse
from raincoat.match import Match


class PythonChecker(object):
    """
    Find the matches related to the same source, find all the
    files it needs, then parse these files and compare the elements
    inside.

    This is an abstract class.
    """

    def current_source_key(self, match):
        """
        Should return a hashable identifier of the source code
        to read for the "current" version of the code.
        """
        raise NotImplementedError

    def match_source_key(self, match):
        """
        Should return a hashable identifier of the source code
        to read for the version of the code at the time the
        Raincoat comment (the "match") was written.
        """
        raise NotImplementedError

    def get_source(self, key, files):
        """
        The key is the one defined in *_source_key
        The files are the set of files we want in this source.
        """
        raise NotImplementedError

    def check(self, matches):
        """
        Main entrypoint
        """
        matches = list(matches)

        # A set of all source keys.
        # source_key should be: (source, path, element)
        source_keys = sorted(set(self.get_source_keys(matches)))

        # A dict: (source_key, path, element_key) > element
        elements = dict(self.get_elements(source_keys))

        # A generator yielding every match and the error message
        return self.run_matches(matches, elements)

    def get_source_keys(self, matches):
        for match in matches:
            path, element = match.get_path(), match.get_element()
            match_key = self.match_source_key(match)
            yield match_key, path, element
            current_key = self.current_source_key(match)
            yield current_key, path, element

    def get_elements(self, source_keys):
        grouped_keys = group_composite(source_keys)
        for source_key, files_dict in grouped_keys.items():
            files_source = self.get_source(source_key, set(files_dict))
            for path, element_names in files_dict.items():
                file_source = files_source[path]
                if file_source is constants.FILE_NOT_FOUND:
                    for element_name in element_names:
                        full_key = (source_key, path, element_name)
                        yield full_key, constants.FILE_NOT_FOUND
                else:
                    elements = parse.find_elements(file_source, element_names)
                    for element_name, element_source in elements:
                        full_key = (source_key, path, element_name)
                        yield full_key, element_source

    def run_matches(self, matches, elements):
        for match in matches:
            path, element = match.get_path(), match.get_element()

            match_key = (self.match_source_key(match), path, element)
            current_key = (self.current_source_key(match), path, element)

            match_element = elements.get(match_key)
            current_element = elements.get(current_key)

            not_found = match_element in (
                constants.FILE_NOT_FOUND,
                constants.ELEMENT_NOT_FOUND,
            )

            if match_element != current_element or not_found:
                yield self.run_match(
                    match=match,
                    match_element=match_element,
                    current_element=current_element,
                )

    def run_match(self, match, match_element, current_element):

        if match_element is constants.FILE_NOT_FOUND:
            return (
                "Invalid Raincoat PyPI comment : {match.path} does "
                "not exist"
                "".format(match=match),
                match,
            )
        if match_element is constants.ELEMENT_NOT_FOUND:
            return (
                "Invalid Raincoat PyPI comment : {match.element} does "
                "not exist in {match.path}"
                "".format(match=match),
                match,
            )

        if current_element is constants.FILE_NOT_FOUND:
            return ("File {match.path} disappeared" "".format(match=match), match)
        if current_element is constants.ELEMENT_NOT_FOUND:
            return (
                "Element {match.element} disappeared from "
                "{match.path}"
                "".format(match=match),
                match,
            )

        path = match.get_path()
        diff = "\n".join(
            difflib.unified_diff(
                match_element, current_element, fromfile=path, tofile=path, lineterm=""
            )
        )
        return "Code is different:\n{}".format(diff), match


def group_composite(elements):
    """
    Create a nested structure by grouping iterables
    based on common first elements

    Input is expected to be sorted.
    All input is expected to be of the same length

    >>> group_composite(["abc", "abd", "acd", "bbc"])
    {"a": {"b": ["c", "d"], "c": ["d"]}, "b": {"b": ["c"]}}

    """
    elements = list(elements)

    # End of recursion
    if len(elements[0]) == 1:
        return list(map(itemgetter(0), elements))

    result = OrderedDict()
    for key, sub_elements in groupby(elements, itemgetter(0)):
        result[key] = group_composite(el[1:] for el in sub_elements)

    return result


class PythonMatch(Match):
    def get_path(self):
        return self.path

    def get_element(self):
        return self.element

    def format_line(self, line, color, i):
        line = super(PythonMatch, self).format_line(line, color, i)
        if line[0] in "+-@":
            line = color["diff" + line[0]](line)

        return line
