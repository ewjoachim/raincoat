from __future__ import annotations

from raincoat import toml


def test_toml_container__as_dict():
    assert toml.loads("a = 1").as_dict() == {"a": 1}
