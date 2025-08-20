from __future__ import annotations

import ast

import pytest

from raincoat import exceptions
from raincoat.plugins import diff


@pytest.fixture
def module_ast():
    return ast.parse("""
a = 1+2
def b():
    pass
class C:
    def d(self):
        pass
""")


def test_get_element_code__not_found(module_ast):
    with pytest.raises(exceptions.PythonDiffElementNotFoundError):
        diff.get_element_code(tree=module_ast, element="e")


@pytest.mark.parametrize(
    "element, expected",
    [
        ("a", "a = 1 + 2"),
        ("b", "def b():\n    pass"),
        ("C", "class C:\n\n    def d(self):\n        pass"),
        ("C.d", "def d(self):\n    pass"),
    ],
)
def test_get_element_code_assign(module_ast, element, expected):
    result = ast.unparse(diff.get_element_code(tree=module_ast, element=element))
    assert result == expected


@pytest.mark.parametrize(
    "ref, new, element, expected",
    [
        (
            "a = 1 + 2",
            "a = 1    +3",
            "a",
            "--- ref\n+++ new\n@@ -1 +1 @@\n-a = 1 + 2+a = 1    +3",
        ),
        (
            "a = 1 + 2\nb=1",
            "a = 1    +3\nb=1",
            "b",
            None,
        ),
        (
            "a = 1 + 2",
            "a = 1    +2",
            "a",
            None,
        ),
    ],
)
def test_python(ref, new, element, expected):
    assert diff.python(ref=ref, new=new, element=element) == expected
