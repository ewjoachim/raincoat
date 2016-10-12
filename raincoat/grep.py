import os
import re

from collections import namedtuple


REGEX = r'# Raincoat: package "(?P<package>[^=]+)==(?P<version>[^"]+)" path "(?P<path>[^"]+)" "(?P<code_object>[^"]+)"'


Match = namedtuple("Match",
                   ["package", "version", "path",
                    "code_object", "filename", "lineno"])


def find_in_string(file_content, filename):
    print(file_content)
    for match in re.finditer(REGEX, file_content):
        lineno = lineno = file_content.count(
            os.linesep, 0, match.start()) + 1

        yield Match(*match.groups(), lineno=lineno, filename=filename)


def find_in_file(filename):
    with open(filename) as handler:
        return find_in_string(handler.read(), filename)


def list_python_files(base_dir="."):
    for root, __, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                yield os.path.normpath(os.path.join(base_dir, root, file))


def find_in_dir(base_dir="."):
    for python_file in list_python_files(base_dir):
        for match in find_in_file(python_file):
            yield match
