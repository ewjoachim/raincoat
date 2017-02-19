import pytest

from raincoat.match.pypi import PyPIChecker


@pytest.fixture
def match_info(match):
    return PyPIChecker().get_match_info([match])


def test_match_str(match):
    assert(
        str(match) ==
        "umbrella == 3.2 @ path/to/file.py:MyClass (from filename:12)")


def test_match_str_other_version(match):
    match.other_version = "3.4"
    assert(
        str(match) ==
        "umbrella == 3.2 vs 3.4 @ path/to/file.py:MyClass (from filename:12)")


def test_get_match_info(match, match_module, match_other_file,
                        match_other_package, match_other_version):
    result = PyPIChecker().get_match_info([match_module,
                                           match,
                                           match_other_file,
                                           match_other_package,
                                           match_other_version])
    assert result == (
        {
            ("umbrella", "3.2"): {
                "path/to/file.py": {
                    "MyClass": [match],
                    None: [match_module]},
                "path/to/other_file.py": {"MyOtherClass": [match_other_file]}},
            ("umbrella", "3.4"): {
                "path/to/file.py": {"MyClass": [match_other_version]}},
            ("poncho", "3.2"): {
                "some/file.py": {"SomeClass": [match_other_package]}},
        })


def test_get_all_matches(match, match_module, match_other_file):
    result = (set(PyPIChecker().get_all_matches(
        {"a": {"b": [match, match_module]}, "c": [match_other_file]})))

    assert result == {match, match_module, match_other_file}


def test_compare_blocks(match):
    result = PyPIChecker().compare_blocks(
        match=match,
        match_block=["a", "b"],
        current_block=["a", "c"],
        path="path")

    assert result == ("""Code is different:
--- path
+++ path
@@ -1,2 +1,2 @@
 a
-b
+c""", match)


def test_get_differences():
    match_dict = {"a": "b"}
    current_dict = {"a": "c"}

    result = list(PyPIChecker().get_differences(
        match_dict, current_dict))

    assert result == [("a", ("b", "c"))]


def test_get_differences_identical():
    match_dict = {"a": "b"}
    current_dict = {"a": "b"}

    result = list(PyPIChecker().get_differences(
        match_dict, current_dict))

    assert result == []


def test_get_differences_missing_in_match():
    match_dict = {}
    current_dict = {"a": "b"}

    result = list(PyPIChecker().get_differences(
        match_dict, current_dict))

    assert result == [("a", (None, "b"))]


def test_get_differences_missing_in_current():
    match_dict = {"a": "b"}
    current_dict = {}

    result = list(PyPIChecker().get_differences(
        match_dict, current_dict))

    assert result == [("a", ("b", None))]


def test_compare_packages(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    pass"},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "Code is different:\n"
        "--- path/to/file.py\n"
        "+++ path/to/file.py\n"
        "@@ -1,2 +1,2 @@\n"
        " class MyClass(object):\n"
        "-    pass\n"
        "+    return None",
        match)]


def test_compare_packages_identical(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == []


def test_compare_packages_difference_elsewhere(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None\n"
                "def yay():\n"
                "    pass"},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == []


def test_compare_packages_module(match_module):

    match_info = PyPIChecker().get_match_info([match_module])

    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None\n"
                "def yay():\n"
                "    pass"},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "Code is different:\n"
        "--- path/to/file.py\n"
        "+++ path/to/file.py\n"
        "@@ -1,4 +1,2 @@\n"
        " class MyClass(object):\n"
        "     return None\n"
        "-def yay():\n"
        "-    pass",
        match_module)]


def test_compare_packages_missing_element_in_match(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class Blah(object):\n"
                "    return None"},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "Invalid Raincoat PyPI comment : "
        "MyClass does not exist in path/to/file.py "
        "in umbrella==3.2", match)]


def test_compare_packages_missing_element_in_current(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"},
            {"path/to/file.py":
                "class Blah(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "MyClass disappeared from path/to/file.py "
        "in umbrella", match)]


def test_compare_packages_missing_file_in_match(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {},
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "Invalid Raincoat PyPI comment : "
        "path/to/file.py does not exist in "
        "umbrella==3.2", match)]


