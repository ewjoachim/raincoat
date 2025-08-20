from __future__ import annotations

import dataclasses

from raincoat import raincoat, types, updater


def test_default_diff_function__no_diff():
    assert raincoat.default_diff_function(ref="foo", new="foo") is None


def test_default_diff_function():
    result = raincoat.default_diff_function(ref="foo", new="bar")
    expected = """--- ref
+++ new
@@ -1 +1 @@
-foo+bar"""

    assert result == expected


def test_check_single__no_updater(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
        },
    )
    result = raincoat.check_single(settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        skipped=types.SkippedReason.NO_UPDATER,
    )

    assert result == expected


def test_check_single__update_with_diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "17.3.5"},
        },
    )

    result = raincoat.check_single(settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="17.3.5",
        diff="--- ref\n+++ new\n@@ -1 +1 @@\n-14.5.7+17.3.5",
    )

    assert result == expected


def test_check_single__update_without_diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: "foo"},
            "updater": {"bar": lambda: "17.3.5"},
        },
    )

    result = raincoat.check_single(settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="17.3.5",
    )

    assert result == expected


def test_check_single__manual__no_diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: "foo"},
        },
    )

    result = raincoat.check_single(
        check=settings.checks["dance_with_umbrella"], manual_version="17.3.5"
    )

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="17.3.5",
    )

    assert result == expected


def test_check_single__manual__diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
        },
    )

    result = raincoat.check_single(
        check=settings.checks["dance_with_umbrella"], manual_version="17.3.5"
    )

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="17.3.5",
        diff="--- ref\n+++ new\n@@ -1 +1 @@\n-14.5.7+17.3.5",
    )

    assert result == expected


def test_check_single__no_new_version(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}
updater.bar = {}

""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "14.5.7"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(check=settings.checks["dance_with_umbrella"])

    assert result == expected


def test_check_single__fail_to_fetch_new_code(make_settings):
    def source(version):
        if version == "1":
            return "foo"
        raise ValueError

    settings = make_settings(
        """
[dance_with_umbrella]
version = "1"
source.foo = {}
updater.bar = {}

""",
        additional_plugins={
            "source": {"foo": source},
            "updater": {"bar": lambda: "2"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="2",
        diff="--- ref\n+++ new\n@@ -1 +0,0 @@\n-foo",
    )

    assert result == expected


def test_check_single__diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "1"
source.foo = {}
diff.baz.suffix = "yay"
updater.bar = {}

""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "diff": {"baz": lambda ref, new, suffix: f"-{ref}+{new}/{suffix}"},
            "updater": {"bar": lambda: "2"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="2",
        diff="-1+2/yay",
    )

    assert result == expected


def test_check_single__old_version(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
old_version = "1"
version = "2"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "3"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        new_version="2",
        diff="--- ref\n+++ new\n@@ -1 +1 @@\n-1+2",
    )

    assert result == expected


def test_check_single__error_updater(make_settings):
    def updater():
        raise ValueError("Boom")

    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": updater},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        error=types.CheckError(error="Boom", plugin_type="updater"),
    )

    assert result == expected


def test_check_single__error_source(make_settings):
    def source(version):
        raise ValueError("Boom")

    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": source},
            "updater": {"bar": lambda: "3"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        error=types.CheckError(error="Boom", plugin_type="source"),
    )

    assert result == expected


def test_check_single__error_diff(make_settings):
    def diff(ref, new):
        raise ValueError("Boom")

    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
diff.baz = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "diff": {"baz": diff},
            "updater": {"bar": lambda: "3"},
        },
    )

    result = raincoat.check_single(check=settings.checks["dance_with_umbrella"])

    expected = types.CheckResult(
        check=settings.checks["dance_with_umbrella"],
        error=types.CheckError(error="Boom", plugin_type="diff"),
    )

    assert result == expected


def test_check(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}

[sing_in_the_rain]
version = "23.5.8"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "24"},
        },
    )

    result = list(raincoat.check(checks=settings.checks))

    expected = [
        types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            skipped=types.SkippedReason.NO_UPDATER,
        ),
        types.CheckResult(
            check=settings.checks["sing_in_the_rain"],
            new_version="24",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-23.5.8+24",
        ),
    ]

    assert result == expected


def test_check__manual_version(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "14.5.7"
source.foo = {}

[sing_in_the_rain]
version = "23.5.8"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "24"},
        },
    )

    result = list(
        raincoat.check(
            checks=settings.checks,
            manual_updates=[
                types.ManualUpdate(name="dance_with_umbrella", version="17")
            ],
        )
    )

    expected = [
        types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            new_version="17",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-14.5.7+17",
        ),
    ]

    assert result == expected


def test_check__no_include_external_updaters(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "12"
source.foo = {}
updater.bar = {}

[sing_in_the_rain]
version = "13"
source.foo = {}
updater.bar_ext = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {
                "bar": lambda: "24",
                "bar_ext": updater.external(lambda: "24"),
            },
        },
    )

    result = list(
        raincoat.check(checks=settings.checks, include_external_updaters=False),
    )

    expected = [
        types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            new_version="24",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-12+24",
        ),
        types.CheckResult(
            check=settings.checks["sing_in_the_rain"],
            skipped=types.SkippedReason.EXTERNAL_UPDATER,
        ),
    ]

    assert result == expected


