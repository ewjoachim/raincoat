from __future__ import annotations

import dataclasses
import sys
from typing import Any

if sys.version_info < (3, 11):
    import tomli as toml
else:
    import tomllib as toml

import pathlib


def read_toml(file_path: pathlib.Path) -> dict[str, Any]:
    return toml.loads(file_path.read_text())

@dataclasses.dataclass
class Settings:

@dataclasses.dataclass
class Settings:

    @classmethod
    def from_pyproject(cls, config_path: pathlib.Path, is_pyproject: bool) -> Settings:
        data = read_toml(pyproject_path)
        if is_pyproject:
            data = data.get("tool", {}).get("raincoat", {})


        return cls(**data)
