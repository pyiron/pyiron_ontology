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


def build_tree(parameter, parent=None, additional_conditions=None) -> NodeTree:
    node = NodeTree(parameter, parent=parent)
    conditions = parameter.get_conditions(additional_conditions)

    for source in parameter.get_sources(conditions):
        build_tree(source, parent=node, additional_conditions=conditions)

    return node


def build_path(parameter, *path_indices: int, parent=None, additional_conditions=None):
    node = NodeTree(parameter, parent=parent)
    conditions = parameter.get_conditions(additional_conditions)
    sources = parameter.get_sources(conditions)

    if len(path_indices) > 0:
        i, path_indices = path_indices[0], path_indices[1:]
        source = sources[i]
        _, sources = build_path(
            source, *path_indices, parent=node, additional_conditions=conditions
        )

    return node, sources
