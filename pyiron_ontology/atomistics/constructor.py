# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building the atomistics ontology from python classes.
"""

from __future__ import annotations

from pyiron_ontology.constructor import Constructor

import owlready2 as owl


class AtomisticsOntology(Constructor):
    def __init__(
        self, name: str = "atomistics", closed: bool = True, strict: bool = False
    ):
        super().__init__(name=name, closed=closed, strict=strict)

    def _make_specific_declarations(self):
        onto = self.onto
        with onto:
            class UserInput(onto.Generic): pass

            class PyironObject(onto.Generic): pass
            class PhysicalProperty(onto.Generic): pass  # Add units, etc
            owl.AllDisjoint([PyironObject, PhysicalProperty])
            class ChemicalElement(PhysicalProperty): pass
            class MaterialProperty(PhysicalProperty): pass
            class BulkModulus(MaterialProperty): pass
            class BPrime(MaterialProperty): pass

            class Dimensional(onto.Generic): pass
            class OneD(Dimensional): pass
            class TwoD(Dimensional): pass
            class ThreeD(Dimensional): pass
            owl.AllDisjoint([OneD, TwoD, ThreeD])

            class Structure(PyironObject, Dimensional): pass
            class Defected(Structure): pass
            class HasDislocation(Defected): pass
            class HasVacancy(Defected): pass
            class HasInterface(Defected): pass
            class HasGB(HasInterface): pass
            class HasSurface(HasInterface): pass
            class HasPB(HasInterface): pass
            class Bulk(Structure): pass
            # equivalent_to = [Structure & owl.Not(Defected)]
            owl.AllDisjoint([Bulk, Defected])  # Not even needed given Bulk definition
            owl.AllDisjoint([OneD, HasGB])
            owl.AllDisjoint([OneD, HasDislocation])

            class PyironProject(PyironObject): pass
            class AtomisticsProject(PyironProject): pass

            class PyironJob(PyironObject): pass
            class AtomisticsJob(PyironJob): pass
            class Lammps(AtomisticsJob): pass
            class Vasp(AtomisticsJob): pass
            owl.AllDisjoint([Structure, PyironProject, PyironJob])

        bulk_structure_node = onto.Function(name="bulk_structure_node")
        bulk_structure_node_input_element = onto.Input(
            optional_input_of=bulk_structure_node,
            name=f"{bulk_structure_node.name}_input_element",
            generic=onto.Generic(is_a=[onto.ChemicalElement, onto.UserInput])
        )
        bulk_structure_node_output_structure = onto.Output(
            output_of=bulk_structure_node,
            name=f"{bulk_structure_node.name}_output_structure",
            generic=onto.Structure(is_a=[onto.Bulk, onto.ThreeD]),
        )

        surface_structure_node = onto.Function("surface_structure_node")
        surface_structure_node_input_element = onto.Input(
            optional_input_of=surface_structure_node,
            name=f"{surface_structure_node.name}_input_element",
            generic=onto.Generic(is_a=[onto.ChemicalElement, onto.UserInput])
        )
        surface_structure_node_output_structure = onto.Output(
            output_of=surface_structure_node,
            name=f"{surface_structure_node.name}_output_structure",
            generic=onto.Structure(is_a=[onto.HasSurface, onto.ThreeD]),
        )

        lammps_node = onto.Function("lammps_node")
        lammps_node_input_structure = onto.Input(
            mandatory_input_of=lammps_node,
            name=f"{lammps_node.name}_input_structure",
            generic=onto.Structure()
        )
        lammps_node_output_job = onto.Output(
            output_of=lammps_node,
            name=f"{lammps_node.name}_output_job",
            generic=onto.Lammps()
        )

        vasp_node = onto.Function("vasp_node")
        vasp_node_input_structure = onto.Input(
            mandatory_input_of=vasp_node,
            name=f"{vasp_node.name}_input_structure",
            generic=onto.Structure(is_a=[onto.ThreeD])
        )
        vasp_node_output_job = onto.Output(
            output_of=vasp_node,
            name=f"{vasp_node.name}_output_job",
            generic=onto.Vasp()
        )

        murnaghan_node = onto.Function("murnaghan_node", )
        murnaghan_node_input_project = onto.Input(
            name=f"{murnaghan_node.name}_input_project",
            generic=onto.AtomisticsProject(),
            mandatory_input_of=murnaghan_node,
        )
        murnaghan_node_input_job = onto.Input(
            name=f"{murnaghan_node.name}_input_job",
            generic=onto.AtomisticsJob(),
            mandatory_input_of=murnaghan_node,
            requirements=[onto.Structure(is_a=[onto.Bulk, onto.ThreeD])]
        )
        murnaghan_node_output_bulk_modulus = onto.Output(
            name=f"{murnaghan_node.name}_output_bulk_modulus",
            generic=onto.BulkModulus(),
            output_of=murnaghan_node,
        )
        murnaghan_node_output_b_prime = onto.Output(
            name=f"{murnaghan_node.name}_output_b_prime",
            generic=onto.BPrime(),
            output_of=murnaghan_node,
        )
