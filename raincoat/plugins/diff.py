"""Diff plugins for comparing code."""

from __future__ import annotations

import ast
from typing import Any

from raincoat import exceptions, raincoat


class ElementFinder(ast.NodeVisitor):
    def __init__(self, element: str):
        super().__init__()
        self.current_parts = []
        self.element = element.split(".")
        self.found: ast.AST | None = None

    def check(self, node: ast.AST, name: str) -> None:
        if [*self.current_parts, name] == self.element:
            self.found = node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.check(node, node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.check(node, node.name)

        self.current_parts.append(node.name)
        self.generic_visit(node)
        self.current_parts.pop()

    def visit_Assign(self, node: ast.Assign) -> Any:
        if isinstance(node.targets[0], ast.Name):
            self.check(node, node.targets[0].id)

        self.generic_visit(node)


default = raincoat.default_diff_function


def get_element_code(tree: ast.AST, element: str) -> ast.AST:
    finder = ElementFinder(element)
    finder.visit(tree)
    found = finder.found

    if not found:
        raise exceptions.PythonDiffElementNotFoundError(element=element)

    return found


async def python(
    *,
    ref: str,
    new: str,
    element: str | None = None,
) -> str | None:
    """
    A diff plugin for Python code that can compare specific functions/classes.

    Parameters
    ----------
    ref:
        The reference Python code
    new:
        The new Python code
    element:
        Optional element (function/class/method) name to compare

    Returns
    -------
    str | None
        A unified diff if the code is different, None if identical
    """
    try:
        ref_ast = ast.parse(ref)
        new_ast = ast.parse(new)
    except SyntaxError as exc:
        raise exceptions.PythonDiffSyntaxError(error=exc)

    if element:
        # Find specific element in both versions
        ref_ast = get_element_code(ref_ast, element)
        try:
            new_ast = get_element_code(new_ast, element)
        except exceptions.PythonDiffElementNotFoundError:
            # If element not found in new code, consider it as removed, show diff of removal
            return await default(
                ref=ast.get_source_segment(ref, ref_ast) or ast.unparse(ref_ast),
                new="",
            )

    # Compare the ASTs (ignoring formatting differences)
    if ast.dump(ref_ast) == ast.dump(new_ast):
        return None

    # If ASTs differ, show a traditional diff of real code (or of unparsed AST)
    return await default(
        ref=ast.get_source_segment(ref, ref_ast) or ast.unparse(ref_ast),
        new=ast.get_source_segment(new, new_ast) or ast.unparse(new_ast),
    )
