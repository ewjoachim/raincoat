from __future__ import absolute_import

import logging
import os
import re

from .match import NotMatching, match_from_comment

logger = logging.getLogger(__name__)


REGEX = re.compile(r'# Raincoat: ([a-z]+) (.+)(\n|#|$)')
ARGS_REGEX = re.compile(r' *([^ ]+): *([^ ]+)(?: *|$)')


def find_in_string(file_content, filename):
    for match in REGEX.finditer(file_content):
        lineno = lineno = file_content.count(
            os.linesep, 0, match.start()) + 1

        kwargs_str = match.group(2).strip()
        kwargs = dict(
            pair.groups()
            for pair in ARGS_REGEX.finditer(kwargs_str))

        try:
            match = match_from_comment(match_type=match.group(1),
                                       filename=filename,
                                       lineno=lineno,
                                       **kwargs)

        except NotMatching:
            logger.warning("Unrecognized Raincoat comment at {}:{}\n{}".format(
                filename, lineno, match.group(0)))
            continue

        yield match


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
