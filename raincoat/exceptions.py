from __future__ import annotations


class RaincoatException(Exception):
    """
    Unexpected raincoat error.
    """

    def __init__(self, message=None):
        if not message:
            message = self.__doc__
        super().__init__(message)


class NotMatching(Exception):
    """
    Raincoat comment match was almost found but the format is slightly wrong.
    """
