class NotMatching(Exception):
    pass


class Match(object):
    # Filled at the end of the module
    match_type = NotImplemented
    checker = NotImplemented

    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        return "Match in {}:{}".format(self.filename, self.lineno)


def match_from_comment(match_type, filename, lineno, **kwargs):
    """
    Indentifies the correct Match subclass and
    creates a match
    """
    try:
        return match_types[match_type](filename, lineno, **kwargs)
    except KeyError:
        raise NotMatching


def check_matches(matches):
    for match_type, matches_for_type in matches.items():
        match_class = match_types[match_type]
        checker = match_class.checker

        if checker is NotImplemented:
            raise NotImplementedError(
                "{} has no checker".format(match_class))

        for difference in checker().check(matches_for_type):
            yield difference


def fill_match_types(match_types, match_classes):
    for match_class in match_classes:
        match_type = match_class.match_type

        if match_type is NotImplemented:
            raise NotImplementedError(
                "{} has no match_type".format(match_class))

        match_types[match_type] = match_class


from .pypi import PyPIMatch  # noqa
from .django import DjangoMatch  # noqa
match_classes = [PyPIMatch, DjangoMatch]

match_types = {}

fill_match_types(match_types, match_classes)
