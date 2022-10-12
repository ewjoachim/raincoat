"""
Responsible for gluing together all the parts of the package.
raincoat is the entrypoint that receives a path and
will:
 - Find all the Raincoat comments
 - Find all the corresponding code
 - Format errors
 - Yield them

"""

from __future__ import absolute_import, annotations

import itertools

from . import grep
from .color import get_color
from .match import check_matches


def class_key(match):
    return match.__class__


def class_key_name(match):
    return match.__class__.__name__


def raincoat(path, exclude=None, color=False):
    """
    Main entrypoint
    """
    matches = sorted(grep.find_in_dir(path, exclude=exclude), key=class_key_name)

    matches_dict = {}
    for match_class, matches_for_class in itertools.groupby(matches, key=class_key):
        matches_for_class = list(matches_for_class)
        matches_dict[match_class.match_type] = matches_for_class

    color_obj = get_color(color)
    for error, match in check_matches(matches_dict):
        yield match.format(error, color_obj)
