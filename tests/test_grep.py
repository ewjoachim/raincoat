import io
import tempfile

import six

from raincoat import grep


def test_string_normal():
    matches = list(grep.find_in_string("""
        # Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py element: foo
    """, filename="foo/bar"))

    assert len(matches) == 1
    match, = matches

    assert match.package == "BLA"
    assert match.version == "1.2.3"
    assert match.path == "yo/yeah.py"
    assert match.element == "foo"
    assert match.lineno == 2
    assert match.filename == "foo/bar"


def test_string_normal_whole_module():
    matches = list(grep.find_in_string("""
        # Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py
    """, filename="foo/bar"))

    assert len(matches) == 1
    match, = matches

    assert match.package == "BLA"
    assert match.version == "1.2.3"
    assert match.path == "yo/yeah.py"
    assert match.element == ""
    assert match.lineno == 2
    assert match.filename == "foo/bar"


def test_other_operator(caplog):
    matches = list(grep.find_in_string("""
        # Raincoat: pypi package: BLA>=1.2.3 path: yo/yeah.py: foo
    """, "foo/bar"))
    assert "Unrecognized Raincoat comment" in caplog.records[0].message
    assert len(matches) == 0


def test_empty():
    matches = list(grep.find_in_string("", ""))

    assert len(matches) == 0


def test_find_in_file():
    with tempfile.NamedTemporaryFile("w+") as handler:
        handler.write("""
            # Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py element: foo
        """)
        handler.seek(0)
        matches = list(grep.find_in_file(handler.name))
        assert len(matches) == 1


def test_find_in_file_oneliner():
    with tempfile.NamedTemporaryFile("w+") as handler:
        handler.write('''# Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py element: foo''')  # noqa
        handler.seek(0)
        matches = list(grep.find_in_file(handler.name))
        assert len(matches) == 1


def test_find_in_file_with_comment():
    with tempfile.NamedTemporaryFile("w+") as handler:
        handler.write('''# Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py element: foo  # noqa''')  # noqa
        handler.seek(0)
        matches = list(grep.find_in_file(handler.name))
        assert len(matches) == 1
        assert matches[0].element == "foo"


def test_list_python_files(mocker):
    walk = mocker.patch("os.walk")
    walk.return_value = [
        (".", ["a"], ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f")) == [
        "c.py", "a/e.py"
    ]


def test_list_python_files_exclude_dir_dot_slash(mocker):
    walk = mocker.patch("os.walk")
    dirs = ["a", "b"]
    walk.return_value = [
        (".", dirs, ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["./b"])) == [
        "c.py", "a/e.py"
    ]
    assert dirs == ["a"]


def test_list_python_files_exclude_dir(mocker):
    walk = mocker.patch("os.walk")
    dirs = ["a", "b"]
    walk.return_value = [
        (".", dirs, ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["b"])) == [
        "c.py", "a/e.py"
    ]
    assert dirs == ["a"]


def test_list_python_files_exclude_multiple(mocker):
    walk = mocker.patch("os.walk")
    dirs = ["a", "b"]
    walk.return_value = [
        (".", dirs, ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["b", "a/*"])) == [
        "c.py"
    ]
    assert dirs == ["a"]


def test_list_python_files_exclude_dir_wildcard(mocker):
    walk = mocker.patch("os.walk")
    dirs = ["aaa", "bbb"]
    walk.return_value = [
        (".", dirs, ["b.txt", "c.py"]),
        ("aaa", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["b*"])) == [
        "c.py", "aaa/e.py"
    ]
    assert dirs == ["aaa"]


def test_list_python_files_exclude_file(mocker):
    walk = mocker.patch("os.walk")
    walk.return_value = [
        (".", ["a"], ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["a/e.py"])) == [
        "c.py"]


def test_list_python_files_exclude_file_wildcard(mocker):
    walk = mocker.patch("os.walk")
    walk.return_value = [
        (".", ["a"], ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f", exclude=["a/*.py"])) == [
        "c.py"]


# Full chain test
def test_find_in_dir(mocker):
    open_responses = iter([
        ("c.py", io.StringIO(
            six.u('''# Raincoat: pypi package: BLA==1.2.3 path: yo/yeah.py element: foo'''))),  # noqa
        ("a/e.py", io.StringIO(
            six.u('''# Raincoat: pypi package: BLU==1.2.4 path: yo/hai.py element: bar'''))),  # noqa
    ])

    def fake_open(file):
        expected_file, response = next(open_responses)
        assert expected_file == file
        return response

    open_mock = mocker.patch("raincoat.grep.open", create=True)
    open_mock.side_effect = fake_open

    walk = mocker.patch("os.walk")
    walk.return_value = [
        (".", ["a"], ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]
    matches = list(grep.find_in_dir("f"))

    assert len(matches) == 2
    m1, m2 = matches
    assert m1.filename == "c.py"
    assert m1.lineno == 1
    assert m1.package == "BLA"

    assert m2.filename == "a/e.py"
    assert m2.lineno == 1
    assert m2.package == "BLU"
