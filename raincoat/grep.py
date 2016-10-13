from __future__ import absolute_import

import os
import re


REGEX = (r'# Raincoat: package "(?P<package>[^=]+)==(?P<version>[^"]+)" '
         'path "(?P<path>[^"]+)" (?:"(?P<code_object>[^"]+)")?')


class Match(object):
    def __init__(self, package, version, path,
                 filename, lineno, code_object=None):

        self.package = package
        self.version = version
        self.path = path
        self.filename = filename
        self.lineno = lineno
        self.code_object = code_object

    def __str__(self):
        return (
            "{match.package} == {match.version} "
            "@ {match.path}:{match.code_object} "
            "(from {match.filename}:{match.lineno})".format(match=self))


def find_in_string(file_content, filename):
    for match in re.finditer(REGEX, file_content):
        lineno = lineno = file_content.count(
            os.linesep, 0, match.start()) + 1

        kwargs = match.groupdict()
        yield Match(lineno=lineno, filename=filename, **kwargs)


def find_in_file(filename):
    with open(filename) as handler:
        return find_in_string(handler.read(), filename)


def list_python_files(base_dir="."):
    for root, __, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                yield os.path.normpath(os.path.join(root, file))


def find_in_dir(base_dir="."):
    for python_file in list_python_files(base_dir):
        for match in find_in_file(python_file):
            yield match
