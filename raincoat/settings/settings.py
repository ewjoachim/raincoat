from __future__ import annotations

import logging
import pathlib
from collections.abc import Generator
from typing import Any

import pydantic

from raincoat import exceptions, toml, types

from . import inline_comments, models, utils

logger = logging.getLogger(__name__)


def is_pyproject(path: pathlib.PurePath) -> bool:
    return path.name == "pyproject.toml"


def get_check_from_config(
    name: str,
    config: models.ConfigCheck,
    path: pathlib.Path,
    additional_plugins: types.AdditionalPlugins | None = None,
    location: str | None = None,
) -> types.Check:
    source_name, source_config = next(iter(config.source.items()))
    check_function: types.UpdaterFunction = utils.get_entry_point_function(
        plugin_type="source",
        entry_point_name=source_name,
        additional_plugins=additional_plugins,
    )
    source: types.Plugin[str] = types.Plugin(
        name=source_name,
        config=source_config,
        function=check_function,
    )

    diff: types.Plugin[str | None] | None = None
    if config.diff:
        diff_name, diff_config = next(iter(config.diff.items()))
        diff_function: types.DiffFunction = utils.get_entry_point_function(
            plugin_type="diff",
            entry_point_name=diff_name,
            additional_plugins=additional_plugins,
        )
        diff = types.Plugin(
            name=diff_name,
            config=diff_config,
            function=diff_function,
        )

    updater: types.UpdaterPlugin | None = None
    if config.updater:
        updater_name, updater_config = next(iter(config.updater.items()))

        updater_function: types.UpdaterFunction = utils.get_entry_point_function(
            plugin_type="updater",
            entry_point_name=updater_name,
            additional_plugins=additional_plugins,
        )
        updater = types.UpdaterPlugin(
            name=updater_name,
            config=updater_config,
            function=updater_function,
            external=getattr(updater_function, "external", False),
        )

    return types.Check(
        name=name,
        version=config.version,
        source=source,
        diff=diff,
        updater=updater,
        update_if_no_diff=config.update_if_no_diff,
        old_version=config.old_version,
        path=path,
        location=config.location or location,
    )


def load_from_toml_file_and_comments(
    *,
    config_path: pathlib.Path | None,
    root_dir: pathlib.Path = pathlib.Path("."),
    files: list[pathlib.Path] | None = None,
    additional_plugins: types.AdditionalPlugins | None = None,
) -> types.Settings:
    checks: dict[str, types.Check] = {}
    config_file = None
    exclude = None

    if config_path:
        raw_data = toml.loads(config_path.read_text(encoding="utf-8"))
        data = raw_data.as_dict()
        if is_pyproject(config_path):
            data = data.get("tool", {}).get("raincoat", {})

        try:
            config = models.Config.model_validate(
                data, context={"additional_plugins": additional_plugins}
            )
        except pydantic.ValidationError as exc:
            raise exceptions.ConfigFormatError(
                error=f"{exc}.\nConfiguration:\n{data}"
            ) from exc

        checks.update(
            {
                name: get_check_from_config(
                    name=name,
                    config=config,
                    path=config_path,
                    additional_plugins=additional_plugins,
                )
                for name, config in config.checks.items()
            }
        )
        config_file = types.ConfigFile(path=config_path, raw_content=raw_data)
        exclude = config.exclude

    found_inline_comments = {}
    for comment in inline_comments.parse_inline_comments_from_files(
        root_dir=root_dir, files=files, exclude=exclude
    ):
        try:
            comment_config = models.Config.model_validate(
                {"checks": comment.payload.as_dict()},
                context={"additional_plugins": additional_plugins},
            )
        except pydantic.ValidationError as exc:
            raise exceptions.InlineConfigFormatError(
                path=comment.path, line=comment.raw_content.start_line, error=exc
            ) from exc

        # Check for duplicates
        for name, config_check in comment_config.checks.items():
            if name in checks:
                if other := found_inline_comments.get(name):
                    other_path = f"{other.path}:{other.raw_content.start_line}"
                else:
                    other_path = f"{config_path}"

                raise exceptions.DuplicateCommentError(
                    name=name,
                    path=comment.path,
                    line=comment.raw_content.start_line,
                    other_path=other_path,
                )

            checks[name] = get_check_from_config(
                name=name,
                config=config_check,
                path=comment.path,
                additional_plugins=additional_plugins,
                location=f"{comment.path}:{comment.raw_content.start_line}",
            )
            found_inline_comments[name] = comment

    return types.Settings(
        config_file=config_file,
        checks=checks,
        inline_comments=found_inline_comments,
        exclude=exclude,
    )


def update_config_file(
    config_file: types.ConfigFile,
    updates: list[types.UpdateInstructions],
) -> Generator[types.UpdateResult]:
    data: Any = config_file.raw_content.container

    if is_pyproject(config_file.path):
        data = data["tool"]["raincoat"]

    for result in toml.update_toml(toml_value=data["checks"], updates=updates):
        yield types.UpdateResult(
            name=result.name,
            path=config_file.path,
            new_version=result.new_version,
            old_version=result.old_version,
            fixed=result.fixed,
        )

    config_file.path.write_text(toml.dumps(config_file.raw_content))


def update_inline_comments(
    inline_comments: dict[str, types.InlineComment],
    updates: list[types.UpdateInstructions],
) -> Generator[types.UpdateResult]:
    files_to_update: dict[pathlib.Path, str] = {}

    for update in updates:
        try:
            comment = inline_comments[update.name]
        except KeyError:
            continue

        if comment.path not in files_to_update:
            files_to_update[comment.path] = comment.path.read_text()

        for result in toml.update_toml(
            toml_value=comment.payload.container, updates=[update]
        ):
            yield types.UpdateResult(
                name=result.name,
                path=comment.path,
                new_version=result.new_version,
                old_version=result.old_version,
                fixed=result.fixed,
            )
        # We could check that the call above produces 1 result, but I really
        # can't see how to write a coverage test for the case it wouldn't.

        new_content = toml.dumps(comment.payload)
        fenced = "\n".join(
            comment.raw_content.prefix + line
            for line in [
                "--- raincoat",
                *new_content.splitlines(),
                "---",
            ]
        )
        file_contents = files_to_update[comment.path]
        if comment.raw_content.text not in file_contents:
            raise exceptions.ConfigNotFoundInPath(name=update.name, path=comment.path)
        files_to_update[comment.path] = file_contents.replace(
            comment.raw_content.text, fenced + "\n"
        )

    for path, content in files_to_update.items():
        path.write_text(content)


def update(
    settings: types.Settings, update_instructions: list[types.UpdateInstructions]
) -> list[types.UpdateResult]:
    """
    Update version numbers in the TOML file.

    Parameters
    ----------
    settings : types.Settings
    updates : dict[str, str]
        Dictionary mapping check names to their new versions
    """
    update_results: list[types.UpdateResult] = []
    if settings.config_file:
        update_results += update_config_file(
            config_file=settings.config_file,
            updates=update_instructions,
        )
    update_results += update_inline_comments(
        inline_comments=settings.inline_comments,
        updates=update_instructions,
    )
    if missing := (
        {e.name for e in update_instructions} - {e.name for e in update_results}
    ):
        raise exceptions.ConfigNotFound(names=", ".join(f'"{e}"' for e in missing))

    return update_results
