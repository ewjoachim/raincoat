from raincoat.raincoat import Raincoat
from raincoat.match import Match

from .test_match import get_match


def test_raincoat(mocker):
    find_in_dir = mocker.patch("raincoat.grep.find_in_dir")

    class MatchSubtype(Match):
        def __init__(self, filename, lineno, **kwargs):
            super(MatchSubtype, self).__init__(filename, lineno)

        @classmethod
        def check_matches(cls, matches):
            assert matches == cls.matches
            return [("Oh :(", matches[0])]

    class MatchSubtypeA(MatchSubtype):
        pass

    class MatchSubtypeB(MatchSubtype):
        pass

    Match.subclasses.update({
        "a": MatchSubtypeA, "b": MatchSubtypeB
    })

    matches = [
        get_match(match_type="a", package="a", path="a"),
        get_match(match_type="b", package="b"),
        get_match(match_type="a", package="a", path="b"),
    ]
    match1, match2, match3 = matches
    MatchSubtypeA.matches = [match1, match3]

    MatchSubtypeB.matches = [match2]

    find_in_dir.return_value = matches

    raincoat = Raincoat()

    # Asserts are made in the check_package method
    list(raincoat.raincoat("."))
