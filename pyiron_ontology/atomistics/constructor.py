# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building the atomistics ontology from python classes.
"""

from __future__ import annotations

from pyiron_ontology.constructor import Constructor


class AtomisticsOntology(Constructor):
    def __init__(
        self, name: str = "atomistics", closed: bool = True, strict: bool = False
    ):
        super().__init__(name=name, closed=closed, strict=strict)

    def _declare_individuals(self, onto):
        lblAtomistic = onto.Label(name="Atomistic")
        lblCode = onto.Label(name="lCode")
        lblDFT = onto.Label(name="DFT")
        lblMaterialProperty = onto.Label(name="MaterialProperty")
        lblPeriodicBoundaryConditions = onto.Label(name="PeriodicBoundaryConditions")
        lblUserInput = onto.Label(
            name="UserInput",
            comment="Easy to provide input. Can be used to start a workflow",
        )
        lblBulk3DCrystal = onto.Label(
            name="Bulk3dStructure",
            comment="Bulk 3d structure generated/needed. Has a well defined volume.",
        )
        lblAtomisticEnergyCalculator = onto.Label(
            name="AtomisticEnergyCalculator",
            comment="Code to compute the energy of an atomic structure",
        )

        ChemicalElement = onto.GenericParameter(
            name="ChemicalElement",
            description="Single chemical element",
            domain=[lblAtomistic, lblUserInput],
        )
        AtomicStructure = onto.GenericParameter(
            name="AtomicStructure",
            description="Contains all information to construct an atomic structure (molecule, crystal, etc.)",
            domain=[lblAtomistic],
        )
        Executable = onto.GenericParameter(
            name="Executable",
            description="Code that requires input and produces output",
            domain=[],
        )
        Flag = onto.GenericParameter(
            name="Flag",
            description="Input that selects a choice for a particular code",
            domain=[lblUserInput],
        )

        # Structure
        CreateStructureBulk = onto.Code(
            name="CreateStructureBulk",
            domain=[lblAtomistic, lblCode],
            generic_parameter=[Executable],
        )
        CreateStructureBulk_element = onto.InputParameter(
            name=f"{CreateStructureBulk.name}/input/element",
            mandatory_input_in=[CreateStructureBulk],
            generic_parameter=[ChemicalElement],
        )
        CreateStructureBulk_structure = onto.OutputParameter(
            name=f"{CreateStructureBulk.name}/output/structure",
            output_of=[CreateStructureBulk],
            generic_parameter=[AtomicStructure],
            has_options=[lblBulk3DCrystal],
        )

        CreateSurface = onto.Code(
            name="CreateSurface",
            domain=[lblAtomistic, lblCode],
            generic_parameter=[Executable],
        )
        CreateSurface_element = onto.InputParameter(
            name=f"{CreateSurface.name}/input/element",
            mandatory_input_in=[CreateSurface],
            generic_parameter=[ChemicalElement],
        )
        CreateSurface_structure = onto.OutputParameter(
            name=f"{CreateSurface.name}/output/structure",
            output_of=[CreateSurface],
            generic_parameter=[AtomicStructure],
            has_options=[],
        )

        # Murnaghan
        Bulkmodulus = onto.GenericParameter(
            name="Bulk_modulus",
            description="https://en.wikipedia.org/wiki/Bulk_modulus",
            symbols=["B", "K"],
            unit=["MPa"],
            domain=[lblMaterialProperty],
        )
        Bprime = onto.GenericParameter(
            name="B_prime",
            decription="First derivative of Bulk modulus with respect to volume",
            symbols=["Bprime"],
            unit=["1"],
            domain=[lblMaterialProperty],
        )

        Murnaghan = onto.Code(
            name="Murnaghan",
            domain=[lblAtomistic, lblCode],
            generic_parameter=[Executable],
        )
        Murnaghan_Bulkmodulus = onto.OutputParameter(
            name=f"{Murnaghan.name}/output/equilibrium_bulk_modulus",
            output_of=[Murnaghan],
            generic_parameter=[Bulkmodulus],
            unit=["GPa"],
        )
        Murnaghan_Bprime = onto.OutputParameter(
            name=f"{Murnaghan.name}/output/equilibrium_b_prime",
            output_of=[Murnaghan],
            generic_parameter=[Bprime],
        )
        Murnaghan_Ref_Job = onto.InputParameter(
            name=f"{Murnaghan.name}/ref_job",
            mandatory_input_in=[Murnaghan],
            generic_parameter=[Executable],
            has_conditions=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
        )

        # DFT
        EnergyCutoff = onto.GenericParameter(
            name="EnergyCutoff",
            description="The cutoff on the number of plane wave functions being utilized as basis functions to represent the wavefunction",
        )

        VASP = onto.Code(
            name="VASP",
            domain=[lblAtomistic, lblCode, lblDFT],
            has_options=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
            generic_parameter=[Executable],
        )
        VASP_ENCUT = onto.InputParameter(
            name="ENCUT",
            input_in=[VASP],
            generic_parameter=[EnergyCutoff],
            unit=["eV"],
        )
        VASP_IBRION = onto.InputParameter(
            name="IBRION",
            generic_parameter=[Flag],
            input_in=[VASP],
        )
        VASP_Structure = onto.InputParameter(
            name=f"{VASP.name}/input/structure",
            mandatory_input_in=[VASP],
            generic_parameter=[AtomicStructure],
            has_transitive_conditions=[lblBulk3DCrystal],
        )

        VASP_ETOT = onto.OutputParameter(name="ETOT", output_of=[VASP])

        # LAMMPS

        LAMMPS = onto.Code(
            name="LAMMPS",
            domain=[lblAtomistic, lblCode],
            has_options=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
            generic_parameter=[Executable],
        )

        LAMMPS_Structure = onto.InputParameter(
            name=f"{LAMMPS.name}/input/structure",
            mandatory_input_in=[LAMMPS],
            generic_parameter=[AtomicStructure],
            has_transitive_conditions=[lblBulk3DCrystal],
        )

        LAMMPS_ETOT = onto.OutputParameter(name="ETOT", output_of=[LAMMPS])
