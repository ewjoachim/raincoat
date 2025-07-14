from __future__ import annotations

import functools
import importlib
import importlib.metadata
import inspect
import logging
import pathlib
from collections.abc import Awaitable
from typing import Any, Callable, Literal, Self

import pydantic

from . import exceptions, toml, types

logger = logging.getLogger(__name__)


class Config(pydantic.BaseModel):
    checks: dict[str, ConfigCheck]


@functools.cache
def get_entry_points_for_namespace(
    namespace: str,
) -> dict[str, importlib.metadata.EntryPoint]:
    entry_points = importlib.metadata.entry_points(group=namespace)
    return {ep.name: ep for ep in entry_points}


def len_1(value: dict[str, Any]) -> dict[str, Any]:
    """Validator to ensure the dictionary has exactly one key."""
    if len(value) != 1:
        raise ValueError("Dictionary must have exactly one key")
    return value


class ConfigCheck(pydantic.BaseModel):
    version: str
    source: dict[str, dict[str, Any]]
    diff: dict[str, dict[str, Any]] | None = None
    updater: dict[str, dict[str, Any]] | None = None

    @pydantic.field_validator("source", mode="after")
    @classmethod
    def len_1_source(cls, value):
        return len_1(value)

    @pydantic.field_validator("diff", mode="after")
    @classmethod
    def len_1_diff(cls, value):
        if value is None:
            return value
        return len_1(value)

    @pydantic.field_validator("updater", mode="after")
    @classmethod
    def len_1_updater(cls, value):
        if value is None:
            return value
        return len_1(value)

    @pydantic.model_validator(mode="after")
    def check_entry_points_and_signatures(self) -> Self:
        check_entry_point_and_signature(
            plugin=self.source, plugin_type="source", extra_config={"version": ""}
        )
        if self.diff:
            check_entry_point_and_signature(
                plugin=self.diff,
                plugin_type="diff",
                extra_config={"ref": "", "new": ""},
            )
        if self.updater:
            check_entry_point_and_signature(
                plugin=self.updater,
                plugin_type="updater",
                extra_config=self.source["config"],
            )
        return self

    model_config = pydantic.ConfigDict(strict=True, extra="forbid")


@functools.cache
def get_entry_point_function(
    plugin_type: Literal["source", "diff", "updater"],
    entry_point_name: str,
) -> Callable[..., Awaitable[Any]]:
    entry_points = get_entry_points_for_namespace(f"raincoat.{plugin_type}")
    try:
        entry_point = entry_points[entry_point_name]
    except KeyError:
        raise ValueError(f"Unknown source entry point: {entry_point_name}")

    function = entry_point.load()
    if not inspect.iscoroutinefunction(function):
        raise ValueError(
            f"The source plugin '{entry_point_name}' must be a coroutine function (async def)"
        )
    return function


def check_entry_point_and_signature(
    *,
    plugin: dict[str, dict[str, Any]],
    plugin_type: Literal["source", "diff", "updater"],
    extra_config: dict[str, Any],
) -> None:
    entry_point_name, config = next(iter(plugin.items()))

    function = get_entry_point_function(plugin_type, entry_point_name)

    # Get the function signature
    signature = inspect.signature(function)

    # Prepare arguments for binding

    plugin_config = {**config, **extra_config}

    try:
        # Bind arguments to the function signature
        signature.bind(**plugin_config)
    except TypeError as exc:
        raise ValueError(f"{plugin_type} plugin invalid signature") from exc


def is_pyproject(path) -> bool:
    return path.name == "pyproject.toml"


def get_check_from_config(name: str, config: ConfigCheck) -> types.Check:
    source_name, source_config = next(iter(config.source.items()))
    source = types.Plugin(
        name=source_name,
        config=source_config,
        function=get_entry_point_function("source", source_name),  # type: ignore
    )

    diff = None
    if config.diff:
        diff_name, diff_config = next(iter(config.diff.items()))
        diff = types.Plugin(
            name=diff_name,
            config=diff_config,
            function=get_entry_point_function("diff", diff_name),  # type: ignore
        )

    updater = None
    if config.updater:
        updater_name, updater_config = next(iter(config.updater.items()))

        updater = types.Plugin(
            name=updater_name,
            config=updater_config,
            function=get_entry_point_function("updater", updater_name),  # type: ignore
        )

    return types.Check(
        name=name, version=config.version, source=source, diff=diff, updater=updater
    )


def load_from_toml_file(config_path: pathlib.Path) -> types.Settings:
    raw_data = data = toml.read_toml(config_path)
    if is_pyproject(config_path):
        data = data.get("tool", {}).get("raincoat", {})

    try:
        config = Config.model_validate(data)
    except pydantic.ValidationError as exc:
        raise exceptions.RaincoatConfigFormatError(
            error=f"Invalid configuration format: {exc}"
        ) from exc

    return types.Settings(
        path=config_path,
        payload=raw_data,
        checks={
            name: get_check_from_config(name=name, config=config)
            for name, config in config.checks.items()
        },
    )


def update_versions(settings: types.Settings, updates: dict[str, str]) -> None:
    """
    Update version numbers in the TOML file.

    Parameters
    ----------
    settings : types.Settings
    updates : dict[str, str]
        Dictionary mapping check names to their new versions
    """

    raw_data = data = settings.payload
    if is_pyproject(settings.path):
        data = data.get("tool", {}).get("raincoat", {})

    # Update versions
    for check_name in updates.keys() & settings.checks.keys():
        data["checks"][check_name]["version"] = updates[check_name]

    # Write back to file
    toml.write_toml(settings.path, raw_data)
