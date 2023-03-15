# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A parent class for the constructors of all pyiron ontologies.
"""

from __future__ import annotations

from warnings import warn

import owlready2 as owl
import pint

from pyiron_ontology.workflow import NodeTree

UREG = pint.UnitRegistry()


class Constructor:
    def __init__(
        self,
        name: str,
        closed: bool = True,
        strict: bool = False,
        debug: int = 0,
    ):
        onto = owl.get_ontology(f"file://{name}.owl")
        self.onto = onto
        self._make_universal_declarations()
        self._make_specific_declarations()
        # TODO: Introduce a "from_csv" option for constructing, and leverage
        #       `all_classes=False` in `declare_classes`?
        self.sync(closed=closed, strict=strict, debug=debug)

    def sync(
        self,
        closed=True,
        infer_property_values=True,
        infer_data_property_values=True,
        debug=0,
        strict=True,
    ):
        if closed:
            owl.close_world(self.onto.PyObject)
        with self.onto:
            owl.sync_reasoner_pellet(
                infer_property_values=infer_property_values,
                infer_data_property_values=infer_data_property_values,
                debug=debug,
            )
        inconsistent = list(self.onto.inconsistent_classes())
        if len(inconsistent) > 0:
            msg = f"Inconsistent classes were found in the ontology: {inconsistent}"
            if strict:
                raise RuntimeError(msg)
            else:
                warn(msg)

    def save(self):
        self.onto.save()

    def _make_specific_declarations(self):
        pass

    def _make_universal_declarations(self):
        with self.onto:

            class PyironOntoThing(owl.Thing):
                def get_sources(
                    self, additional_requirements: list[Generic] = None
                ) -> list[WorkflowThing]:
                    raise NotImplementedError

                def get_source_tree(self, additional_requirements=None):
                    return build_tree(
                        self,
                        additional_requirements=additional_requirements
                    )

                def get_source_path(self, *path_indices: int):
                    return build_path(self, *path_indices)

            class Parameter(PyironOntoThing):
                def unit_conversion(self, other_unit: str) -> float:
                    if self.unit is not None:
                        return UREG(self.unit).to(other_unit).magnitude
                    else:
                        raise ValueError("Parameters must have a unit specified")

            class has_unit(Parameter >> str, owl.FunctionalProperty):
                class_property_type = ["some"]
                python_name = "unit"

            class Generic(Parameter):
                def get_sources(
                    self, additional_requirements: list[Generic] = None
                ) -> list[Output]:
                    return [
                        out
                        for out in self.indirect_outputs
                        if out.satisfies(
                            additional_requirements
                            if additional_requirements is not None
                            else []
                        )
                    ]

                @staticmethod
                def only_get_thing_classes(things):
                    return [
                        is_a_class
                        for is_a_class in things
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
                    return [p for ui in unique_instances for p in ui.parameters]

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
                                dj.entities
                            )  # Don't modify entities in place!
                            entities.remove(thing)
                            thing_disjoints += entities
                        disjoints += thing_disjoints
                    return set(disjoints)

                @property
                def indirect_disjoints_set(self) -> set[Generic]:
                    return self._get_disjoints_set(self.indirect_things)

                @property
                def representation_info(self):
                    """
                    A more computationally efficient call when you know you need both
                    the `indirect_disjoints` _and_ `indirect_things` properties at once.

                    Returns:
                        list, set: indirect things, indirect disjoints
                    """
                    indirect_things = self.indirect_things
                    indirect_disjoints = self._get_disjoints_set(indirect_things)
                    return indirect_disjoints, indirect_things

                @classmethod
                def class_is_indirectly_disjoint_with(cls, other: owl.ThingClass):
                    ancestors1 = list(cls.ancestors())
                    ancestors2 = list(other.ancestors())
                    combined_disjoints = cls._get_disjoints_set(ancestors1).union(
                        cls._get_disjoints_set(ancestors2)
                    )
                    combined_ancestors = set(ancestors1).union(ancestors2)
                    return len(combined_disjoints.intersection(combined_ancestors)) > 0

                def has_a_representation_among_others(self, others_info):
                    my_disjoints, my_things = self.representation_info
                    return any(
                        self._not_disjoint(
                            my_disjoints,
                            other_disjoints,
                            my_things,
                            other_things
                        )
                        for (other_disjoints, other_things) in others_info
                    )

                @staticmethod
                def _not_disjoint(disjoints1, disjoints2, things1, things2):
                    return len(disjoints1.intersection(things2)) == \
                        len(disjoints2.intersection(things1)) == 0

                def is_more_specific_than(self, other: Generic) -> bool:
                    """
                    Only has extra classes compared to other, and none of them are
                    disjoint
                    """
                    my_things_set = set(self.indirect_things)
                    others_things_set = set(other.indirect_things)

                    exclusively_mine = my_things_set.difference(others_things_set)
                    any_of_mine_are_disjoint = any(
                        my_thing in other.indirect_disjoints_set
                        for my_thing in exclusively_mine
                    )
                    return (
                        not any_of_mine_are_disjoint and
                        others_things_set < my_things_set
                    )

            class WorkflowThing(PyironOntoThing):
                pass

            class Function(WorkflowThing):
                def get_sources(
                    self, additional_requirements: list[Generic] = None
                ) -> list[Input]:
                    return self.mandatory_inputs

                @property
                def inputs(self):
                    return self.mandatory_inputs + self.optional_inputs

                @property
                def options(self):
                    options = []
                    for inp in self.inputs:
                        options.append(inp.generic)
                        options += inp.requirements
                        options += inp.transitive_requirements
                    return options

            class IO(Parameter, WorkflowThing):
                pass

            class has_generic(IO >> Generic, owl.FunctionalProperty):
                python_name = "generic"

            class has_for_parameter(Generic >> IO, owl.InverseFunctionalProperty):
                python_name = "parameters"
                inverse_property = has_generic

            class has_hdf_path(IO >> str, owl.FunctionalProperty):
                python_name = "hdf_path"

            class Output(IO):
                def get_sources(
                    self, additional_requirements: list[Generic] = None
                ) -> list[Function]:
                    return [self.output_of]

                @property
                def options(self):
                    return self.output_of.options

                def satisfies(self, requirements: list[Generic]) -> bool:
                    others_info = [
                        other.representation_info
                        for other in self.options + [self.generic]
                    ]
                    return all(
                        requirement.has_a_representation_among_others(others_info)
                        for requirement in requirements
                    )

            class is_output_of(Output >> Function, owl.FunctionalProperty):
                python_name = "output_of"

            class has_for_output(Function >> Output, owl.InverseFunctionalProperty):
                python_name = "outputs"
                inverse_property = is_output_of

            class Input(IO):
                def get_sources(self, additional_requirements=None) -> list[Output]:
                    return self.generic.get_sources(
                        additional_requirements=self.get_requirements(
                            additional_requirements=additional_requirements
                        )
                    )

                def get_requirements(self, additional_requirements=None):
                    # Throw away anything the input can't use, then make a more specific
                    # union of the input's requirements and the additional ones
                    others_info = [
                        other.representation_info
                        for other in [self.generic]
                                     + self.requirements
                                     + self.transitive_requirements
                    ]
                    if additional_requirements is not None:
                        usable_additional_requirements = [
                            req for req in additional_requirements
                            if req.has_a_representation_among_others(others_info)
                        ]
                    else:
                        usable_additional_requirements = []

                    return self.more_specific(
                        usable_additional_requirements
                        + [self.generic]
                        + self.requirements
                    )

                @staticmethod
                def more_specific(requirements: list[Generic]) -> list[Generic]:
                    """
                    Throws away any items for which there is a more specific item in the
                    list.
                    """
                    return [
                        req for req in requirements
                        if not any(
                            other.is_more_specific_than(req) for other in requirements
                        )
                    ]

            class is_optional_input_of(Input >> Function, owl.FunctionalProperty):
                python_name = "optional_input_of"

            class has_for_optional_input(
                Function >> Input, owl.InverseFunctionalProperty
            ):
                python_name = "optional_inputs"
                inverse_property = is_optional_input_of

            class is_mandatory_input_of(Input >> Function, owl.FunctionalProperty):
                python_name = "mandatory_input_of"

            class has_for_mandatory_input(
                Function >> Input, owl.InverseFunctionalProperty
            ):
                python_name = "mandatory_inputs"
                inverse_property = is_mandatory_input_of

            class has_for_requirement(Input >> Generic):
                python_name = "requirements"

            class is_requirement_of(Generic >> Input):
                python_name = "requirement_of"
                inverse_property = has_for_requirement

            class has_for_transitive_requirement(Input >> Generic):
                python_name = "transitive_requirements"

            class is_transitive_requirement_of(Generic >> Input):
                python_name = "transitive_requirement_of"
                inverse_property = has_for_transitive_requirement

            owl.AllDisjoint([is_optional_input_of, is_mandatory_input_of])
            owl.AllDisjoint([Input, Function, Output, Generic])

        def build_tree(
            parameter, parent=None, additional_requirements=None
        ) -> NodeTree:
            node = NodeTree(parameter, parent=parent)

            for source in parameter.get_sources(
                additional_requirements=additional_requirements
            ):
                build_tree(
                    source, parent=node, additional_requirements=additional_requirements
                )

            return node

        def build_path(
            parameter, *path_indices: int, parent=None, additional_requirements=None
        ):
            node = NodeTree(parameter, parent=parent)

            sources = parameter.get_sources(
                additional_requirements=additional_requirements
            )

            if len(path_indices) > 0:
                i, path_indices = path_indices[0], path_indices[1:]
                source = sources[i]
                _, sources = build_path(
                    source,
                    *path_indices,
                    parent=node,
                    additional_requirements=additional_requirements,
                )

            return node, sources
