from __future__ import annotations

import pytest

from raincoat import exceptions, toml, types


def test_loads():
    result = toml.loads("""
[x]
a = 1
""")
    assert result == toml.create_from_dict({"x": {"a": 1}})


def test_loads__error():
    with pytest.raises(exceptions.TomlParseError):
        toml.loads("[")


def test_dumps():
    result = toml.dumps(toml.create_from_dict({"x": {"a": 1}}))
    expected = """[x]
a = 1
"""
    assert result == expected


def test_update_toml():
    value = toml.loads("""
[sing_in_the_rain]
version = "13.6.5"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[dance_with_umbrella]
version = "14.5.7"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
""")

    result = list(
        toml.update_toml(
            toml_value=value.container,
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
    assert list(result) == [
        types.UpdateResultIntermediary(
            name="sing_in_the_rain",
            new_version="14.6.8",
        ),
        types.UpdateResultIntermediary(
            name="dance_with_umbrella",
            old_version="14.5.7",
            new_version="17.11.4",
        ),
    ]

    written_file = toml.dumps(value)
    expected = """
[sing_in_the_rain]
version = "14.6.8"
source.pypi.package = "sing"
source.pypi.path = "sing/__init__.py"
diff.python.element = "do_sing"

[dance_with_umbrella]
version = "17.11.4"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
old_version = "14.5.7" # Remove this line when the diff has been checked
"""
    assert written_file == expected


def test_update_toml__fix():
    value = toml.loads("""
[dance_with_umbrella]
version = "17.11.4"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
old_version = "14.5.7" # Remove this line when the diff has been checked
""")

    result = toml.update_toml(
        toml_value=value.container,
        updates=[
            types.UpdateInstructions(name="dance_with_umbrella", fix=True),
        ],
    )

    assert list(result) == [
        types.UpdateResultIntermediary(
            name="dance_with_umbrella", fixed=True, new_version="17.11.4"
        ),
    ]

    written_file = toml.dumps(value)
    expected = """
[dance_with_umbrella]
version = "17.11.4"
source.pypi.package = "umbrella"
source.pypi.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
"""
    assert written_file == expected
