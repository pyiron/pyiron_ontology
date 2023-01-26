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
import pandas


def is_subset(a, b):
    return np.all([aa in b for aa in a])


class Constructor(ABC):
    def __init__(self, name: str, closed: bool = True, strict: bool = False):
        onto = owl.get_ontology(f"file://{name}.owl")
        self._declare_classes(onto)
        self._declare_additional_classes(onto)
        self._declare_individuals(onto)
        df = self._generate_df(onto)
        self._declare_dynamic_individuals(onto, df)
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
        self.df = df

    def save(self):
        self.onto.save()

    @abstractmethod
    def _declare_individuals(self, onto):
        pass

    def _declare_additional_classes(self, onto):
        pass

    def _declare_classes(self, onto):
        with onto:

            class PyObject(owl.Thing):
                comment = "my pyiron object"

            class Parameter(PyObject):
                @property
                def description(self):
                    if len(self.generic_parameter) > 0:
                        return self.generic_parameter[0].description

                def get_conditions(
                    self, additional_conditions: Optional[list[Label]] = None
                ):
                    additional_conditions = (
                        [] if additional_conditions is None else additional_conditions
                    )
                    return additional_conditions

                @abstractmethod
                def get_sources(
                    self, additional_conditions: list[Label] = None
                ) -> list:
                    # Note: We aren't actually enforcing the abstractmethod with ABC
                    #       because of metaclass conflicts with owlready
                    #       It just functions as a behaviour hint to devs.
                    pass

                @staticmethod
                def _filter_by_conditions(
                    items: list[Parameter], conditions: list[Label]
                ):
                    return [i for i in items if is_subset(conditions, i.has_options)]

                @staticmethod
                def _filter_by_class(
                    items: list[Parameter],
                    valid_classes: type[Parameter] | tuple[type[Parameter], ...],
                ):
                    return [i for i in items if isinstance(i, valid_classes)]

            class InputParameter(Parameter):
                def get_conditions(
                    self, additional_conditions: Optional[list[Label]] = None
                ):
                    additional_conditions = super().get_conditions(
                        additional_conditions
                    )
                    receivable_conditions = list(
                        set(additional_conditions).intersection(
                            self.has_transitive_conditions
                        )
                    )
                    return list(set(self.has_conditions).union(receivable_conditions))

                def get_sources(
                    self, additional_conditions: list[Label] = None
                ) -> list[OutputParameter | Code]:
                    conditions = self.get_conditions(additional_conditions)

                    matching_parameters = self._filter_by_conditions(
                        self.generic_parameter[0].has_parameters, conditions
                    )

                    return self._filter_by_class(
                        matching_parameters, (OutputParameter, Code)
                    )

            class OutputParameter(Parameter):
                def get_sources(
                    self, additional_conditions: list[Label] = None
                ) -> list[Code]:
                    conditions = self.get_conditions(additional_conditions)
                    return self._filter_by_conditions(self.output_of, conditions)

            class GenericParameter(Parameter):
                description = ""

                def get_sources(
                    self, additional_conditions: list[Label] = None
                ) -> list[OutputParameter]:
                    conditions = self.get_conditions(additional_conditions)
                    candidates = self._filter_by_class(
                        self.has_parameters, OutputParameter
                    )
                    return self._filter_by_conditions(candidates, conditions)

            class Code(Parameter):
                def get_sources(
                    self, additional_conditions: list[Label] = None
                ) -> list[InputParameter]:
                    return self.mandatory_input

            class Label(PyObject):
                pass

            class has_conditions(Parameter >> Label):
                pass

            class has_transitive_conditions(Parameter >> Label):
                pass  # condition to fulfill option in code

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

    def _declare_dynamic_individuals(self, onto, df):
        for index, row in df.iterrows():
            if isinstance(row["class"], str):
                parent = onto[row["class"]]
                if parent is None:
                    # print('Invalid class:', parent)
                    # Raise warning??
                    continue

                qwargs = self._get_args(index, df, onto)
                individuum = parent(**qwargs)
