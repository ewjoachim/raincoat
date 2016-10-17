import difflib


class NotMatching(ValueError):
    pass


class Match(object):
    # Filled at the end of the module
    subclasses = []

    def __init__(self, package, version, path,
                 filename, lineno, code_object=None):

        self.package = package
        self.version = version
        self.path = path
        self.filename = filename
        self.lineno = lineno
        self.code_object = code_object

        # This may be filled manually later.
        self.other_version = None

    def __str__(self):
        return (
            "{match.package} == {match.version}{vs_match} "
            "@ {match.path}:{code_object} "
            "(from {match.filename}:{match.lineno})".format(
                match=self,
                vs_match=" vs {}".format(self.other_version)
                         if self.other_version else "",
                code_object=self.code_object or "whole module"))

    @classmethod
    def from_comment(cls, comment, filename, lineno):
        """
        Indentifies the correct Match subclass and
        creates a match
        """
        for subcls in cls.subclasses:

            try:
                return subcls.match(comment, filename, lineno)
            except NotMatching:
                continue
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


class RegexMatchMixin(object):
    regex = NotImplemented

    @classmethod
    def match(cls, comment, filename, lineno):
        if cls.regex is NotImplemented:
            raise NotImplementedError(
                "RegexMatchMixin subclasses need a regex.")

        args_match = cls.regex.match(comment)
        if not args_match:
            raise NotMatching()

        kwargs = args_match.groupdict()
        return cls(lineno=lineno, filename=filename, **kwargs)


class Checker(object):

    def add_error(self, error, match):
        self.errors.append((error, match))

from .pypi import PyPIMatch  # noqa
Match.subclasses.extend([PyPIMatch])
