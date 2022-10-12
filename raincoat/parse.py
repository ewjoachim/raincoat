from __future__ import absolute_import, annotations

import ast
from collections import deque
from typing import Iterable

import asttokens

from raincoat.constants import ELEMENT_NOT_FOUND

Line = str
Lines = Iterable[Line]


class CodeLocator(ast.NodeVisitor):
    def __init__(self, source, filters):
        self.path = deque()
        self.source = source
        self.filters = filters
        self.open_nodes = deque()

    def load(self):
        self.nodes = {}
        self.marked_ast = asttokens.ASTTokens(self.source, parse=True)
        self.visit(self.marked_ast.tree)
        return self.nodes

    def visit_node(self, node):
        self.path.append(node.name)
        node_name = ".".join(self.path)
        if node_name in self.filters:
            self.nodes[node_name] = node
        ast.NodeVisitor.generic_visit(self, node)
        self.path.pop()
        self.open_nodes.append(node)

    def visit_FunctionDef(self, node):
        self.visit_node(node)

    def visit_ClassDef(self, node):
        self.visit_node(node)

    def get_source(self, node):
        start, end = self.marked_ast.get_text_range(node)
        line_start = self.source[:start].rfind("\n") + 1
        line_start = 0 if line_start == -1 else line_start
        line_end = self.source[end:].find("\n")
        line_end = None if line_end == -1 else line_end + end
        return self.source[line_start:line_end].splitlines()


def find_elements(source, elements) -> Iterable[tuple[str, Lines]]:

    elements = set(elements)
    if "" in elements:
        yield "", source.splitlines()
        elements.remove("")

    if elements and source:

        locator = CodeLocator(source=source, filters=elements)

        for node_name, node in locator.load().items():
            elements.remove(node_name)
            yield node_name, locator.get_source(node)

    for element in elements:
        yield element, ELEMENT_NOT_FOUND
