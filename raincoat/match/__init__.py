import difflib


class NotMatching(ValueError):
    pass


class Match(object):
    # Filled at the end of the module
    subclasses = {}
    match_type = None

    def __init__(self, filename, lineno):

        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        return "Match in {}:{}".format(self.filename, self.lineno)

    @classmethod
    def from_comment(cls, match_type, filename, lineno, **kwargs):
        """
        Indentifies the correct Match subclass and
        creates a match
        """
        try:
            return cls.subclasses[match_type](filename, lineno, **kwargs)
        except KeyError:
            raise NotMatching

    checker = NotImplemented

    @classmethod
    def check_matches(cls, matches):
        if cls.checker is NotImplemented:
            raise NotImplementedError()

        return cls.checker().check(matches)

    def check(self, checker, match_block, current_block):
        """
        Compares the matched code against the current code. This
        part should probably be the same for all subclasses.
        """
        if match_block != current_block:
            diff = "\n".join(difflib.ndiff(
                match_block,
                current_block))
            checker.add_error("Code is different : \n{}".format(diff), self)


class Checker(object):

    def add_error(self, error, match):
        self.errors.append((error, match))


from .pypi import PyPIMatch  # noqa
Match.subclasses = {
    match_class.match_type: match_class
    for match_class in [PyPIMatch]
}
