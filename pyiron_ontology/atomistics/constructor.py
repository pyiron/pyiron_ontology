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
            class Bulk(Structure):
                equivalent_to = [Structure & owl.Not(Defected)]
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

            project = onto.Function(name="project")
            project_input_name = onto.Input(
                optional_input_of=project,
                name=f"{project.name}_input_name",
                generic=UserInput,
            )
            project_output_atomistics_project = onto.Output(
                output_of=project,
                name=f"{project.name}_output_atomistics_project",
                generic=AtomisticsProject,
            )

            bulk_structure = onto.Function(name="bulk_structure")
            bulk_structure_input_element = onto.Input(
                optional_input_of=bulk_structure,
                name=f"{bulk_structure.name}_input_element",
                generic=onto.Generic(is_a=[ChemicalElement, UserInput])
            )
            bulk_structure_output_structure = onto.Output(
                output_of=bulk_structure,
                name=f"{bulk_structure.name}_output_structure",
                generic=onto.Structure(is_a=[Bulk, ThreeD]),
            )

            surface_structure = onto.Function("surface_structure")
            surface_structure_input_element = onto.Input(
                optional_input_of=surface_structure,
                name=f"{surface_structure.name}_input_element",
                generic=onto.Generic(is_a=[ChemicalElement, UserInput])
            )
            surface_structure_output_structure = onto.Output(
                output_of=surface_structure,
                name=f"{surface_structure.name}_output_structure",
                generic=Structure(is_a=[HasSurface, ThreeD]),
            )

            lammps = onto.Function("lammps")
            lammps_input_structure = onto.Input(
                mandatory_input_of=lammps,
                name=f"{lammps.name}_input_structure",
                generic=Structure()
            )
            lammps_output_job = onto.Output(
                output_of=lammps,
                name=f"{lammps.name}_output_job",
                generic=Lammps()
            )

            vasp = onto.Function("vasp")
            vasp_input_structure = onto.Input(
                mandatory_input_of=vasp,
                name=f"{vasp.name}_input_structure",
                generic=onto.Generic(is_a=[Structure, ThreeD])
                # Can't be onto.Structure(is_a=[onto.ThreeD]) because is_a _overrides_ the
                # instantiated class, and ThreeD is not a child of Structure!
            )
            vasp_output_job = onto.Output(
                output_of=vasp,
                name=f"{vasp.name}_output_job",
                generic=Vasp()
            )

            murnaghan = onto.Function("murnaghan", )
            murnaghan_input_project = onto.Input(
                name=f"{murnaghan.name}_input_project",
                generic=AtomisticsProject(),
                mandatory_input_of=murnaghan,
            )
            murnaghan_input_job = onto.Input(
                name=f"{murnaghan.name}_input_job",
                generic=AtomisticsJob(),
                mandatory_input_of=murnaghan,
                requirements=[Structure(is_a=[Bulk, ThreeD])]
            )
            murnaghan_output_bulk_modulus = onto.Output(
                name=f"{murnaghan.name}_output_bulk_modulus",
                generic=BulkModulus(),
                output_of=murnaghan,
            )
            murnaghan_output_b_prime = onto.Output(
                name=f"{murnaghan.name}_output_b_prime",
                generic=BPrime(),
                output_of=murnaghan,
            )
