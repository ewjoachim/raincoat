"""Functions for reading and writing TOML files while preserving formatting and comments."""

from __future__ import annotations

import contextlib
import copy
import pathlib
from collections.abc import Generator
from typing import Any

import tomlkit


def read_toml(file_path: pathlib.Path) -> dict[str, Any]:
    return tomlkit.loads(file_path.read_text())


def write_toml(file_path: pathlib.Path, data: dict[str, Any]) -> None:
    file_path.write_text(tomlkit.dumps(data))
