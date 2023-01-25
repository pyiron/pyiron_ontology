# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A tree structure for ontologically-informed workflows
"""


class NodeTree:
    def __init__(self, value, parent=None):
        self.value = value
        self.children = []
        self.parent = parent
        if parent is not None:
            parent.children.append(self)

    def render(self, depth=0):
        tabs = "".join(["\t"] * depth)
        print(f"{tabs}{self.value}")
        for child in self.children:
            child.render(depth=depth + 1)


def build_tree(parameter, parent=None, transitive_conditions=None) -> NodeTree:
    node = NodeTree(parameter, parent=parent)

    conditions = parameter.get_all_conditions(transitive_conditions)

    for source in parameter.get_sources(conditions):
        build_tree(source, parent=node, transitive_conditions=conditions)

    return node