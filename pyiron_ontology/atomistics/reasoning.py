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

if TYPE_CHECKING:
    import pyiron_atomistics

    from pyiron_ontology import atomistics_onto as onto

UREG = pint.UnitRegistry()


class AtomisticsReasoner:
    def __init__(self, ontology):
        self.onto = ontology

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
