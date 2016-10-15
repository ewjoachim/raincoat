from __future__ import absolute_import

import ast
from collections import deque


class CodeLocator(ast.NodeVisitor):
    def __init__(self, source, filters):
        self.path = deque()
        self.source = source
        self.source_lines = source.splitlines()
        self.filters = filters
        self.ended_nodes = deque()

    def load(self):
        self.nodes = {}
        nodes = ast.parse(self.source)
        self.visit(nodes)
        self.mark_end_lineno(self.source.count("\n"))
        return self.nodes

    def mark_end_lineno(self, lineno):
        # Empty lines are not counted
        while not self.source_lines[lineno - 1]:
            lineno -= 1

        # Mark all finshed nodes
        try:
            while True:
                self.ended_nodes.pop().end_lineno = lineno
        except IndexError:
            pass

    def visit_node(self, node):
        self.path.append(node.name)
        node_name = ".".join(self.path)
        if node_name in self.filters:
            self.nodes[node_name] = node
        ast.NodeVisitor.generic_visit(self, node)
        self.path.pop()
        self.ended_nodes.append(node)

    def visit_FunctionDef(self, node):
        self.visit_node(node)
        if node.decorator_list:
            node.lineno = min(decorator.lineno
                              for decorator in node.decorator_list)

    def visit_ClassDef(self, node):
        self.visit_node(node)

    def visit(self, node):
        end_lineno = getattr(node, 'lineno', 1) - 1
        self.mark_end_lineno(end_lineno)

        super(CodeLocator, self).visit(node)


def find_objects(source, code_objects):

    source_lines = source.splitlines()

    if not all(code_objects):
        yield None, source_lines

    if any(code_objects):

        locator = CodeLocator(source=source, filters=code_objects)

        for node_name, node in locator.load().items():
            if node_name in code_objects:
                yield node_name, source_lines[node.lineno - 1:node.end_lineno]
