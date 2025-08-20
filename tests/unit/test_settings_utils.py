from __future__ import annotations

import importlib.metadata
import uuid

import pytest

from raincoat import exceptions
from raincoat.plugins import diff
from raincoat.settings import utils


def test_get_entry_points_for_namespace():
    result = utils.get_entry_points_for_namespace("raincoat.diff")

    assert result["default"] == importlib.metadata.EntryPoint(
        name="default", value="raincoat.plugins.diff:default", group="raincoat.diff"
    )


def test_get_entry_point_function():
    result = utils.get_entry_point_function(
        plugin_type="diff", entry_point_name="default"
    )

    assert result is diff.default


def test_get_entry_point_function__unknown_entrypoint():
    with pytest.raises(exceptions.PluginNotFound):
        utils.get_entry_point_function(
            plugin_type="diff", entry_point_name=str(uuid.uuid4())
        )


def test_check_entry_point_and_signature():
    utils.check_entry_point_and_signature(
        plugin={"default": {}},
        plugin_type="diff",
        extra_config={"ref": "", "new": ""},
    )


def test_check_entry_point_and_signature__extra_config_overlap():
    utils.check_entry_point_and_signature(
        plugin={"default": {"ref": ""}},
        plugin_type="diff",
        extra_config={"ref": "", "new": ""},
    )


def test_check_entry_point_and_signature__invalid_signature():
    with pytest.raises(exceptions.InvalidPluginConfiguration):
        utils.check_entry_point_and_signature(
            plugin={"default": {"foo": ""}},
            plugin_type="diff",
            extra_config={"ref": "", "new": ""},
        )
