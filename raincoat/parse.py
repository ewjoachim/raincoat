from __future__ import absolute_import

import ast
from collections import deque

from raincoat.ast_utils import mark_text_ranges


class CodeLocator(ast.NodeVisitor):
    def __init__(self, source, filters):
        self.path = deque()
        self.source = source
        self.filters = filters

    def load(self):
        self.nodes = {}
        nodes = ast.parse(self.source)
        mark_text_ranges(nodes, self.source)
        self.visit(nodes)
        return self.nodes

    def visit_node(self, node):
        self.path.append(node.name)
        node_name = ".".join(self.path)
        if node_name in self.filters:
            self.nodes[node_name] = node
        ast.NodeVisitor.generic_visit(self, node)
        self.path.pop()

    def visit_FunctionDef(self, node):
        self.visit_node(node)

    def visit_ClassDef(self, node):
        self.visit_node(node)


def find_objects(source, code_objects):

    source_lines = source.splitlines()

    if not all(code_objects):
        yield None, source_lines

    if any(code_objects):

        locator = CodeLocator(source=source, filters=code_objects)

        for node_name, node in locator.load().items():
            if node_name in code_objects:
                yield node_name, source_lines[node.lineno - 1:node.end_lineno]
