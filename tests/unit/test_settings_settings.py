from __future__ import annotations

import pathlib
from typing import Any

import pytest

import raincoat.updater
from raincoat import exceptions, toml, types
from raincoat.plugins import diff, source, updater
from raincoat.settings import models
from raincoat.settings import settings as settings_module


@pytest.mark.parametrize(
    "input, expected",
    [
        (pathlib.PurePath("foo"), False),
        (pathlib.PurePath("pyproject.toml"), True),
    ],
)
def test_is_pyproject(input, expected):
    assert settings_module.is_pyproject(input) is expected


def test_get_check_from_config():
    result = settings_module.get_check_from_config(
        name="foo",
        path=pathlib.Path("foo"),
        config=models.ConfigCheck(
            version="0.0",
            location="/path",
            source={"pypi": {"package": "bar", "path": "baz"}},
            diff={"python": {"element": "qux"}},
            updater={"venv": {}},
            update_if_no_diff=False,
        ),
    )

    # Type checker complains because of contravariance.
    assert result == types.Check(
        name="foo",
        version="0.0",
        source=types.Plugin(
            name="pypi",
            config={"package": "bar", "path": "baz"},
            function=source.pypi,  # type: ignore
        ),
        diff=types.Plugin(
            name="python",
            config={"element": "qux"},
            function=diff.python,  # type: ignore
        ),
        updater=types.UpdaterPlugin(name="venv", config={}, function=updater.venv),
        update_if_no_diff=False,
        path=pathlib.Path("foo"),
        location="/path",
    )


def test_get_check_from_config__minimal():
    result = settings_module.get_check_from_config(
        name="foo",
        path=pathlib.Path("foo"),
        config=models.ConfigCheck(
            version="0.0",
            source={"pypi": {"package": "bar", "path": "baz"}},
        ),
    )

    # Type checker complains because of contravariance.
    assert result == types.Check(
        name="foo",
        version="0.0",
        source=types.Plugin(
            name="pypi",
            config={"package": "bar", "path": "baz"},
            function=source.pypi,  # type: ignore
        ),
        path=pathlib.Path("foo"),
    )


