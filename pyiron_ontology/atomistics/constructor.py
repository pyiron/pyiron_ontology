# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building the atomistics ontology from python classes.
"""

import numpy as np
import owlready2 as owl
import pandas


def is_subset(a, b):
    return np.all([aa in b for aa in a])


class AtomisticsOntology:
    def __init__(self, filename: str = "pyiron_atomistics"):
        onto = owl.get_ontology(f"file://{filename}.owl")
        self._declare_classes(onto)
        df = self._generate_df(onto)
        self._declare_more_individuals(onto, df)
        # TODO: Introduce a "from_csv" option for constructing, and leverage
        #       `all_classes=False` in `declare_classes`?

        owl.close_world(onto.PyObject)
        with onto:
            owl.sync_reasoner_pellet(
                infer_property_values=True, infer_data_property_values=True, debug=0
            )

        self.onto = onto
        self.df = df

    def save(self):
        self.onto.save()

    def _declare_classes(self, onto, all_classes=True):
        with onto:

            class PyObject(owl.Thing):
                comment = "my pyiron object"

            class Parameter(PyObject):
                @property
                def description(self):
                    if len(self.generic_parameter) > 0:
                        return self.generic_parameter[0].description

            class InputParameter(Parameter):
                # @property
                def consistent_output(self, additional_conditions=None):
                    if additional_conditions is None:
                        conditions = self.has_conditions
                    else:
                        conditions = additional_conditions
                    if len(conditions) > 0:
                        return [
                            p
                            for p in self.generic_parameter[0].has_parameters
                            if is_subset(conditions, p.has_options)
                        ]
                    return self.generic_parameter[0].has_parameters

            # class MandatoryInputParameter(InputParameter): pass

            class OutputParameter(Parameter):
                pass

            class GenericParameter(Parameter):
                description = ""

            class Code(Parameter):
                pass

            class Label(PyObject):
                pass

            class has_conditions(Parameter >> Label):
                pass

            class has_transitive_conditions(Parameter >> Label):
                pass  # condition to fulfill to fulfill option in code

            class has_options(Parameter >> Label):
                pass

            class has_transitive_objects(Label >> Parameter):
                inverse_property = has_transitive_conditions

            class has_conditional_objects(Label >> Parameter):
                inverse_property = has_conditions

            class has_optional_objects(Label >> Parameter):
                inverse_property = has_options

            class has_symbol(GenericParameter >> str):
                class_property_type = ["some"]
                python_name = "symbols"

            class has_unit(Parameter >> str):
                class_property_type = ["some"]
                python_name = "unit"

            class is_in_domains(Parameter >> Label):
                class_property_type = ["some"]
                python_name = "domain"

            class domain_has_codes(Label >> Parameter):
                python_name = "has_objects"
                inverse_property = is_in_domains

            class has_generic_parameter(Parameter >> GenericParameter):
                class_property_type = ["some"]
                python_name = "generic_parameter"

            class generic_parameter_has(GenericParameter >> Parameter):
                python_name = "has_parameters"
                inverse_property = has_generic_parameter

            class is_input_of(InputParameter >> Code):
                class_property_type = ["some"]
                python_name = "input_in"

            class has_input(Code >> InputParameter):
                python_name = "input"
                inverse_property = is_input_of

            class is_mandatory_input_of(InputParameter >> Code):
                class_property_type = ["some"]
                python_name = "mandatory_input_in"

            class has_mandatory_input(Code >> InputParameter):
                python_name = "mandatory_input"
                inverse_property = is_mandatory_input_of

            class is_output_of(OutputParameter >> Code):
                class_property_type = ["some"]
                python_name = "output_of"  # python name has to be unique (even for different class)

            class has_output(Code >> OutputParameter):
                python_name = "output"
                inverse_property = is_output_of

            owl.AllDisjoint([InputParameter, OutputParameter, Label])

        if all_classes:
            lblAtomistic = Label(name="Atomistic")
            lblCode = Label(name="lCode")
            lblDFT = Label(name="DFT")
            lblMaterialProperty = Label(name="MaterialProperty")
            lblPeriodicBoundaryConditions = Label(name="PeriodicBoundaryConditions")
            lblUserInput = Label(
                name="UserInput",
                comment="Easy to provide input. Can be used to start a workflow",
            )
            lblBulk3DCrystal = Label(
                name="Bulk3dStructure",
                comment="Bulk 3d structure generated/needed. Has a well defined volume.",
            )
            lblAtomisticEnergyCalculator = Label(
                name="AtomisticEnergyCalculator",
                comment="Code to compute the energy of an atomic structure",
            )

            ChemicalElement = GenericParameter(
                name="ChemicalElement",
                description="Single chemical element",
                domain=[lblAtomistic, lblUserInput],
            )
            AtomicStructure = GenericParameter(
                name="AtomicStructure",
                description="Contains all information to construct an atomic structure (molecule, crystal, etc.)",
                domain=[lblAtomistic],
            )
            Executable = GenericParameter(
                name="Executable",
                description="Code that requires input and produces output",
                domain=[],
            )

            # Structure
            CreateStructureBulk = Code(
                name="CreateStructureBulk",
                domain=[lblAtomistic, lblCode],
                generic_parameter=[Executable],
            )
            CreateStructureBulk_element = InputParameter(
                name=f"{CreateStructureBulk.name}/input/element",
                mandatory_input_in=[CreateStructureBulk],
                generic_parameter=[ChemicalElement],
            )
            CreateStructureBulk_structure = OutputParameter(
                name=f"{CreateStructureBulk.name}/output/structure",
                output_of=[CreateStructureBulk],
                generic_parameter=[AtomicStructure],
                has_options=[lblBulk3DCrystal],
            )

            CreateSurface = Code(
                name="CreateSurface",
                domain=[lblAtomistic, lblCode],
                generic_parameter=[Executable],
            )
            CreateSurface_element = InputParameter(
                name=f"{CreateSurface.name}/input/element",
                mandatory_input_in=[CreateSurface],
                generic_parameter=[ChemicalElement],
            )
            CreateSurface_structure = OutputParameter(
                name=f"{CreateSurface.name}/output/structure",
                output_of=[CreateSurface],
                generic_parameter=[AtomicStructure],
                has_options=[],
            )

            # Murnaghan
            Bulkmodulus = GenericParameter(
                name="Bulk_modulus",
                description="https://en.wikipedia.org/wiki/Bulk_modulus",
                symbols=["B", "K"],
                unit=["MPa"],
                domain=[lblMaterialProperty],
            )
            Bprime = GenericParameter(
                name="B_prime",
                decription="First derivative of Bulk modulus with respect to volume",
                symbols=["Bprime"],
                unit=["1"],
                domain=[lblMaterialProperty],
            )

            Murnaghan = Code(
                name="Murnaghan",
                domain=[lblAtomistic, lblCode],
                generic_parameter=[Executable],
            )
            Murnaghan_Bulkmodulus = OutputParameter(
                name=f"{Murnaghan.name}/output/equilibrium_bulk_modulus",
                output_of=[Murnaghan],
                generic_parameter=[Bulkmodulus],
                unit=["GPa"],
            )
            Murnaghan_Bprime = OutputParameter(
                name=f"{Murnaghan.name}/output/equilibrium_b_prime",
                output_of=[Murnaghan],
                generic_parameter=[Bprime],
            )
            Murnaghan_Ref_Job = InputParameter(
                name=f"{Murnaghan.name}/ref_job",
                mandatory_input_in=[Murnaghan],
                generic_parameter=[Executable],
                has_conditions=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
            )

            # DFT
            EnergyCutoff = GenericParameter(
                name="EnergyCutoff",
                description="The cutoff on the number of plane wave functions being utilized as basis functions to represent the wavefunction",
            )

            VASP = Code(
                name="VASP",
                domain=[lblAtomistic, lblCode, lblDFT],
                has_options=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
                generic_parameter=[Executable],
            )
            VASP_ENCUT = InputParameter(
                name="ENCUT",
                input_in=[VASP],
                generic_parameter=[EnergyCutoff],
                unit=["eV"],
            )
            VASP_IBRAV = InputParameter(name="IBRAV", input_in=[VASP])
            VASP_Structure = InputParameter(
                name=f"{VASP.name}/input/structure",
                mandatory_input_in=[VASP],
                generic_parameter=[AtomicStructure],
                has_transitive_conditions=[lblBulk3DCrystal],
            )

            VASP_ETOT = OutputParameter(name="ETOT", output_of=[VASP])

            # LAMMPS

            LAMMPS = Code(
                name="LAMMPS",
                domain=[lblAtomistic, lblCode],
                has_options=[lblBulk3DCrystal, lblAtomisticEnergyCalculator],
                generic_parameter=[Executable],
            )

            LAMMPS_Structure = InputParameter(
                name=f"{LAMMPS.name}/input/structure",
                mandatory_input_in=[LAMMPS],
                generic_parameter=[AtomicStructure],
                has_transitive_conditions=[lblBulk3DCrystal],
            )

            LAMMPS_ETOT = OutputParameter(name="ETOT", output_of=[LAMMPS])

    def _generate_df(self, onto):
        inverse_list = [
            "has_objects",
            "has_transitive_objects",
            "has_conditional_objects",
            "has_optional_objects",
            "has_parameters",
            "output",
            "mandatory_input",
            "input",
        ]

        obj_lst = []
        individuals = list(onto.individuals())
        for i in individuals:
            obj_dict = {}
            # print (i.is_instance_of[0], i.name)
            obj_dict["class"] = i.is_instance_of[0].name
            obj_dict["name"] = i.name
            for p in list(i.get_properties()):
                if p.python_name in inverse_list:
                    continue
                # print ("   ", p.python_name, getattr(i, p.python_name))
                new_item_lst = []
                item_lst = getattr(i, p.python_name)
                for item in item_lst:
                    if hasattr(item, "name"):
                        new_item_lst.append(item.name)
                    else:
                        new_item_lst.append(item)

                obj_dict[p.python_name] = new_item_lst
            obj_lst.append(obj_dict)
        df = pandas.DataFrame(obj_lst)

        sorter = [
            "Label",
            "GenericParameter",
            "Code",
            "InputParameter",
            "OutputParameter",
        ]
        df["class"] = pandas.Categorical(df["class"], sorter)
        df = df.sort_values(by="class")
        df = df.reset_index(drop=True)
        return df

    def _get_args(self, i_0, df, onto):
        non_ontology_keys = ["symbols", "unit"]
        qwargs = {}
        # print ('class: ', df.iloc[i_0]['class'])
        for key in df.keys():
            if key in ["class"]:
                continue
            val = df.iloc[i_0][key]
            if val is not np.nan:
                # print (key, val)
                if isinstance(val, str):
                    val = val.strip()
                    if key == "comment":
                        val = val[2:-2]
                    # print (key, val)
                    if len(val) == 0:
                        continue
                    elif val[0] == "[":  # list
                        val_lst = eval(val)
                        if key not in non_ontology_keys:
                            val_lst = [onto[d.strip()] for d in val_lst]
                        qwargs[key] = val_lst
                    else:
                        qwargs[key] = val

        return qwargs

    def _declare_more_individuals(self, onto, df):
        for index, row in df.iterrows():
            if isinstance(row["class"], str):
                parent = onto[row["class"]]
                if parent is None:
                    # print('Invalid class:', parent)
                    # Raise warning??
                    continue

                qwargs = self._get_args(index, df, onto)
                individuum = parent(**qwargs)
