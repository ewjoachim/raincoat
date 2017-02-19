from __future__ import absolute_import

import itertools

from . import grep
from .match import check_matches


class Raincoat(object):
    """
    Responsible for gluing together all the parts of the package.
    Raincoat.raincoat is the entrypoint that receives a path and
    will:
     - Find all the Raincoat comments
     - Find all the corresponding code
     - Add errors

    """
    # In large parts of this class, the terms "match" and "current"
    # are frequently used to designate the version of the code that
    # matches the Raincoat: comment pattern and the current version
    # of the code (or the latest one if the package is not installed)

    @staticmethod
    def class_key(match):
        return match.__class__

    @staticmethod
    def class_key_id(match):
        return id(match.__class__)

    def raincoat(self, path):
        """
        Main entrypoint
        """
        matches = sorted(grep.find_in_dir(path), key=self.class_key_id)
        # In order to minimize useless computation, we'll analyze
        # all the match for a given package at the same time.
        matches_dict = {}
        for match_class, matches_for_class in itertools.groupby(
                matches, key=self.class_key):
            matches_for_class = list(matches_for_class)
            matches_dict[match_class.match_type] = matches_for_class

        return check_matches(matches_dict)
