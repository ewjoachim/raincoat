from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Generic, Protocol, TypeVar


class SourceFunction(Protocol):
    async def __call__(self, *, version: str, **config: Any) -> str: ...


class DiffFunction(Protocol):
    async def __call__(self, *, ref: str, new: str, **config: Any) -> str | None: ...


class UpdaterFunction(Protocol):
    async def __call__(self, **config: Any) -> str: ...


T = TypeVar("T", SourceFunction, DiffFunction, UpdaterFunction)


@dataclasses.dataclass
class Plugin(Generic[T]):
    name: str
    config: dict[str, Any]
    function: T


@dataclasses.dataclass
class Check:
    name: str
    version: str
    source: Plugin[SourceFunction]
    diff: Plugin[DiffFunction] | None = None
    updater: Plugin[UpdaterFunction] | None = None


@dataclasses.dataclass
class Settings:
    path: pathlib.Path
    payload: dict[str, Any]
    checks: dict[str, Check] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class UpdateResult:
    check: Check
    new_version: str
    diff: str | None

    @property
    def has_new_version(self) -> bool:
        return self.new_version != self.check.version
