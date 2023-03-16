# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A parent class for the constructors of all pyiron ontologies.
"""

from __future__ import annotations

from typing import Optional
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
                        self, additional_requirements=additional_requirements
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
                        if (
                            out.satisfies(additional_requirements)
                            if additional_requirements is not None
                            else True
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

                @property
                def indirect_disjoints_set(self) -> set[Generic]:
                    return get_disjoints_set(self.indirect_things)

                @property
                def representation_info(self):
                    """
                    A more computationally efficient call when you know you need both
                    the `indirect_disjoints` _and_ `indirect_things` properties at once.

                    Returns:
                        list, set: indirect things, indirect disjoints
                    """
                    indirect_things = self.indirect_things
                    indirect_disjoints = get_disjoints_set(indirect_things)
                    return indirect_things, indirect_disjoints

                @classmethod
                def class_is_indirectly_disjoint_with(cls, other: owl.ThingClass):
                    ancestors1 = list(cls.ancestors())
                    ancestors2 = list(other.ancestors())
                    combined_disjoints = get_disjoints_set(ancestors1).union(
                        get_disjoints_set(ancestors2)
                    )
                    combined_ancestors = set(ancestors1).union(ancestors2)
                    return len(combined_disjoints.intersection(combined_ancestors)) > 0

                def has_a_representation_among_others(self, others_info):
                    my_things, my_disjoints = self.representation_info
                    return any(
                        compatible_classes(
                            my_things,
                            my_disjoints,
                            other_things,
                            other_disjoints,
                        )
                        for (other_things, other_disjoints) in others_info
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
                    return [
                        opt
                        for inp in self.inputs
                        for opt in [inp.generic]
                        + inp.requirements
                        + inp.transitive_requirements
                    ]

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
                def get_sources(
                    self, additional_requirements: Optional[list[Generic]] = None
                ) -> list[Output]:
                    return self.get_sources_and_passed_requirements(
                        additional_requirements=additional_requirements
                    )[0]

                def get_sources_and_passed_requirements(
                    self, additional_requirements: Optional[list[Generic]] = None
                ) -> tuple[list[Output], list[Generic]]:
                    requirements = self.get_requirements(
                        additional_requirements=additional_requirements
                    )
                    sources = self.generic.get_sources(
                        additional_requirements=requirements
                    )
                    return sources, requirements

                def get_requirements(self, additional_requirements=None):
                    """
                    For each additional requirement, see if it is as or more specific
                    than an existing requirement (from among the generic class,
                    requirements, and transitive requirements), and if so keep it
                    (discarding the original if in the generic class or requirements,
                    appending if it's a transitive requirement that we're actually
                    receiving).
                    """
                    if additional_requirements is None:
                        return [self.generic] + self.requirements
                    requirements = [self.generic] + self.requirements

                    base_infos = [other.representation_info for other in requirements]
                    transitive_infos = [
                        other.representation_info
                        for other in self.transitive_requirements
                    ]

                    for add_req in additional_requirements:
                        add_things, add_disjoints = add_req.representation_info
                        used = False  # For early breaking if we use the additional req
                        for i, (base_things, base_disjoints) in enumerate(base_infos):
                            if self.candidate_is_as_or_more_specific_than(
                                add_things, base_disjoints, base_things
                            ):
                                requirements[i] = add_req  # Overwrite the thing you're
                                # more specific than
                                used = True
                                break
                        if used:
                            continue

                        for trans_things, trans_disjoints in transitive_infos:
                            # If you haven't found the additional requirement yet,
                            # check if it's in the allowed transitive requirements
                            if compatible_classes(
                                add_things,
                                add_disjoints,
                                trans_things,
                                trans_disjoints,
                            ):
                                requirements.append(add_req)
                                break
                    return requirements

                @staticmethod
                def candidate_is_as_or_more_specific_than(
                    candidate_things, ref_disjoints, ref_things
                ) -> bool:
                    not_disjoint = (
                        len(ref_disjoints.intersection(candidate_things)) == 0
                    )
                    return not_disjoint and set(ref_things).issubset(candidate_things)

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

        def compatible_classes(
            things1: list[owl.ThingClass],
            disjoints1: set[owl.ThingClass],
            things2: list[owl.ThingClass],
            disjoints2: set[owl.ThingClass],
        ):
            """
            Given the `is_a` and disjoint classes of two individuals, checks whether
            they are compatible -- i.e. whether the classes of one are in the disjoints
            of the other (which would lead to incompatibility).

            Args:
                things1 (list[owl.ThingClass]): Classes of the first indivual.
                disjoints1 (set[owl.ThingClass]): Disjoints of the first individual.
                things2 (list[owl.ThingClass]): Classes of the second individual.
                disjoints2 (set[owl.ThingClass]):

            Returns:
                (bool): Whether any classes of one individual are in the disjoints of
                    the other.
            """
            # Put 0 first so we can skip the second evaluation when the first fails
            return (
                0
                == len(disjoints1.intersection(things2))
                == len(disjoints2.intersection(things1))
            )

        def get_disjoints_set(classes: list[owl.ThingClass]):
            """
            For a list of things, get the set of all the things they're disjoint
            to
            """
            disjoints = []
            for thing in classes:
                if thing == owl.Thing:
                    continue
                try:
                    entities = list(next(thing.disjoints()).entities)
                    # The entities are the actual classes that are disjoint
                    # The entities for each of the disjoints are ideantical,
                    # so we can just use `next` to grab the first one
                    entities.remove(thing)
                    # The entities of our disjoint include us, so remove us
                    disjoints += entities
                except StopIteration:
                    # If the disjoints are empty, just continue
                    continue
            return set(disjoints)

        def build_tree(
            parameter, parent=None, additional_requirements=None
        ) -> NodeTree:
            node = NodeTree(parameter, parent=parent)

            if isinstance(parameter, Input):
                (
                    sources,
                    additional_requirements,
                ) = parameter.get_sources_and_passed_requirements(
                    additional_requirements=additional_requirements
                )  # Snag the accepted transitive requirements as well
            else:
                sources = parameter.get_sources(
                    additional_requirements=additional_requirements
                )

            for source in sources:
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
