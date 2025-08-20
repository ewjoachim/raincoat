from __future__ import annotations

import functools
import importlib
import importlib.metadata
import inspect
from typing import Any, Callable

from raincoat import exceptions, types


@functools.cache
def get_entry_points_for_namespace(
    namespace: str,
) -> dict[str, importlib.metadata.EntryPoint]:
    entry_points = importlib.metadata.entry_points(group=namespace)
    return {ep.name: ep for ep in entry_points}


def get_entry_point_function(
    plugin_type: types.PluginType,
    entry_point_name: str,
    additional_plugins: types.AdditionalPlugins | None = None,
) -> Callable:
    entry_points = get_entry_points_for_namespace(f"raincoat.{plugin_type}")
    try:
        entry_point = entry_points[entry_point_name]
    except KeyError:
        try:
            return (additional_plugins or {})[plugin_type][entry_point_name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            raise exceptions.PluginNotFound(
                type=plugin_type.capitalize(), name=entry_point_name
            )

    return entry_point.load()


def check_entry_point_and_signature(
    *,
    plugin: dict[str, dict[str, Any]],
    plugin_type: types.PluginType,
    extra_config: dict[str, Any],
    additional_plugins: types.AdditionalPlugins | None = None,
) -> None:
    entry_point_name, config = next(iter(plugin.items()))

    function = get_entry_point_function(
        plugin_type=plugin_type,
        entry_point_name=entry_point_name,
        additional_plugins=additional_plugins,
    )

    # Get the function signature
    signature = inspect.signature(function)

    # Prepare arguments for binding

    plugin_config = {**config, **extra_config}

    try:
        # Bind arguments to the function signature
        signature.bind(**plugin_config)
    except TypeError as exc:
        raise exceptions.InvalidPluginConfiguration(
            type=plugin_type.capitalize(), name=entry_point_name, error=exc
        ) from exc
