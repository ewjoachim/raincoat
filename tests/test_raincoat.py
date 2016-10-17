from raincoat.raincoat import Raincoat
from raincoat.match import Match

from .test_match import get_match


def test_raincoat(mocker):
    # The test strategy is a little contrieved here but the problem
    # is that we'll take match and call a classmethod on their class
    # so it's not easy to mock, because the Mock class itself is
    # not a mock.

    # If you have an idea on how to do this better.

    find_in_dir = mocker.patch("raincoat.grep.find_in_dir")

    class MatchSubtype(Match):
        @classmethod
        def check_matches(cls, matches):
            assert matches == cls.matches
            return [("Oh :(", matches[0])]

    class MatchSubtypeA(MatchSubtype):
        pass

    class MatchSubtypeB(MatchSubtype):
        pass

    matches = [
        get_match(match_class=MatchSubtypeA, package="a", path="a"),
        get_match(match_class=MatchSubtypeB, package="b"),
        get_match(match_class=MatchSubtypeA, package="a", path="b"),
    ]
    match1, match2, match3 = matches
    MatchSubtypeA.matches = [match1, match3]

    MatchSubtypeB.matches = [match2]

    find_in_dir.return_value = matches

    raincoat = Raincoat()

    # Asserts are made in the check_package method
    list(raincoat.raincoat("."))