def test_load_from_toml_file_and_comments(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.foo = {}
# ---""")

    pathlib.Path("bar.py").write_text("""
# --- raincoat
# [ignored]
# version = "3.14"
# source.pypi.package = "ignored"
# source.pypi.path = "imnotthere/__init__.py"
# diff.python.element = "forgetme"
# updater.venv = {}
# ---""")

    config = pathlib.Path("raincoat.toml")
    config.write_text("""
[checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"
""")

    updater_function: Any = raincoat.updater.external(lambda package, path: "3.3")
    result = settings_module.load_from_toml_file_and_comments(
        config_path=config,
        files=[pathlib.Path("foo.py")],
        additional_plugins={"updater": {"foo": updater_function}},
    )

    assert result == types.Settings(
        config_file=types.ConfigFile(
            path=config,
            raw_content=toml.create_from_dict(
                {
                    "checks": {
                        "sing_in_the_rain": {
                            "version": "13.6.5",
                            "source": {
                                "pypi": {"package": "sing", "path": "sing/__init__.py"}
                            },
                            "diff": {"python": {"element": "do_sing"}},
                        }
                    }
                }
            ),
        ),
        checks={
            "sing_in_the_rain": types.Check(
                name="sing_in_the_rain",
                version="13.6.5",
                source=types.Plugin(
                    name="pypi",
                    config={"package": "sing", "path": "sing/__init__.py"},
                    function=source.pypi,  # type: ignore
                ),
                diff=types.Plugin(
                    name="python",
                    config={"element": "do_sing"},
                    function=diff.python,  # type: ignore
                ),
                updater=None,
                path=config,
            ),
            "dance_with_umbrella": types.Check(
                name="dance_with_umbrella",
                version="14.5.7",
                source=types.Plugin(
                    name="pypi",
                    config={"package": "umbrella", "path": "umbrella/__init__.py"},
                    function=source.pypi,  # type: ignore
                ),
                diff=types.Plugin(
                    name="python",
                    config={"element": "use_umbrella"},
                    function=diff.python,  # type: ignore
                ),
                updater=types.UpdaterPlugin(
                    name="foo",
                    config={},
                    function=updater_function,
                    external=True,
                ),
                path=pathlib.Path("foo.py"),
                location="foo.py:2",
            ),
        },
        inline_comments={
            "dance_with_umbrella": types.InlineComment(
                path=pathlib.Path("foo.py"),
                payload=toml.create_from_dict(
                    {
                        "dance_with_umbrella": {
                            "version": "14.5.7",
                            "source": {
                                "pypi": {
                                    "package": "umbrella",
                                    "path": "umbrella/__init__.py",
                                }
                            },
                            "diff": {"python": {"element": "use_umbrella"}},
                            "updater": {"foo": {}},
                        }
                    },
                ),
                raw_content=types.RawComment(
                    start_line=2,
                    end_line=9,
                    text="""# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.foo = {}
# ---""",
                    prefix="# ",
                ),
            ),
        },
    )


def test_load_from_toml_file_and_comments__pyproject(tmp_cwd):
    config = pathlib.Path("pyproject.toml")
    config.write_text("""
[tool.raincoat.checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"
""")
    settings = settings_module.load_from_toml_file_and_comments(config_path=config)

    assert "sing_in_the_rain" in settings.checks


def test_load_from_toml_file_and_comments__config_error(tmp_cwd):
    config = pathlib.Path("raincoat.toml")
    config.write_text("""[checks.sing_in_the_rain]""")

    with pytest.raises(exceptions.ConfigFormatError):
        settings_module.load_from_toml_file_and_comments(config_path=config)


def test_load_from_toml_file_and_comments__inline_config_error(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# ---""")
    with pytest.raises(exceptions.InlineConfigFormatError):
        settings_module.load_from_toml_file_and_comments(config_path=None)


def test_load_from_toml_file_and_comments__inline_config_duplicate(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# version = "13.6.5"
# source.pypi.package = "sing"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---
# --- raincoat
# [dance_with_umbrella]
# version = "13.6.6"
# source.pypi.package = "foo"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---
# """)
    with pytest.raises(
        exceptions.DuplicateCommentError, match='''for check "dance_with_umbrella"'''
    ) as exc_info:
        settings_module.load_from_toml_file_and_comments(config_path=None)
    assert "foo.py:2" in str(exc_info.value)
    assert "foo.py:9" in str(exc_info.value)


def test_load_from_toml_file_and_comments__config_duplicate(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [sing_in_the_rain]
# version = "13.6.5"
# source.pypi.package = "sing"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---""")

    config = pathlib.Path("raincoat.toml")
    config.write_text("""
[checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"
""")

    with pytest.raises(
        exceptions.DuplicateCommentError, match='''for check "sing_in_the_rain"'''
    ) as exc_info:
        settings_module.load_from_toml_file_and_comments(config_path=config)
    assert "raincoat.toml" in str(exc_info.value)
    assert "foo.py:2" in str(exc_info.value)


def test_update_config_file(tmp_cwd):
    config = pathlib.Path("raincoat.toml")
    config.write_text("""
[checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[checks.dance_with_umbrella]
version = "14.5.7"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=config)
    assert settings.config_file
    result = settings_module.update_config_file(
        config_file=settings.config_file,
        updates=[
            types.UpdateInstructions(
                name="sing_in_the_rain",
                set_new_version="14.6.8",
            ),
            types.UpdateInstructions(
                name="dance_with_umbrella",
                set_new_version="17.11.4",
                set_old_version="14.5.7",
            ),
        ],
    )

    assert list(result) == [
        types.UpdateResult(
            name="sing_in_the_rain",
            path=config,
            new_version="14.6.8",
        ),
        types.UpdateResult(
            name="dance_with_umbrella",
            path=config,
            old_version="14.5.7",
            new_version="17.11.4",
        ),
    ]

    expected = """
[checks.sing_in_the_rain]
version = "14.6.8"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[checks.dance_with_umbrella]
version = "17.11.4"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
old_version = "14.5.7" # Remove this line when the diff has been checked
"""
    assert config.read_text() == expected


def test_update_config_file__pyproject(tmp_cwd):
    config = pathlib.Path("pyproject.toml")
    config.write_text("""
[project]
name = "foo"

[tool.raincoat.checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[tool.raincoat.checks.dance_with_umbrella]
version = "14.5.7"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=config)
    assert settings.config_file
    list(
        settings_module.update_config_file(
            config_file=settings.config_file,
            updates=[
                types.UpdateInstructions(
                    name="sing_in_the_rain",
                    set_new_version="14.6.8",
                ),
                types.UpdateInstructions(
                    name="dance_with_umbrella",
                    set_old_version="14.5.7",
                    set_new_version="17.11.4",
                ),
            ],
        )
    )

    expected = """
[project]
name = "foo"

[tool.raincoat.checks.sing_in_the_rain]
version = "14.6.8"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[tool.raincoat.checks.dance_with_umbrella]
version = "17.11.4"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
old_version = "14.5.7" # Remove this line when the diff has been checked
"""
    assert config.read_text() == expected


def test_update_inline_comments(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [sing_in_the_rain]
# version = "13.6.5"
# source.pypi.package = "sing"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---

class X:
    pass

# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# ---
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=None)

    result = settings_module.update_inline_comments(
        inline_comments=settings.inline_comments,
        updates=[
            types.UpdateInstructions(
                name="sing_in_the_rain",
                set_new_version="14.6.8",
            ),
            types.UpdateInstructions(
                name="dance_with_umbrella",
                set_new_version="17.11.4",
                set_old_version="14.5.7",
            ),
            types.UpdateInstructions(
                name="other",
                set_new_version="3.14",
            ),
        ],
    )

    assert list(result) == [
        types.UpdateResult(
            name="sing_in_the_rain",
            path=pathlib.Path("foo.py"),
            new_version="14.6.8",
        ),
        types.UpdateResult(
            name="dance_with_umbrella",
            path=pathlib.Path("foo.py"),
            old_version="14.5.7",
            new_version="17.11.4",
        ),
    ]

    expected = """
# --- raincoat
# [sing_in_the_rain]
# version = "14.6.8"
# source.pypi.package = "sing"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---

class X:
    pass

# --- raincoat
# [dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# old_version = "14.5.7" # Remove this line when the diff has been checked
# ---
"""
    assert pathlib.Path("foo.py").read_text() == expected


def test_update_inline_comments__file_modified_concurrently(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [sing_in_the_rain]
# version = "13.6.5"
# source.pypi.package = "sing"
# source.pypi.path = "sing/__init__.py"
# diff.python.element = "do_sing"
# ---
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=None)

    pathlib.Path("foo.py").write_text("")
    with pytest.raises(exceptions.ConfigNotFoundInPath):
        list(
            settings_module.update_inline_comments(
                inline_comments=settings.inline_comments,
                updates=[
                    types.UpdateInstructions(
                        name="sing_in_the_rain", set_new_version="14.6.8"
                    )
                ],
            )
        )


def test_update(tmp_cwd):
    config = pathlib.Path("raincoat.toml")
    config.write_text("""
[checks.sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"
""")

    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# ---
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=config)
    assert settings.config_file
    settings_module.update(
        settings=settings,
        update_instructions=[
            types.UpdateInstructions(
                name="sing_in_the_rain",
                set_new_version="14.6.8",
            ),
            types.UpdateInstructions(
                name="dance_with_umbrella",
                set_new_version="17.11.4",
                set_old_version="14.5.7",
            ),
        ],
    )

    expected_config = """
[checks.sing_in_the_rain]
version = "14.6.8"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"
"""
    assert config.read_text() == expected_config

    expected_inline = """
# --- raincoat
# [dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# old_version = "14.5.7" # Remove this line when the diff has been checked
# ---
"""
    assert pathlib.Path("foo.py").read_text() == expected_inline


def test_update__no_config(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# ---
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=None)

    settings_module.update(
        settings=settings,
        update_instructions=[
            types.UpdateInstructions(
                name="dance_with_umbrella",
                set_new_version="17.11.4",
                set_old_version="14.5.7",
            ),
        ],
    )

    expected_inline = """
# --- raincoat
# [dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# old_version = "14.5.7" # Remove this line when the diff has been checked
# ---
"""
    assert pathlib.Path("foo.py").read_text() == expected_inline


def test_update__fix(tmp_cwd):
    pathlib.Path("foo.py").write_text("""
# --- raincoat
# [dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# old_version = "14.5.7" # Remove this line when the diff has been checked
# ---
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=None)

    result = settings_module.update(
        settings=settings,
        update_instructions=[
            types.UpdateInstructions(name="dance_with_umbrella", fix=True)
        ],
    )

    assert list(result) == [
        types.UpdateResult(
            name="dance_with_umbrella",
            path=pathlib.Path("foo.py"),
            fixed=True,
            new_version="17.11.4",
        ),
    ]

    expected_inline = """
# --- raincoat
# [dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# ---
"""
    assert pathlib.Path("foo.py").read_text() == expected_inline


def test_update__missing(tmp_cwd):
    pathlib.Path("raincoat.toml").write_text(""")
# [checks.dance_with_umbrella]
# version = "17.11.4"
# source.pypi.package = "umbrella"
# source.pypi.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
""")

    settings = settings_module.load_from_toml_file_and_comments(config_path=None)
    with pytest.raises(exceptions.ConfigNotFound):
        settings_module.update(
            settings=settings,
            update_instructions=[
                types.UpdateInstructions(name="some_other_test", fix=True)
            ],
        )
