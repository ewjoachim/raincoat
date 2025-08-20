from __future__ import annotations

from typing import Any, Self

import pydantic

from raincoat import exceptions

from . import utils


class Config(pydantic.BaseModel):
    checks: dict[str, ConfigCheck]
    exclude: list[str] | None = None


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
    update_if_no_diff: bool = True
    old_version: str | None = None
    location: str | None = None

    @pydantic.field_validator("source", mode="after")
    @classmethod
    def len_1_source(cls, value):
        return len_1(value)

    @pydantic.field_validator("diff", mode="after")
    @classmethod
    def len_1_diff(cls, value):
        return len_1(value)

    @pydantic.field_validator("updater", mode="after")
    @classmethod
    def len_1_updater(cls, value):
        return len_1(value)

    @pydantic.model_validator(mode="after")
    def check_entry_points_and_signatures(self, info: pydantic.ValidationInfo) -> Self:
        try:
            utils.check_entry_point_and_signature(
                plugin=self.source,
                plugin_type="source",
                extra_config={"version": ""},
                additional_plugins=(info.context or {}).get("additional_plugins"),
            )

            if self.diff:
                utils.check_entry_point_and_signature(
                    plugin=self.diff,
                    plugin_type="diff",
                    extra_config={"ref": "", "new": ""},
                    additional_plugins=(info.context or {}).get("additional_plugins"),
                )
            if self.updater:
                utils.check_entry_point_and_signature(
                    plugin=self.updater,
                    plugin_type="updater",
                    extra_config=self.source[next(iter(self.source))],
                    additional_plugins=(info.context or {}).get("additional_plugins"),
                )
        except (
            exceptions.PluginNotFound,
            exceptions.InvalidPluginConfiguration,
        ) as exc:
            raise ValueError(str(exc)) from exc
        return self

    model_config = pydantic.ConfigDict(strict=True, extra="forbid")