def test_check__include_external_updaters(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "12"
source.foo = {}
updater.bar = {}

[sing_in_the_rain]
version = "13"
source.foo = {}
updater.bar_ext = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {
                "bar": lambda: "24",
                "bar_ext": updater.external(lambda: "24"),
            },
        },
    )

    result = list(
        raincoat.check(checks=settings.checks, include_external_updaters=True)
    )

    expected = [
        types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            new_version="24",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-12+24",
        ),
        types.CheckResult(
            check=settings.checks["sing_in_the_rain"],
            new_version="24",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-13+24",
        ),
    ]

    assert result == expected


def test_check__error(make_settings, mocker):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "12"
source.foo = {}
updater.bar = {}

[sing_in_the_rain]
version = "13"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "24"},
        },
    )
    mocker.patch(
        "raincoat.raincoat.check_single",
        side_effect=[
            ValueError("Boom"),
            types.CheckResult(
                check=settings.checks["sing_in_the_rain"],
                new_version="24",
                diff="--- ref\n+++ new\n@@ -1 +1 @@\n-13+24",
            ),
        ],
    )
    result = list(raincoat.check(checks=settings.checks))

    expected = [
        types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            error=types.CheckError(error="Boom", plugin_type="other"),
        ),
        types.CheckResult(
            check=settings.checks["sing_in_the_rain"],
            new_version="24",
            diff="--- ref\n+++ new\n@@ -1 +1 @@\n-13+24",
        ),
    ]

    assert result == expected


def test_generate_update_instructions__plugin_error(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    update_instructions = raincoat.generate_update_instructions(
        check_result=types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            error=types.CheckError(error="Boom", plugin_type="source"),
        ),
    )

    assert update_instructions == types.UpdateInstructions(name="dance_with_umbrella")


def test_generate_update_instructions__no_new_version(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    update_instructions = raincoat.generate_update_instructions(
        check_result=types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
        )
    )

    assert update_instructions == types.UpdateInstructions(name="dance_with_umbrella")


def test_generate_update_instructions__no_update_if_no_diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
update_if_no_diff = false
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    update_instructions = raincoat.generate_update_instructions(
        check_result=types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            diff=None,
            new_version="3",
        )
    )

    assert update_instructions == types.UpdateInstructions(name="dance_with_umbrella")


def test_generate_update_instructions__update_if_no_diff(make_settings):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    update_instructions = raincoat.generate_update_instructions(
        check_result=types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            diff=None,
            new_version="3",
        )
    )

    assert update_instructions == types.UpdateInstructions(
        name="dance_with_umbrella", set_new_version="3"
    )


def test_generate_update_instructions__diff(make_settings, capsys):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    update_instructions = raincoat.generate_update_instructions(
        check_result=types.CheckResult(
            check=settings.checks["dance_with_umbrella"],
            diff="foo",
            new_version="3",
        ),
    )

    assert update_instructions == types.UpdateInstructions(
        name="dance_with_umbrella",
        set_new_version="3",
        set_old_version="2",
    )


@dataclasses.dataclass
class TestReporter:
    check_results: list[types.CheckResult] = dataclasses.field(default_factory=list)
    update_results: list[types.UpdateResult] = dataclasses.field(default_factory=list)
    fix_results: list[types.UpdateResult] = dataclasses.field(default_factory=list)

    def on_check_result(self, result: types.CheckResult, /):
        self.check_results.append(result)

    def on_update_result(self, result: types.UpdateResult, /):
        self.update_results.append(result)

    def on_fix(self, result: types.UpdateResult, /):
        self.fix_results.append(result)


def test_run_check(make_settings, comment_file):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
""",
        additional_plugins={"source": {"foo": lambda version: ""}},
    )
    reporter = TestReporter()
    raincoat.run_check_and_update(
        settings=settings,
        manual_updates=[types.ManualUpdate(name="dance_with_umbrella", version="3")],
        reporter=reporter,
    )
    assert reporter == TestReporter(
        check_results=[
            types.CheckResult(
                check=settings.checks["dance_with_umbrella"],
                new_version="3",
                diff=None,
                error=None,
                skipped=None,
            ),
        ],
        update_results=[
            types.UpdateResult(
                name="dance_with_umbrella",
                path=comment_file,
                new_version="3",
                old_version=None,
                fixed=False,
            ),
        ],
    )

    assert (
        comment_file.read_text()
        == """
--- raincoat

[dance_with_umbrella]
version = "3"
source.foo = {}

---
"""
    )


def test_run_check__no_reporter(make_settings, comment_file):
    settings = make_settings(
        """
[dance_with_umbrella]
version = "2"
source.foo = {}
updater.bar = {}
""",
        additional_plugins={
            "source": {"foo": lambda version: version},
            "updater": {"bar": lambda: "3"},
        },
    )
    raincoat.run_check_and_update(settings=settings)

    assert (
        comment_file.read_text()
        == """
--- raincoat

[dance_with_umbrella]
version = "3"
source.foo = {}
updater.bar = {}
old_version = "2" # Remove this line when the diff has been checked

---
"""
    )


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
    reporter = TestReporter()
    raincoat.run_fix(
        settings=settings,
        checks=["dance_with_umbrella"],
        reporter=reporter,
    )

    assert reporter == TestReporter(
        fix_results=[
            types.UpdateResult(
                name="dance_with_umbrella",
                path=comment_file,
                new_version="2",
                old_version=None,
                fixed=True,
            ),
        ]
    )
    expected = """
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
    assert comment_file.read_text() == expected


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

    raincoat.run_fix(settings=settings, checks=[])

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
