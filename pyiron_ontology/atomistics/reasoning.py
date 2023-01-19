# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building the atomistics ontology from python classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyiron_ontology.atomistics.constructor import is_subset

if TYPE_CHECKING:
    from pyiron_ontology import atomistics_onto as onto


class Node:
    # TODO: Just use anytree instead -- this is just a temporary placeholder
    def __init__(self, value, parent=None):
        self.value = value
        self.children = []
        self.parent = parent
        if parent is not None:
            parent.children.append(self)

    def render(self, depth=0):
        if depth == 0:
            print(
                "(Target, Executable, Req. Inputs) (note: Target == None --> Use the"
                " Executable as input)\n"
            )
        tabs = ''.join(['\t'] * depth)
        print(f"{tabs}{self.value}")
        for child in self.children:
            child.render(depth=depth + 1)


class AtomisticsReasoner:
    def __init__(self, ontology):
        self.onto = ontology

    def _get_triples_for_generic(self, parameter: onto.GenericParameter):
        triples: list[
            tuple[
                onto.OutputParameter,
                onto.Executable,
                list[onto.InputParameter]
            ]
        ] = []
        sources = self.get_sources(parameter)
        for source in sources:
            target_output = [s for s in source.output if parameter in s.generic_parameter]
            if len(target_output) > 1:
                raise ValueError()
            elif len(target_output) == 0:
                raise RuntimeError()
            else:
                target_output = target_output[0]
            triples.append((target_output, source, list(source.mandatory_input)))

        return triples

    def _get_triples_for_executable(self, parameter: onto.Executable):
        sources = self.gives_consistent_output(parameter)
        triples: list[tuple[None, onto.Executable, list[onto.InputParameter]]] = []
        for source in sources:
            triples.append((None, source, list(source.mandatory_input)))
        return triples

    def _get_triples_for_input(self, parameter: onto.InputParameter):
        triples: list[
            tuple[onto.OutputParameter, onto.Executable, list[onto.InputParameter]]] = []
        outputs = self.gives_consistent_output(parameter, parameter.has_transitive_conditions)
        for output in outputs:
            sources = output.output_of
            for source in sources:
                triples.append((output, source, list(source.mandatory_input)))
        return triples

    def get_triples(self, thing):
        """
        Given a thing, finds the places you can get it.
        """
        if isinstance(thing, self.onto.GenericParameter):
            return self._get_triples_for_generic(thing)
        elif thing.generic_parameter[0] == self.onto.Executable:
            # TODO: I don't like this. I'm pretty sure this only exists because,
            #       from a graph perspective, we're demanding a node as input to
            #       another node! I want a functional world where there are no
            #       reference jobs, only engines (which are no longer jobs) and
            #       macros (which know how to create jobs inside themselves as
            #       needed), s.t. we never pass around jobs (nodes/Executable)
            #       as IO.
            #       You can see right away that this is a bad thing, because the
            #       `target` field needs to be `None` in this case, totally
            #       unlike the other two.
            return self._get_triples_for_executable(thing)
        elif isinstance(thing, self.onto.InputParameter):
            if self.onto.UserInput in thing.generic_parameter[0].domain:
                return [(None, None, [None])]
            else:
                return self._get_triples_for_input(thing)
        else:
            raise RuntimeError(f"Got an unexpected thing, {thing}")

    @staticmethod
    def get_sources(parameter: onto.GenericParameter):
        """
        For a generic parameter, return all codes that output a matching specific parameter
        """
        return [source for specific in parameter.has_parameters for source in
                specific.output_of]

    def build_tree(self, thing, parent=None):
        triples = self.get_triples(thing)
        for triple in triples:
            node = Node(triple, parent=parent)
            for next_ in triple[2]:
                if next_ is not None:
                    self.build_tree(next_, parent=node)
                else:
                    node.value = "User input"
        return node

    @staticmethod
    def gives_consistent_output(thing, additional_conditions=None):
        conditions = thing.has_conditions if additional_conditions is None else additional_conditions

        if len(conditions) > 0:
            return [p for p in thing.generic_parameter[0].has_parameters if
                    is_subset(conditions, p.has_options)]
        else:
            return thing.generic_parameter[0].has_parameters