def test_compare_packages_missing_file_in_current(match, match_info):
    packages = {
        ("umbrella", "3.2"): (
            {"path/to/file.py":
                "class MyClass(object):\n"
                "    return None"},
            {})}

    result = list(PyPIChecker().compare_packages(
        packages, match_info))

    assert result == [(
        "File path/to/file.py disappeared from umbrella", match)]


def test_mark_other_version(match_info, match):
    PyPIChecker().mark_other_version(match_info, "3.4")

    assert match.other_version == "3.4"


def test_get_packages(mocker, match_info):
    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = True, "3.4"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.return_value = 1
    source.open_installed.return_value = 2

    result = list(PyPIChecker().get_packages(match_info))

    assert source.mock_calls == [
        mocker.call.get_current_or_latest_version("umbrella"),
        mocker.call.download_package("umbrella", "3.2", "/tmp/clean"),
        mocker.call.open_downloaded("/tmp/clean", ["path/to/file.py"],
                                    "umbrella"),
        mocker.call.get_current_path("umbrella"),
        mocker.call.open_installed("/sites_packages/umbrella",
                                   ["path/to/file.py"]),
    ]

    assert result == [(("umbrella", "3.2"), (1, 2))]


def test_get_packages_identical(mocker, match_info):
    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = True, "3.4"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.return_value = 1
    source.open_installed.return_value = 1

    result = list(PyPIChecker().get_packages(match_info))

    assert result == []


def test_get_packages_same_version(mocker, match_info):
    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = True, "3.2"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.return_value = 1
    source.open_installed.return_value = 2

    result = list(PyPIChecker().get_packages(match_info))

    assert source.mock_calls == [
        mocker.call.get_current_or_latest_version("umbrella"),
    ]

    assert result == []


def test_get_packages_package_cache(mocker, match, match_other_version):
    match_info = PyPIChecker().get_match_info([match, match_other_version])

    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = True, "3.5"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.return_value = 1
    source.open_installed.return_value = 2

    result = list(PyPIChecker().get_packages(match_info))

    assert source.mock_calls == [
        mocker.call.get_current_or_latest_version("umbrella"),
        # First version
        mocker.call.download_package("umbrella", "3.2", "/tmp/clean"),
        mocker.call.open_downloaded("/tmp/clean", ["path/to/file.py"],
                                    "umbrella"),
        mocker.call.get_current_path("umbrella"),
        mocker.call.open_installed("/sites_packages/umbrella",
                                   ["path/to/file.py"]),

        # Second version, current version is cached
        mocker.call.download_package("umbrella", "3.4", "/tmp/clean"),
        mocker.call.open_downloaded("/tmp/clean", ["path/to/file.py"],
                                    "umbrella"),
    ]

    assert result == [(("umbrella", "3.2"), (1, 2)),
                      (("umbrella", "3.4"), (1, 2))]


def test_get_package_not_installed(mocker, match_info):
    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = False, "3.4"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.side_effect = [1, 2]

    result = list(PyPIChecker().get_packages(match_info))

    assert source.mock_calls == [
        mocker.call.get_current_or_latest_version("umbrella"),
        mocker.call.download_package("umbrella", "3.2", "/tmp/clean"),
        mocker.call.open_downloaded("/tmp/clean", ["path/to/file.py"],
                                    "umbrella"),
        mocker.call.download_package("umbrella", "3.4", "/tmp/clean"),
        mocker.call.open_downloaded("/tmp/clean", ["path/to/file.py"],
                                    "umbrella"),
    ]

    assert result == [(("umbrella", "3.2"), (1, 2))]


def test_check(mocker, match):
    source = mocker.patch("raincoat.match.pypi.source")
    mocker.patch("raincoat.match.pypi.Cleaner.mkdir",
                 return_value="/tmp/clean")
    source.get_current_or_latest_version.return_value = True, "3.4"
    source.get_current_path.return_value = "/sites_packages/umbrella"
    source.open_downloaded.return_value = {
        "path/to/file.py": "class MyClass():\n"
                           "    pass"
    }
    source.open_installed.return_value = {
        "path/to/file.py": "class MyClass():\n"
                           "    return None"
    }

    assert list(PyPIChecker().check([match])) == [(
        "Code is different:\n"
        "--- path/to/file.py\n"
        "+++ path/to/file.py\n"
        "@@ -1,2 +1,2 @@\n"
        " class MyClass():\n"
        "-    pass\n"
        "+    return None",
        match)]
