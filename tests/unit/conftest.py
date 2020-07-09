import pytest

from raincoat.match.pypi import PyPIMatch
from raincoat.color import Color


@pytest.fixture
def match_module():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="umbrella==3.2",
        path="path/to/file.py",
        element=""
    )


@pytest.fixture
def match():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="umbrella==3.2",
        path="path/to/file.py",
        element="MyClass"
    )


@pytest.fixture
def match_other_file():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="umbrella==3.2",
        path="path/to/other_file.py",
        element="MyOtherClass"
    )


@pytest.fixture
def match_other_package():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="poncho==3.2",
        path="some/file.py",
        element="SomeClass"
    )


@pytest.fixture
def match_other_version():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="umbrella==3.4",
        path="path/to/file.py",
        element="MyClass"
    )


@pytest.fixture
def match_other_version_other_file():
    return PyPIMatch(
        filename="filename",
        lineno=12,
        package="umbrella==3.4",
        path="path/to/other_file.py",
        element="MyClass"
    )


class ValuesAreKeys(object):
    def __getitem__(self, key):
        return key

    def get(self, key, *args):
        return key


@pytest.fixture
def color():
    return Color(ValuesAreKeys())
