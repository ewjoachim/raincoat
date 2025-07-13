from __future__ import annotations


class RaincoatError(Exception):
    """There was an error in the raincoat library."""

    def __init__(self, message: str = "", **kwargs) -> None:
        message = message or type(self).__doc__ or ""
        message = message.format(**kwargs)

        super().__init__(message)
