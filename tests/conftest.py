from __future__ import annotations

import pathlib
from typing import Protocol

import pytest

from raincoat import settings as settings_module
from raincoat import types


class MakeSettings(Protocol):
    def __call__(
        self, *config: str, additional_plugins: types.AdditionalPlugins | None = None
    ) -> types.Settings: ...


@pytest.fixture
def comment_file(tmp_path) -> pathlib.Path:
    return tmp_path / "foo"


@pytest.fixture
def make_settings(comment_file, tmp_path) -> MakeSettings:
    def f(*config: str, additional_plugins: types.AdditionalPlugins | None = None):
        with comment_file.open("w") as file:
            for c in config:
                file.write(f"""
--- raincoat
{c}
---
""")
        return settings_module.load_from_toml_file_and_comments(
            config_path=None,
            root_dir=tmp_path,
            additional_plugins=additional_plugins,
        )

    return f


@pytest.fixture
def tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
