from __future__ import annotations

import dataclasses
import functools
from typing import Callable, Generic, ParamSpec, TypeVar

from . import types

P = ParamSpec("P")
T = TypeVar("T", bound=types.UpdaterFunction)


@dataclasses.dataclass
class Updater(types.Updater, Generic[P]):
    """A class representing an updater with an optional external flag."""

    function: Callable[P, str]
    external: bool = False

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> str:
        """Call the updater function with the provided configuration."""
        return self.function(*args, **kwargs)


def external(function: Callable[P, str]) -> Callable[P, str]:
    """Decorator to mark an updater as external, preserving signature and docstring."""
    updater = Updater(function=function, external=True)
    return functools.wraps(function)(updater)
