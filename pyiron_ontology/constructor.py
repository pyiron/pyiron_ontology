# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A parent class for the constructors of all pyiron ontologies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from warnings import warn

import numpy as np
import owlready2 as owl


def is_subset(a, b):
    return np.all([aa in b for aa in a])


class Constructor(ABC):
    def __init__(self, name: str, closed: bool = True, strict: bool = False):
        onto = owl.get_ontology(f"file://{name}.owl")
        self._make_universal_declarations(onto)
        self._make_specific_declarations(onto)
        # TODO: Introduce a "from_csv" option for constructing, and leverage
        #       `all_classes=False` in `declare_classes`?

        if closed:
            owl.close_world(onto.PyObject)
        with onto:
            owl.sync_reasoner_pellet(
                infer_property_values=True, infer_data_property_values=True, debug=0
            )

        inconsistent = list(onto.inconsistent_classes())
        if len(inconsistent) > 0:
            msg = f"Inconsistent classes were found in the ontology: {inconsistent}"
            if strict:
                raise RuntimeError(msg)
            else:
                warn(msg)

        self.onto = onto

    def save(self):
        self.onto.save()

    @abstractmethod
    def _make_specific_declarations(self, onto):
        pass

    def _make_universal_declarations(self, onto):
        with onto:
            class PyironThing(owl.Thing):
                pass

            class Parameter(PyironThing):
                pass

            class Generic(Parameter):
                @staticmethod
                def only_get_thing_classes(things):
                    return [
                        is_a_class for is_a_class in things
                        if isinstance(is_a_class, owl.ThingClass)
                    ]

                @property
                def indirect_things(self):
                    return self.only_get_thing_classes(self.INDIRECT_is_a)

                @property
                def indirect_io(self) -> list[Parameter]:
                    generic_classes = self.only_get_thing_classes(self.is_a)
                    unique_instances = list(
                        set(generic_classes[0].instances()).union(
                            *[gc.instances() for gc in generic_classes[1:]]
                        )
                    )
                    return [
                        p for ui in unique_instances for p in ui.parameters
                    ]

                @property
                def indirect_outputs(self) -> list[Output]:
                    return [p for p in self.indirect_io if Output in p.is_a]

                @classmethod
                def _get_disjoints_set(cls, classes: list[owl.ThingClass]):
                    disjoints = []
                    for thing in classes:
                        if thing == owl.Thing:
                            continue
                        thing_disjoints = []
                        for dj in thing.disjoints():
                            entities = list(
                                dj.entities)  # Don't modify entities in place!
                            entities.remove(thing)
                            thing_disjoints += entities
                        disjoints += thing_disjoints
                    return set(disjoints)

                @property
                def INDIRECT_disjoints_set(self) -> set[Generic]:
                    return self._get_disjoints_set(self.indirect_things)

                @classmethod
                def class_is_indirectly_disjoint_with(cls, other: owl.ThingClass):
                    ancestors1 = list(cls.ancestors())
                    ancestors2 = list(other.ancestors())
                    combined_disjoints = cls._get_disjoints_set(ancestors1).union(
                        cls._get_disjoints_set(ancestors2)
                    )
                    combined_ancestors = set(ancestors1).union(ancestors2)
                    return len(combined_disjoints.intersection(combined_ancestors)) > 0

                def is_representable_by(self, other: Generic) -> bool:
                    """
                    Checks for disjointness among all indirect thing classes.
                    """
                    my_things = self.indirect_things
                    others_things = other.indirect_things

                    exclusively_mine = set(my_things).difference(others_things)
                    exclusively_others = set(others_things).difference(my_things)

                    my_disjoints = self.INDIRECT_disjoints_set
                    others_disjoints = other.INDIRECT_disjoints_set

                    any_of_mine_are_disjoint = any(
                        [my_thing in others_disjoints for my_thing in exclusively_mine]
                    )
                    any_of_others_are_disjoint = any(
                        [others_thing in my_disjoints for others_thing in
                         exclusively_others]
                    )

                    return not any_of_mine_are_disjoint and not any_of_others_are_disjoint

                def is_more_specific_than(self, other: Generic) -> bool:
                    """
                    Only has extra classes compared to other, and non of them are disjoint
                    """
                    my_things_set = set(self.indirect_things)
                    others_things_set = set(other.indirect_things)

                    exclusively_mine = my_things_set.difference(others_things_set)
                    any_of_mine_are_disjoint = any(
                        [
                            my_thing in other.INDIRECT_disjoints_set
                            for my_thing in exclusively_mine
                        ]
                    )
                    return others_things_set < my_things_set and not any_of_mine_are_disjoint

            class WorkflowThing(PyironThing):
                pass

            class Function(WorkflowThing):
                @property
                def inputs(self):
                    return self.mandatory_inputs + self.optional_inputs

                @property
                def options(self):
                    options = []
                    for inp in self.inputs:
                        options.append(inp.generic)
                        options += inp.requirements
                    return options

            class IO(Parameter, WorkflowThing):
                # Think about renaming this IO and creating a new `Parameter` common ancestor
                # to Generic _and_ IO that has a field for units
                pass

            class has_generic(IO >> Generic, owl.FunctionalProperty):
                python_name = "generic"

            class has_for_parameter(Generic >> IO,
                                    owl.InverseFunctionalProperty):
                python_name = "parameters"
                inverse_property = has_generic

            class Output(IO):
                @property
                def options(self):
                    return self.output_of.options

                def satisfies(self, requirements: list[Generic]) -> bool:
                    return all(
                        [
                            any(
                                [
                                    requirement.is_representable_by(option)
                                    for option in self.options + [self.generic]
                                ]
                            )
                            for requirement in requirements
                        ]
                    )

            class is_output_of(Output >> Function, owl.FunctionalProperty):
                python_name = "output_of"

            class has_for_output(Function >> Output, owl.InverseFunctionalProperty):
                python_name = "outputs"
                inverse_property = is_output_of

            class Input(IO):
                def get_sources(self, additional_requirements=None) -> list[Output]:
                    requirements = self._more_specific_union(
                        self.requirements,
                        additional_requirements
                    ) if additional_requirements is not None else self.requirements
                    return [
                        out for out in self.generic.indirect_outputs
                        if out.satisfies(requirements + [self.generic])
                    ]

                @staticmethod
                def _more_specific_union(
                        requirements1: list[Generic], requirements2: list[Generic]
                ) -> list[Generic]:
                    """
                    A union of two lists of Generics that throws away any less-specific items.
                    """
                    union = list(set(requirements1).union(requirements2))
                    to_remove = [
                        i for i, req_i in enumerate(union)
                        if any([req_j.is_more_specific_than(req_i) for req_j in union])
                    ]
                    return [req for i, req in enumerate(union) if i not in to_remove]

            class is_optional_input_of(Input >> Function, owl.FunctionalProperty):
                python_name = "optional_input_of"

            class has_for_optional_input(Function >> Input,
                                         owl.InverseFunctionalProperty):
                python_name = "optional_inputs"
                inverse_property = is_optional_input_of

            class is_mandatory_input_of(Input >> Function, owl.FunctionalProperty):
                python_name = "mandatory_input_of"

            class has_for_mandatory_input(Function >> Input,
                                          owl.InverseFunctionalProperty):
                python_name = "mandatory_inputs"
                inverse_property = is_mandatory_input_of

            class has_for_requirement(Input >> Generic):
                python_name = "requirements"

            class is_requirement_of(Generic >> Input):
                python_name = "requirement_of"
                inverse_property = has_for_requirement

            owl.AllDisjoint([is_optional_input_of, is_mandatory_input_of])
            owl.AllDisjoint([Input, Function, Output, Generic])
