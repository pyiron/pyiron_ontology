# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A tree structure for ontologically-informed workflows
"""

from numpy import argsort


class NodeTree:
    def __init__(self, value, parent=None):
        self.value = value
        self.children = []
        self.parent = parent
        if parent is not None:
            parent.children.append(self)

    def render(self, depth=0, order_alphabetically=True):
        tabs = "".join(["  "] * depth)
        print(f"{tabs}{self.value.name}")
        children = (
            [self.children[n] for n in argsort([str(c.value) for c in self.children])]
            if order_alphabetically
            else self.children
        )
        for child in children:
            child.render(depth=depth + 1)
