from __future__ import annotations

import io
import pathlib

import pytest

from raincoat import toml, types
from raincoat.settings import inline_comments


@pytest.mark.parametrize(
    "input, expected",
    [
        pytest.param("", [], id="empty"),
        pytest.param("""def x():\n    pass""", [], id=""),
        pytest.param(
            """
a = 1
--- raincoat
b = 2
""",
            [],
            id="unfinished",
        ),
        pytest.param(
            """
a = 1
# --- raincoat
# x = 1
# ---
b = 2
""",
            [
                types.RawComment(
                    start_line=3,
                    end_line=5,
                    text="# --- raincoat\n# x = 1\n# ---\n",
                    prefix="# ",
                )
            ],
            id="comment #",
        ),
        pytest.param(
            """
a = 1
// --- raincoat
// x = 1
// ---
b = 2
""",
            [
                types.RawComment(
                    start_line=3,
                    end_line=5,
                    text="// --- raincoat\n// x = 1\n// ---\n",
                    prefix="// ",
                )
            ],
            id="comment //",
        ),
        pytest.param(
            """
a = 1
-- --- raincoat
-- x = 1
-- ---
b = 2
""",
            [
                types.RawComment(
                    start_line=3,
                    end_line=5,
                    text="-- --- raincoat\n-- x = 1\n-- ---\n",
                    prefix="-- ",
                )
            ],
            id="comment --",
        ),
        pytest.param(
            """
a = 1
/*
--- raincoat
x = 1
---
*/
b = 2
""",
            [
                types.RawComment(
                    start_line=4,
                    end_line=6,
                    text="--- raincoat\nx = 1\n---\n",
                    prefix="",
                )
            ],
            id="comment /* */",
        ),
    ],
)
def test_find_inline_comments(input, expected):
    result = inline_comments.find_inline_comments(io.StringIO(input))

    assert list(result) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            types.RawComment(
                start_line=3,
                end_line=5,
                text="-- --- raincoat\n-- x = 1\n-- ---\n",
                prefix="-- ",
            ),
            {"x": 1},
        ),
        (
            types.RawComment(
                start_line=4,
                end_line=6,
                text="--- raincoat\nx = 1\n---\n",
                prefix="",
            ),
            {"x": 1},
        ),
    ],
)
def test_get_payload_from_inline_comment(input, expected):
    assert inline_comments.get_payload_from_inline_comment(input).container == expected


def test_parse_inline_comments_from_file__binary(tmp_path, caplog):
    path = tmp_path / "bin"
    path.write_bytes(b"\xff\xfe")
    caplog.set_level("DEBUG")
    with path.open("r") as file:
        result = inline_comments.parse_inline_comments_from_file(
            file_obj=file, path=path
        )

        assert list(result) == []

    assert "File is probably a binary" in caplog.text


def test_parse_inline_comments_from_file__empty(caplog):
    caplog.set_level("WARNING")

    result = inline_comments.parse_inline_comments_from_file(
        file_obj=io.StringIO("""
--- raincoat
---
"""),
        path=pathlib.Path("/foo"),
    )

    assert list(result) == []

    assert "Inline comment block in /foo:2 is empty, skipping." in caplog.text


def test_parse_inline_comments_from_file__badly_formatted(caplog):
    caplog.set_level("WARNING")

    result = inline_comments.parse_inline_comments_from_file(
        file_obj=io.StringIO("""
--- raincoat
a =
---
"""),
        path=pathlib.Path("/foo"),
    )

    assert list(result) == []

    assert (
        "Error parsing inline comment block in /foo:2 - Error parsing TOML file"
        in caplog.text
    )


def test_parse_inline_comments_from_file__ok():
    path = pathlib.Path("/foo")
    result = inline_comments.parse_inline_comments_from_file(
        file_obj=io.StringIO("""
--- raincoat
a = 1
---

--- raincoat
b = 2
---"""),
        path=path,
    )
    assert list(result) == [
        types.InlineComment(
            path=path,
            payload=toml.create_from_dict({"a": 1}),
            raw_content=types.RawComment(
                start_line=2,
                end_line=4,
                text="--- raincoat\na = 1\n---\n",
                prefix="",
            ),
        ),
        types.InlineComment(
            path=path,
            payload=toml.create_from_dict({"b": 2}),
            raw_content=types.RawComment(
                start_line=6,
                end_line=8,
                text="--- raincoat\nb = 2\n---",
                prefix="",
            ),
        ),
    ]


@pytest.fixture
def files(tmp_path):
    (tmp_path / "aa" / "bb").mkdir(parents=True)
    (tmp_path / "aa" / "cc").mkdir(parents=True)
    (tmp_path / "aa" / "bb" / "dd").touch()
    (tmp_path / "aa" / "ee").touch()
    (tmp_path / "aa" / "cc" / "ff").touch()

    return tmp_path


def test_filter_files__all_files(files):
    result = inline_comments.filter_files(files, files=None, exclude=None)

    assert list(result) == [
        (files / "aa" / "ee"),
        (files / "aa" / "bb" / "dd"),
        (files / "aa" / "cc" / "ff"),
    ]


def test_filter_files__all_files_exclude(files):
    result = inline_comments.filter_files(files, files=None, exclude=["c*/*"])

    assert list(result) == [
        (files / "aa" / "ee"),
        (files / "aa" / "bb" / "dd"),
    ]


def test_filter_files__select_files(files):
    result = inline_comments.filter_files(
        files, files=[(files / "aa" / "bb" / "dd")], exclude=None
    )

    assert list(result) == [
        (files / "aa" / "bb" / "dd"),
    ]


def test_filter_files__select_files_exclude(files):
    result = inline_comments.filter_files(
        files,
        files=[(files / "aa" / "bb" / "dd"), (files / "aa" / "cc" / "ff")],
        exclude=["c*/*"],
    )

    assert list(result) == [
        (files / "aa" / "bb" / "dd"),
    ]


def test_parse_inline_comments_from_files(tmp_path):
    (tmp_path / "aa" / "bb").mkdir(parents=True)
    path = tmp_path / "aa" / "bb" / "cc"
    path.write_text("""
a
--- raincoat
a = 1
---
yay
""")

    result = inline_comments.parse_inline_comments_from_files(root_dir=tmp_path)

    assert list(result) == [
        types.InlineComment(
            path=path,
            payload=toml.create_from_dict({"a": 1}),
            raw_content=types.RawComment(
                start_line=3,
                end_line=5,
                text="--- raincoat\na = 1\n---\n",
                prefix="",
            ),
        ),
    ]


def test_parse_inline_comments_from_files__error(tmp_path, caplog):
    path = tmp_path / "non-existant"
    path.symlink_to(tmp_path / "target")

    caplog.set_level("ERROR")
    result = inline_comments.parse_inline_comments_from_files(root_dir=tmp_path)

    assert list(result) == []

    assert (
        f"Error parsing inline comments in {path}: [Errno 2] No such file or directory"
        in caplog.text
    )
