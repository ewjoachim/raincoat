import io
import tempfile

import six

from raincoat import grep


def test_string_normal():
    matches = list(grep.find_in_string("""
        # Raincoat: package "BLA==1.2.3" path "yo/yeah.py" "foo"
    """, filename="foo/bar"))

    assert len(matches) == 1
    match, = matches

    assert match.package == "BLA"
    assert match.version == "1.2.3"
    assert match.path == "yo/yeah.py"
    assert match.code_object == "foo"
    assert match.lineno == 2
    assert match.filename == "foo/bar"


def test_other_operator():
    matches = list(grep.find_in_string("""
        # Raincoat: package "BLA>=1.2.3" path "yo/yeah.py" "foo"
    """, "foo/bar"))

    assert len(matches) == 0


def test_empty():
    matches = list(grep.find_in_string("", ""))

    assert len(matches) == 0


def test_find_in_file():
    with tempfile.NamedTemporaryFile("w+") as handler:
        handler.write("""
            # Raincoat: package "BLA==1.2.3" path "yo/yeah.py" "foo"
        """)
        handler.seek(0)
        matches = list(grep.find_in_file(handler.name))
        assert len(matches) == 1


def test_list_python_files(mocker):
    walk = mocker.patch("os.walk")
    walk.return_value = [
        (".", ["a"], ["b.txt", "c.py"]),
        ("a", [], ["d.txt", "e.py"]),
    ]

    assert list(grep.list_python_files("f")) == [
        "c.py", "a/e.py"
    ]


# Full chain test
def test_find_in_dir(mocker):
    open_responses = iter([
        ("c.py", io.StringIO(
            six.u('''# Raincoat: package "BLA==1.2.3" '''
                  '''path "yo/yeah.py" "foo"'''))),
        ("a/e.py", io.StringIO(
            six.u('''# Raincoat: package "BLU==1.2.4" '''
                  '''path "yo/hai.py" "bar"'''))),
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
