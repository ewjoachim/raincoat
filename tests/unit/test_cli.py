from __future__ import annotations

import argparse
import logging
import pathlib
from typing import Any

import pytest

from raincoat import cli, exceptions, types


@pytest.mark.parametrize(
    "verbosity, log_level",
    [
        (0, logging.WARNING),
        (1, logging.INFO),
        (2, logging.DEBUG),
        (3, logging.DEBUG),
    ],
)
def test_get_log_level(verbosity, log_level):
    assert cli.get_log_level(verbosity=verbosity) == log_level


def test_setup_logging(mocker):
    basic_config = mocker.patch("logging.basicConfig")
    cli.setup_logging(verbosity=1)
    basic_config.assert_called_with(level=logging.INFO)


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            ["check"],
            argparse.Namespace(
                verbose=0,
                config=None,
                command="check",
                with_external=False,
                checks=None,
                fail_if_diff=True,
                files=[],
            ),
        ),
        (
            [
                "-vvvv",
                "--config=foo.toml",
                "check",
                "--with-external",
                "--manual",
                "abc=123",
                "--manual",
                "def",
                "--no-fail-if-diff",
                "a",
                "b",
                "c",
            ],
            argparse.Namespace(
                verbose=4,
                config=pathlib.Path("foo.toml"),
                command="check",
                with_external=True,
                checks=[
                    types.ManualUpdate(name="abc", version="123"),
                    types.ManualUpdate(name="def", version=None),
                ],
                fail_if_diff=False,
                files=["a", "b", "c"],
            ),
        ),
        (
            ["fix", "a", "b"],
            argparse.Namespace(
                verbose=0, config=None, command="fix", checks=["a", "b"]
            ),
        ),
    ],
)
def test_get_argument_parser(args, expected):
    assert cli.get_argument_parser().parse_args(args) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("abc=123", types.ManualUpdate(name="abc", version="123")),
        ("def", types.ManualUpdate(name="def", version=None)),
    ],
)
def test_make_manual_updates(value, expected):
    assert cli.make_manual_updates(value) == expected


def test_find_config__manual(tmp_path):
    assert cli.find_config(manual_config=tmp_path) == tmp_path


@pytest.mark.parametrize("name", ["pyproject.toml", "raincoat.toml"])
def test_find_config_pyproject(name, tmp_path, monkeypatch):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    config = tmp_path / "a" / name
    config.touch()
    assert cli.find_config(manual_config=None) == config


def test_find_config_pyproject__cwd(tmp_cwd):
    assert cli.find_config(manual_config=None) is None


@pytest.mark.parametrize(
    "verbosity, expected",
    [
        (0, ""),
        (1, "/bar:\n   foo: message\n"),
    ],
)
def test_cli_reporter__print__verbosity(capsys, verbosity, expected):
    cli.CLIReporter(verbosity=verbosity).print(
        "message", path=pathlib.Path("/bar"), check_name="foo", verbosity=1
    )
    assert capsys.readouterr().out == expected


def test_cli_reporter__print(capsys):
    reporter = cli.CLIReporter(verbosity=1)

    reporter.print("message", verbosity=1, path=pathlib.Path("/bar"), check_name="a")
    reporter.print("second", verbosity=3, path=pathlib.Path("/bar"), check_name="b")
    reporter.print("third", verbosity=0, path=pathlib.Path("/bar"), check_name="c")
    reporter.print("fourth", verbosity=1, path=pathlib.Path("/foo"), check_name="d")
    expected = """/bar:
   a: message
   c: third
/foo:
   d: fourth
"""
    assert capsys.readouterr().out == expected


@pytest.fixture
def check() -> types.Check:
    return types.Check(
        name="dance_with_umbrella",
        version="1",
        path=pathlib.Path("foo"),
        source=types.Plugin(name="foo", config={}, function=lambda version: ""),
    )


