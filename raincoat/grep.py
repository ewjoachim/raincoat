from __future__ import absolute_import

import fnmatch
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


def list_python_files(base_dir=".", exclude=None):
    exclude = exclude or []
    exclude = {os.path.normpath(path) for path in exclude}
    for root, folders, files in os.walk(base_dir, topdown=True):

        # Prune excluded folders
        full_pathes = [os.path.normpath(os.path.join(root, folder))
                       for folder in folders]

        folders_to_remove = {
            os.path.basename(folder)
            for pattern in exclude
            for folder in fnmatch.filter(full_pathes, pattern)}

        if folders_to_remove:
            folders[:] = set(folders) - folders_to_remove

        # Prune excluded files
        full_pathes = [os.path.normpath(os.path.join(root, file))
                       for file in files]

        files_to_remove = {os.path.basename(file)
                           for pattern in exclude
                           for file in fnmatch.filter(full_pathes, pattern)}

        for file in set(files) - files_to_remove:
            if file.endswith(".py"):
                yield os.path.normpath(os.path.join(root, file))


def find_in_dir(base_dir=".", exclude=None):
    for python_file in list_python_files(base_dir, exclude=exclude):
        for match in find_in_file(python_file):
            yield match
