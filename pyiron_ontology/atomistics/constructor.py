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
        Generic = self.onto.Generic
        Input = self.onto.Input
        Output = self.onto.Output

        with self.onto:

            class AtomisticsFunction(self.onto.Function):
                pass

            class has_pyiron_name(AtomisticsFunction >> str, owl.FunctionalProperty):
                python_name = "pyiron_name"

            Function = AtomisticsFunction

            class UserInput(Generic):
                pass

            class PyironObject(Generic):
                pass

            class PhysicalProperty(Generic):
                pass  # Add units, etc

            owl.AllDisjoint([PyironObject, PhysicalProperty])

            class Energy(PhysicalProperty):
                pass

            class Force(PhysicalProperty):
                pass

            class ChemicalElement(PhysicalProperty):
                pass

            owl.AllDisjoint([Energy, Force, ChemicalElement])

            class MaterialProperty(PhysicalProperty):
                pass

            class BulkModulus(MaterialProperty):
                pass

            class BPrime(MaterialProperty):
                pass

            class SurfaceEnergy(MaterialProperty):
                pass

            owl.AllDisjoint([BulkModulus, BPrime, SurfaceEnergy])

            class Dimensional(Generic):
                pass

            class OneD(Dimensional):
                pass

            class TwoD(Dimensional):
                pass

            class ThreeD(Dimensional):
                pass

            owl.AllDisjoint([OneD, TwoD, ThreeD])

            class Structure(PyironObject, Dimensional):
                pass

            class Defected(Structure):
                pass

            class HasDislocation(Defected):
                pass

            class HasVacancy(Defected):
                pass

            class HasInterface(Defected):
                pass

            class HasGB(HasInterface):
                pass

            class HasSurface(HasInterface):
                pass

            class HasPB(HasInterface):
                pass

            class Bulk(Structure):
                equivalent_to = [Structure & owl.Not(Defected)]

            # equivalent_to = [Structure & owl.Not(Defected)]
            owl.AllDisjoint([Bulk, Defected])  # Not even needed given Bulk definition
            owl.AllDisjoint([OneD, HasGB])
            owl.AllDisjoint([OneD, HasDislocation])

            class PyironProject(PyironObject):
                pass

            class AtomisticsProject(PyironProject):
                pass

            class PyironJob(PyironObject):
                pass

            class AtomisticsJob(PyironJob):
                pass

            class Lammps(AtomisticsJob):
                pass

            class Vasp(AtomisticsJob):
                pass

            owl.AllDisjoint([Structure, PyironProject, PyironJob])

            project = Function(name="project")
            project_input_name = Input(
                optional_input_of=project,
                name=f"{project.name}_input_name",
                generic=UserInput(),
            )
            project_output_atomistics_project = Output(
                output_of=project,
                name=f"{project.name}_output_atomistics_project",
                generic=AtomisticsProject(),
            )

            bulk_structure = Function(name="bulk_structure")
            bulk_structure_input_element = Input(
                optional_input_of=bulk_structure,
                name=f"{bulk_structure.name}_input_element",
                generic=Generic(is_a=[ChemicalElement, UserInput]),
                hdf_path="input/element",
            )
            bulk_structure_output_structure = Output(
                output_of=bulk_structure,
                name=f"{bulk_structure.name}_output_structure",
                generic=Structure(is_a=[Bulk, ThreeD]),
                hdf_path="output/structure",
            )

            surface_structure = Function("surface_structure")
            surface_structure_input_element = Input(
                optional_input_of=surface_structure,
                name=f"{surface_structure.name}_input_element",
                generic=Generic(is_a=[ChemicalElement, UserInput]),
                hdf_path="input/element",
            )
            surface_structure_output_structure = Output(
                output_of=surface_structure,
                name=f"{surface_structure.name}_output_structure",
                generic=Structure(is_a=[HasSurface, ThreeD]),
                hdf_path="output/structure",
            )

            lammps = Function("lammps", pyiron_name="Lammps")
            lammps_input_project = Input(
                name=f"{lammps.name}_input_project",
                generic=AtomisticsProject(),
                mandatory_input_of=lammps,
            )
            lammps_input_structure = Input(
                mandatory_input_of=lammps,
                name=f"{lammps.name}_input_structure",
                generic=Structure(),
                hdf_path="input/structure",
            )
            lammps_output_job = Output(
                output_of=lammps, name=f"{lammps.name}_output_job", generic=Lammps()
            )

            vasp = Function("vasp", pyiron_name="Vasp")
            vasp_input_project = Input(
                name=f"{vasp.name}_input_project",
                generic=AtomisticsProject(),
                mandatory_input_of=vasp,
            )
            vasp_input_structure = Input(
                mandatory_input_of=vasp,
                name=f"{vasp.name}_input_structure",
                generic=Generic(is_a=[Structure, ThreeD]),
                # Can't be onto.Structure(is_a=[onto.ThreeD]) because is_a _overrides_ the
                # instantiated class, and ThreeD is not a child of Structure!
                hdf_path="input/structure",
            )
            vasp_output_job = Output(
                output_of=vasp, name=f"{vasp.name}_output_job", generic=Vasp()
            )

            atomistic_taker = Function("atomistic_taker")
            atomistic_taker_job = Input(
                name="atomistic_taker_job",
                generic=AtomisticsJob(),
                mandatory_input_of=atomistic_taker,
                transitive_requirements=[Structure()],
            )
            atomistic_taker_output_energy_pot = Output(
                name="atomistic_taker_output_energy_pot",
                generic=Energy(),
                output_of=atomistic_taker,
            )
            atomistic_taker_output_forces = Output(
                name="atomistic_taker_output_forces",
                generic=Force(),
                output_of=atomistic_taker,
            )

            murnaghan = Function("murnaghan", pyiron_name="Murnaghan")
            murnaghan_input_project = Input(
                name=f"{murnaghan.name}_input_project",
                generic=AtomisticsProject(),
                mandatory_input_of=murnaghan,
            )
            murnaghan_input_job = Input(
                name=f"{murnaghan.name}_input_job",
                generic=AtomisticsJob(),
                mandatory_input_of=murnaghan,
                requirements=[Structure(is_a=[Bulk, ThreeD])],
                hdf_path="ref_job",
            )
            murnaghan_output_bulk_modulus = Output(
                name=f"{murnaghan.name}_output_bulk_modulus",
                generic=BulkModulus(),
                output_of=murnaghan,
                hdf_path="output/equilibrium_bulk_modulus",
                unit="GPa",
            )
            murnaghan_output_b_prime = Output(
                name=f"{murnaghan.name}_output_b_prime",
                generic=BPrime(),
                output_of=murnaghan,
                hdf_path="output/equilibrium_b_prime",
            )

            surface_energy = Function("surface_energy")
            surface_energy_input_bulk_structure = Input(
                name="surface_energy_input_bulk_structure",
                generic=Structure(is_a=[Bulk, ThreeD]),
                mandatory_input_of=surface_energy,
            )
            surface_energy_input_bulk_energy = Input(
                name="surface_energy_input_bulk_energy",
                generic=Energy(),
                mandatory_input_of=surface_energy,
                requirements=[Structure(is_a=[Bulk, ThreeD])],
            )
            surface_energy_input_slab_structure = Input(
                name="surface_energy_input_slab_structure",
                generic=Structure(is_a=[HasSurface, ThreeD]),
                mandatory_input_of=surface_energy,
            )
            surface_energy_input_slab_energy = Input(
                name="surface_energy_input_slab_energy",
                generic=Energy(),
                mandatory_input_of=surface_energy,
                requirements=[Structure(is_a=[HasSurface, ThreeD])],
            )
            surface_energy_output_surface_energy = Output(
                name=f"{surface_energy.name}_output_surface_energy",
                generic=SurfaceEnergy(),
                output_of=surface_energy,
            )