def test_cli_reporter__on_check_result__plugin_error(check, capsys):
    reporter = cli.CLIReporter()
    reporter.on_check_result(
        types.CheckResult(
            check=check,
            error=types.CheckError(error="Boom", plugin_type="diff"),
        )
    )
    expected = "foo:\n   dance_with_umbrella: Error in diff plugin (for traceback, use -vv): Boom\n"
    assert capsys.readouterr().out == expected
    assert reporter.exit_code == 1


def test_cli_reporter__on_check_result__unexpected_error(check, capsys):
    reporter = cli.CLIReporter()
    reporter.on_check_result(
        types.CheckResult(
            check=check,
            error=types.CheckError(error="Boom", plugin_type="other"),
        )
    )
    expected = "foo:\n   dance_with_umbrella: Unexpected Raincoat Error (for traceback, use -vv): Boom\n"
    assert capsys.readouterr().out == expected
    assert reporter.exit_code == 1


def test_cli_reporter__on_check_result__skipped_no_updater(check, capsys):
    reporter = cli.CLIReporter(verbosity=1)
    reporter.on_check_result(
        types.CheckResult(check=check, skipped=types.SkippedReason.NO_UPDATER)
    )
    expected = """foo:\n   dance_with_umbrella: No updater defined, this check can only be updated manually ("raincoat check --manual")\n"""
    assert capsys.readouterr().out == expected
    assert reporter.exit_code == 0


def test_cli_reporter__on_check_result__skipped_external_updater(check, capsys):
    cli.CLIReporter(verbosity=1).on_check_result(
        types.CheckResult(check=check, skipped=types.SkippedReason.EXTERNAL_UPDATER)
    )
    expected = """foo:\n   dance_with_umbrella: Updater didn't run because it checks for external resources, and this is disabled unless "--with-external" is used\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_check_result__no_new_version(check, capsys):
    cli.CLIReporter(verbosity=1).on_check_result(types.CheckResult(check=check))
    expected = """foo:\n   dance_with_umbrella: No new version detected\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_check_result__no_update_if_no_diff(check, capsys):
    check.update_if_no_diff = False
    cli.CLIReporter(verbosity=1).on_check_result(
        types.CheckResult(check=check, new_version="2")
    )
    expected = """foo:\n   dance_with_umbrella: New version detected, but it has no diff, and "update_if_no_diff" is True, skipping the update\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_check_result__no_diff(check, capsys):
    cli.CLIReporter(verbosity=1).on_check_result(
        types.CheckResult(check=check, new_version="2")
    )
    expected = """foo:\n   dance_with_umbrella: New version "2" available, no diff. Updating raincoat configuration.\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_check_result__diff__no_fail_if_diff(check, capsys):
    reporter = cli.CLIReporter(verbosity=1, fail_if_diff=False)
    reporter.on_check_result(
        types.CheckResult(check=check, new_version="2", diff="+-foo")
    )
    expected = """foo:\n   dance_with_umbrella: New version "2" available, with diff detected. Please check the diff with `raincoat check` then use `raincoat fix`.

   Diff:
   +-foo
"""
    assert capsys.readouterr().out == expected
    assert reporter.exit_code == 0


def test_cli_reporter__on_check_result__diff__fail_if_diff(check, capsys):
    reporter = cli.CLIReporter(verbosity=1, fail_if_diff=True)
    reporter.on_check_result(
        types.CheckResult(check=check, new_version="2", diff="+-foo"),
    )
    expected = """foo:\n   dance_with_umbrella: New version "2" available, with diff detected. Please check the diff with `raincoat check` then use `raincoat fix`.

   Diff:
   +-foo
"""
    assert capsys.readouterr().out == expected
    assert reporter.exit_code == 1


