"""Functions for reading and writing TOML files while preserving formatting and comments."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import tomlkit
import tomlkit.exceptions

from raincoat import exceptions, types


def loads(text: str) -> types.TomlContainer:
    try:
        return types.TomlContainer(container=tomlkit.loads(text))
    except tomlkit.exceptions.TOMLKitError as e:
        raise exceptions.TomlParseError(error=str(e)) from e


def dumps(data: types.TomlContainer) -> str:
    return tomlkit.dumps(data.container)


# Useful for tests mainly
def create_from_dict(value) -> types.TomlContainer:
    return loads(tomlkit.dumps(value))


def update_toml(
    # type is "Toml somthing", but no idea why. Type checker would be angry anyway
    toml_value: Any,
    updates: list[types.UpdateInstructions],
) -> Generator[types.UpdateResultIntermediary]:
    for result in updates:
        name = result.name
        if name in toml_value:
            result_int = types.UpdateResultIntermediary(name=name)
            if (
                result.set_new_version is not None
                and toml_value[name]["version"] != result.set_new_version
            ):
                toml_value[name]["version"] = result.set_new_version
                result_int.new_version = result.set_new_version

            if result.fix and "old_version" in toml_value[name]:
                toml_value[name].pop("old_version", None)
                result_int.fixed = True
                result_int.new_version = toml_value[name]["version"]

            elif result.set_old_version and "old_version" not in toml_value[name]:
                toml_value[name].add("old_version", result.set_old_version)
                toml_value[name]["old_version"].comment(
                    "Remove this line when the diff has been checked"
                )
                result_int.new_version = toml_value[name]["version"]
                result_int.old_version = result.set_old_version

            yield result_int
