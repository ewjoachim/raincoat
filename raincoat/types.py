from __future__ import annotations

import dataclasses
import enum
import pathlib
from collections.abc import Callable
from typing import Any, Generic, Literal, Protocol, TypeAlias, TypedDict, TypeVar

import tomlkit
import tomlkit.items

SourceFunction: TypeAlias = Callable[..., str]
DiffFunction: TypeAlias = Callable[..., str | None]
UpdaterFunction: TypeAlias = Callable[..., str]


T = TypeVar("T")


@dataclasses.dataclass
class Plugin(Generic[T]):
    name: str
    config: dict[str, Any]
    function: Callable[..., T]


PluginType: TypeAlias = Literal["source", "diff", "updater"]


class AdditionalPlugins(TypedDict, total=False):
    source: dict[str, Callable[..., str]]
    diff: dict[str, Callable[..., str | None]]
    updater: dict[str, Callable[..., str]]


@dataclasses.dataclass
class Check:
    name: str
    version: str
    path: pathlib.Path
    source: Plugin[str]
    diff: Plugin[str | None] | None = None
    updater: str | None = None
    update_if_no_diff: bool = True
    old_version: str | None = None
    location: str | None = None


@dataclasses.dataclass
class Settings:
    checks: dict[str, Check]
    config_file: ConfigFile | None
    inline_comments: dict[str, InlineComment]
    exclude: list[str] | None = None


@dataclasses.dataclass
class ConfigFile:
    path: pathlib.Path
    raw_content: TomlContainer


@dataclasses.dataclass
class RawComment:
    start_line: int
    end_line: int
    text: str
    prefix: str


@dataclasses.dataclass
class InlineComment:
    path: pathlib.Path
    payload: TomlContainer
    raw_content: RawComment


@dataclasses.dataclass
class TomlContainer:
    container: tomlkit.TOMLDocument | tomlkit.items.Table

    def as_dict(self) -> dict[str, Any]:
        return self.container.unwrap()


@dataclasses.dataclass
class ManualUpdate:
    name: str
    version: str | None


class SkippedReason(enum.StrEnum):
    NO_UPDATER = "no updater"
    EXTERNAL_UPDATER = "external updater"


@dataclasses.dataclass
class CheckError:
    error: str
    plugin_type: PluginType | Literal["other"] = "other"


@dataclasses.dataclass
class CheckResult:
    check: Check
    new_version: str | None = None
    diff: str | None = None
    error: CheckError | None = None
    skipped: SkippedReason | None = None


@dataclasses.dataclass
class UpdateInstructions:
    name: str
    set_new_version: str | None = None
    set_old_version: str | None = None
    fix: bool = False


@dataclasses.dataclass
class UpdateResultIntermediary:
    name: str
    new_version: str | None = None
    old_version: str | None = None
    fixed: bool = False


@dataclasses.dataclass
class UpdateResult:
    name: str
    path: pathlib.Path
    new_version: str | None = None
    old_version: str | None = None
    fixed: bool = False


class CheckReporter(Protocol):
    def on_check_result(self, check_result: CheckResult, /): ...
    def on_update_result(self, update_result: UpdateResult, /): ...


class FixReporter(Protocol):
    def on_fix(self, update_result: UpdateResult, /): ...