def test_cli_reporter__on_update_result__no_change(capsys):
    reporter = cli.CLIReporter(verbosity=2, fail_if_diff=True)
    reporter.on_update_result(
        types.UpdateResult(name="dance_with_umbrella", path=pathlib.Path("foo"))
    )
    expected = """foo:\n   dance_with_umbrella: Nothing to report\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_update_result__inconsistent_state():
    reporter = cli.CLIReporter(verbosity=2, fail_if_diff=True)
    with pytest.raises(exceptions.InconsistentState):
        reporter.on_update_result(
            types.UpdateResult(
                name="dance_with_umbrella",
                path=pathlib.Path("foo"),
                old_version="1",
            )
        )


def test_cli_reporter__on_update_result__update_diff(capsys):
    reporter = cli.CLIReporter(verbosity=2, fail_if_diff=True)
    reporter.on_update_result(
        types.UpdateResult(
            name="dance_with_umbrella",
            path=pathlib.Path("foo"),
            old_version="1",
            new_version="2",
        )
    )
    expected = """foo:\n   dance_with_umbrella: diff between "1" and "2"\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_update_result__update_no_diff(capsys):
    reporter = cli.CLIReporter(verbosity=2, fail_if_diff=True)
    reporter.on_update_result(
        types.UpdateResult(
            name="dance_with_umbrella",
            path=pathlib.Path("foo"),
            new_version="2",
        )
    )
    expected = """foo:\n   dance_with_umbrella: updated to "2" (without diff)\n"""
    assert capsys.readouterr().out == expected


def test_cli_reporter__on_fix(capsys):
    reporter = cli.CLIReporter(verbosity=2, fail_if_diff=True)
    reporter.on_fix(
        types.UpdateResult(
            name="dance_with_umbrella",
            path=pathlib.Path("foo"),
            new_version="2",
            fixed=True,
        )
    )
    expected = """foo:\n   dance_with_umbrella: validated version "2"\n"""
    assert capsys.readouterr().out == expected


def test_run_fix__with_checks(make_settings, comment_file):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
old_version = "1"
source.foo = {}""",
        """
[sing_in_the_rain]
version = "3"
old_version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: version}},
    )

    assert cli.cli_fix(settings=settings, checks=["dance_with_umbrella"]) == 0

    assert (
        comment_file.read_text()
        == """
--- raincoat

[dance_with_umbrella]
version = "2"
source.foo = {}
---

--- raincoat

[sing_in_the_rain]
version = "3"
old_version = "2"
source.foo = {}

---
"""
    )


def test_run_fix(make_settings, comment_file):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}""",
        """
[sing_in_the_rain]
version = "3"
old_version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: version}},
    )

    assert cli.cli_fix(settings=settings, checks=[]) == 0

    expected = """
--- raincoat

[dance_with_umbrella]
version = "2"
source.foo = {}
---

--- raincoat

[sing_in_the_rain]
version = "3"
source.foo = {}

---
"""
    assert comment_file.read_text() == expected


def test_cli__check(tmp_path, monkeypatch):
    config = tmp_path / "raincoat.toml"
    monkeypatch.chdir(tmp_path)
    config.write_text(
        """
[checks.dance_with_umbrella]
version = "1"
source.foo = {}
updater.bar = {}
""",
    )

    additional_plugins: Any = {
        "source": {"foo": lambda version: ""},
        "updater": {"bar": lambda: "2"},
    }
    assert (
        cli.cli(
            ["check"],
            additional_plugins=additional_plugins,
        )
        == 0
    )

    expected = """
[checks.dance_with_umbrella]
version = "2"
source.foo = {}
updater.bar = {}
"""
    assert config.read_text() == expected


def test_cli__fix(tmp_path, monkeypatch):
    config = tmp_path / "raincoat.toml"
    monkeypatch.chdir(tmp_path)
    config.write_text(
        """
[checks.dance_with_umbrella]
version = "2"
old_version = "1"
source.foo = {}
updater.bar = {}
""",
    )

    additional_plugins: Any = {
        "source": {"foo": lambda version: ""},
        "updater": {"bar": lambda: "2"},
    }
    assert cli.cli(["fix"], additional_plugins=additional_plugins) == 0

    expected = """
[checks.dance_with_umbrella]
version = "2"
source.foo = {}
updater.bar = {}
"""
    assert config.read_text() == expected


def test_run_cli():
    received = []

    def func(args):
        received.extend(args)
        return 3

    with pytest.raises(SystemExit) as exc_info:
        cli.run_cli(func, ["foo"])

    assert exc_info.value.code == 3
    assert received == ["foo"]
