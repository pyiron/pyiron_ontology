# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building a minimal ontology, both for a pedagogical example and for
tests.
"""

from __future__ import annotations

from pyiron_ontology.constructor import Constructor

import owlready2 as owl


class ExampleOntology(Constructor):
    """
    The ontology represents simple three layer diagrams input->middle->output, with
    different choices available at each layer.
    The final output layer has four options, which have restrictions on all combinations
    in the (`generic`, `requirements`) square, allowing for progressively fewer
    possible three-layer graphs.

    In the middle layer there's a bit of extra unused input and output, just so we can
    test to make sure we count everything correctly in non-trivial ways.

    At the domain knowledge level (i.e. the `Generic` things we define) we show how to
    achieve mutual exclusion by use of disjoint classes and instantiating individuals.

    Terminology goes: I:Input:IM:Middle:MO:Output:O, with letters and numbers to
    distinguish siblings/inheritance.
    """

    def __init__(self, name: str = "example", closed: bool = True, strict: bool = True):
        super().__init__(name=name, closed=closed, strict=strict)

    def _make_specific_declarations(self):
        onto = self.onto
        with onto:

            class I(onto.Generic):
                pass

            class I1(I):
                pass

            class I2(I):
                pass

            owl.AllDisjoint([I1, I2])

            class IM(onto.Generic):
                pass

            class IMOptional(onto.Generic):
                pass

            class MO(onto.Generic):
                pass

            class MO1(MO):
                pass

            class MO2(MO):
                pass

            class MO2A(MO2):
                pass

            class MO2B(MO2):
                pass

            owl.AllDisjoint([MO1, MO2])

            class MOUnused(onto.Generic):
                pass

            class O(onto.Generic):
                pass

            owl.AllDisjoint([O, MO, MOUnused, IMOptional, IM, I])

        input1 = onto.Function("input1")
        input1_inp = onto.Input(
            name="input1_inp",
            mandatory_input_of=input1,
            generic=I1(),
        )
        input1_out = onto.Output(
            name="input1_out",
            output_of=input1,
            generic=IM(),
        )

        input2 = onto.Function("input2")
        input2_inp = onto.Input(
            name="input2_inp",
            mandatory_input_of=input2,
            generic=I2(),
        )
        input2_out = onto.Output(
            name="input2_out",
            output_of=input2,
            generic=IM(),
        )

        middle1 = onto.Function("middle1")
        middle1_inp1 = onto.Input(
            name="middle1_inp1",
            mandatory_input_of=middle1,
            generic=IM(),
            transitive_requirements=[I()],
        )
        middle1_inp2 = onto.Input(
            name="middle1_inp2",
            optional_input_of=middle1,
            generic=IMOptional(),
        )
        middle1_out1 = onto.Output(
            name="middle1_out1",
            output_of=middle1,
            generic=MO1(),
        )
        middle1_out2 = onto.Output(
            name="middle1_out2",
            output_of=middle1,
            generic=MOUnused(),
        )

        middle2 = onto.Function("middle2")
        middle2_inp1 = onto.Input(
            name="middle2_inp1",
            mandatory_input_of=middle2,
            generic=IM(),
            transitive_requirements=[I()],
        )
        middle2_inp2 = onto.Input(
            name="middle2_inp2",
            optional_input_of=middle2,
            generic=IMOptional(),
        )
        middle2_out1 = onto.Output(
            name="middle2_out1",
            output_of=middle2,
            generic=MO2B(),
        )
        middle2_out2 = onto.Output(
            name="middle2_out2",
            output_of=middle2,
            generic=MOUnused(),
        )

        output1 = onto.Function("output1")  # Allows all paths
        output1_inp = onto.Input(
            name="output1_inp",
            mandatory_input_of=output1,
            generic=MO(),
        )
        output1_out = onto.Output(
            name="output1_out",
            output_of=output1,
            generic=O(),
        )

        output2 = onto.Function("output2")  # Must pass through middle1
        output2_inp = onto.Input(
            name="output2_inp",
            mandatory_input_of=output2,
            generic=MO1(),
        )
        output2_out = onto.Output(
            name="output2_out",
            output_of=output2,
            generic=O(),
        )

        output3 = onto.Function("output3")  # Must end at input1
        output3_inp = onto.Input(
            name="output3_inp",
            mandatory_input_of=output3,
            generic=MO(),
            requirements=[I1()],
        )
        output3_out = onto.Output(
            name="output3_out",
            output_of=output3,
            generic=O(),
        )

        output4 = onto.Function("output4")  # Only the path middle2 -> input2
        output4_inp = onto.Input(
            name="output4_inp",
            mandatory_input_of=output4,
            generic=MO2(),  # Finds middle2_out1;
            # But it only finds _more specific_ output, if these generics are swapped,
            # it finds nothing.
            # Is this really desirable, or do we want anything
            requirements=[I2()],
        )
        output4_out = onto.Output(
            name="output4_out",
            output_of=output4,
            generic=O(),
        )

        # I don't yet test dual inheritance in this example!!!
