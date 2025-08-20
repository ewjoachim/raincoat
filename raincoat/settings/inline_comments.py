from __future__ import annotations

import logging
import pathlib
import re
from collections.abc import Iterator
from typing import TextIO

from raincoat import toml, types

logger = logging.getLogger(__name__)

INLINE_COMMENT_START = re.compile(r"^(?P<prefix>.*)--- raincoat$")
INLINE_COMMENT_END = re.compile(r"^(?P<prefix>.*)---$")


def find_inline_comments(file: TextIO) -> Iterator[types.RawComment]:
    """
    Find all Raincoat inline comment blocks in the given text.
    Yields (start_line, end_line, block_text) for each block.
    """
    comment_code: types.RawComment | None = None

    for lineno, line in enumerate(file, 1):
        if not comment_code:
            if match := INLINE_COMMENT_START.match(line.rstrip()):
                comment_code = types.RawComment(
                    start_line=lineno,
                    end_line=0,
                    text=line,
                    prefix=match.group("prefix") or "",
                )
        else:
            comment_code.text += line
            if (end_match := INLINE_COMMENT_END.match(line)) and (
                end_match.group("prefix") == comment_code.prefix
            ):
                comment_code.end_line = lineno
                yield comment_code
                comment_code = None


def get_payload_from_inline_comment(
    raw_comment: types.RawComment,
) -> types.TomlContainer:
    """
    Extract TOML data from a Raincoat inline comment block.
    """
    toml_text = "\n".join(
        line.removeprefix(raw_comment.prefix)
        for line in raw_comment.text.splitlines()[1:-1]
    )
    return toml.loads(toml_text + "\n")


def parse_inline_comments_from_file(
    # Passing both the path and the file_obj might seem redundant, but the path is only
    # used for logging, and it much more testable if the function revieves text without
    # being tied to specific I/O
    file_obj: TextIO,
    path: pathlib.Path,
) -> Iterator[types.InlineComment]:
    """
    Parse all Raincoat inline comment blocks in the given text and return a list of TOML dicts.
    """
    try:
        for raw_comment in find_inline_comments(file_obj):
            try:
                payload = get_payload_from_inline_comment(raw_comment)
            except toml.exceptions.TomlParseError as e:
                logger.error(
                    f"Error parsing inline comment block in {path}:{raw_comment.start_line} - {e}"
                )
                continue
            if not payload.container:
                logger.warning(
                    f"Inline comment block in {path}:{raw_comment.start_line} is empty, skipping."
                )
                continue

            yield types.InlineComment(
                path=path,
                payload=payload,
                raw_content=raw_comment,
            )
    except UnicodeDecodeError as e:
        logger.debug(f"Error reading file {path}: {e}. File is probably a binary.")


def filter_files(
    root_dir: pathlib.Path,
    *,
    files: list[pathlib.Path] | None = None,
    exclude: list[str] | None = None,
) -> Iterator[pathlib.Path]:
    """
    Filter files in the base path based on include and exclude patterns.
    """
    if files is None:
        for path, dirnames, filenames in root_dir.walk():
            dirnames.sort()
            for filename in sorted(filenames):
                file_path = path / filename
                if exclude and any(file_path.match(e) for e in exclude):
                    continue
                yield file_path
    else:
        for file in files:
            if exclude and any(file.match(e) for e in exclude):
                continue

            yield file


def parse_inline_comments_from_files(
    root_dir: pathlib.Path,
    *,
    files: list[pathlib.Path] | None = None,
    exclude: list[str] | None = None,
) -> Iterator[types.InlineComment]:
    for file in filter_files(root_dir=root_dir, files=files, exclude=exclude):
        try:
            with file.open(encoding="utf-8") as file_obj:
                yield from list(
                    parse_inline_comments_from_file(file_obj=file_obj, path=file)
                )
        except Exception as e:
            # Just a sanity check to avoid breaking the whole process if one file has an
            # error.
            # There's no _specific_ reason why it should happen, but there are plenty of
            # possible unpredictible reasons.
            # Note: not catching BaseExceptions here, ctrl+c should still work.
            logger.error(f"Error parsing inline comments in {file}: {e}")
            continue
