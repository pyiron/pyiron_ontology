# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building the atomistics ontology from python classes.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pandas as pd
import pint

from pyiron_ontology.atomistics.constructor import is_subset

if TYPE_CHECKING:
    import pyiron_atomistics

    from pyiron_ontology import atomistics_onto as onto

UREG = pint.UnitRegistry()


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
        tabs = "".join(["\t"] * depth)
        print(f"{tabs}{self.value}")
        for child in self.children:
            child.render(depth=depth + 1)


class AtomisticsReasoner:
    def __init__(self, ontology):
        self.onto = ontology

    def _get_triples_for_generic(self, parameter: onto.GenericParameter):
        triples: list[
            tuple[onto.OutputParameter, onto.Executable, list[onto.InputParameter]]
        ] = []
        sources = self.get_sources(parameter)
        for source in sources:
            target_output = [
                s for s in source.output if parameter in s.generic_parameter
            ]
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
            tuple[onto.OutputParameter, onto.Executable, list[onto.InputParameter]]
        ] = []
        outputs = self.gives_consistent_output(
            parameter, parameter.has_transitive_conditions
        )
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
        return [
            source
            for specific in parameter.has_parameters
            for source in specific.output_of
        ]

    def build_tree(self, thing, parent=None):
        triples = self.get_triples(thing)
        node = None
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
        conditions = (
            thing.has_conditions
            if additional_conditions is None
            else additional_conditions
        )

        if len(conditions) > 0:
            return [
                p
                for p in thing.generic_parameter[0].has_parameters
                if is_subset(conditions, p.has_options)
            ]
        else:
            return thing.generic_parameter[0].has_parameters

    @staticmethod
    def _get_ref_job(job):
        ref_job_name = list(set(job.project_hdf5.list_groups()) - {"input", "output"})
        if len(ref_job_name) == 1:
            return ref_job_name[0]

    def _get_job_type(self, job):
        ref_job_name = self._get_ref_job(job)
        if ref_job_name is not None:
            return job[f"{ref_job_name}/TYPE"].split(".")[-1][:-2]
        else:
            return job["TYPE"]

    @staticmethod
    def _alloy_sql(el):
        """Convert to SQL search string"""
        if el is None:
            return "%"
        return f"%{el}%"

    @staticmethod
    def convert_unit(my_parameter):
        if hasattr(my_parameter, "unit"):
            source_unit = my_parameter.unit
            if len(source_unit) == 1:
                target_unit = my_parameter.generic_parameter[0].unit[0]
                if source_unit[0] != target_unit:
                    return UREG(source_unit[0]).to(target_unit).magnitude
            elif len(source_unit) > 1:
                raise ValueError(f"Multiple units not supported -- got {source_unit}")
        return 1

    def search_database_for_property(
        self,
        my_property: onto.GenericParameter,
        project: pyiron_atomistics.Project,
        select_alloy: Optional[str] = None,
    ):
        """
        Use the pyiron database to search for instances of an ontological generic
        parameter. Optionally filter by the chemistry of the job.

        Args:
            my_property:
            project:
            select_alloy:

        Returns:

        """
        specific_property = my_property.has_parameters[0]
        property_hdf_path = "/".join(specific_property.name.split("/")[1:])

        pd_header = [
            "Chemical Formula",
            f"{my_property.name} [{my_property.unit[0]}]",
            "Engine",
        ]
        pd_dic = {k: [] for k in pd_header}

        df_murn = pd.DataFrame(
            project.db.get_items_dict(
                {
                    "hamilton": specific_property.output_of[0].name,
                    "chemicalformula": self._alloy_sql(select_alloy),
                    "project": f"%{project.path}%",
                }
            )
        )

        for _, row in df_murn.iterrows():
            job_hdf = project.inspect(row.id)
            pd_dic["Chemical Formula"].append(row.chemicalformula)
            cv = self.convert_unit(specific_property)
            output_property = job_hdf[property_hdf_path]
            value = cv * output_property if output_property is not None else None
            pd_dic[pd_header[1]].append(value)
            pd_dic["Engine"].append(self._get_job_type(job_hdf))
        return pd.DataFrame(pd_dic)
