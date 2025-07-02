# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A constructor for building a minimal ontology, both for a pedagogical example and for
tests.
"""

from __future__ import annotations

import owlready2 as owl

from pyiron_ontology.constructor import Constructor


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

    Terminology goes: I:Input:InpMid:Middle:MidOut:Output:O, with letters and numbers to
    distinguish siblings/inheritance.
    """

    def __init__(self, name: str = "example", closed: bool = True, strict: bool = True):
        super().__init__(name=name, closed=closed, strict=strict)

    def _make_specific_declarations(self):
        onto = self.onto
        with onto:

            class Inp(onto.Generic):
                pass

            class Inp1(Inp):
                pass

            class Inp2(Inp):
                pass

            owl.AllDisjoint([Inp1, Inp2])

            class InpMid(onto.Generic):
                pass

            class InpMidOptional(onto.Generic):
                pass

            class MidOut(onto.Generic):
                pass

            class MidOut1(MidOut):
                pass

            class MidOut2(MidOut):
                pass

            class MidOut2A(MidOut2):
                pass

            class MidOut2B(MidOut2):
                pass

            owl.AllDisjoint([MidOut1, MidOut2])

            class MidOutUnused(onto.Generic):
                pass

            class Out(onto.Generic):
                pass

            owl.AllDisjoint([Out, MidOut, MidOutUnused, InpMidOptional, InpMid, Inp])

        input1 = onto.Function("input1")
        input1_inp = onto.Input(
            name="input1_inp",
            mandatory_input_of=input1,
            generic=Inp1(),
        )
        input1_out = onto.Output(
            name="input1_out",
            output_of=input1,
            generic=InpMid(),
        )

        input2 = onto.Function("input2")
        input2_inp = onto.Input(
            name="input2_inp",
            mandatory_input_of=input2,
            generic=Inp2(),
        )
        input2_out = onto.Output(
            name="input2_out",
            output_of=input2,
            generic=InpMid(),
        )

        middle1 = onto.Function("middle1")
        middle1_inp1 = onto.Input(
            name="middle1_inp1",
            mandatory_input_of=middle1,
            generic=InpMid(),
            transitive_requirements=[Inp()],
        )
        middle1_inp2 = onto.Input(
            name="middle1_inp2",
            optional_input_of=middle1,
            generic=InpMidOptional(),
        )
        middle1_out1 = onto.Output(
            name="middle1_out1",
            output_of=middle1,
            generic=MidOut1(),
        )
        middle1_out2 = onto.Output(
            name="middle1_out2",
            output_of=middle1,
            generic=MidOutUnused(),
        )

        middle2 = onto.Function("middle2")
        middle2_inp1 = onto.Input(
            name="middle2_inp1",
            mandatory_input_of=middle2,
            generic=InpMid(),
            transitive_requirements=[Inp()],
        )
        middle2_inp2 = onto.Input(
            name="middle2_inp2",
            optional_input_of=middle2,
            generic=InpMidOptional(),
        )
        middle2_out1 = onto.Output(
            name="middle2_out1",
            output_of=middle2,
            generic=MidOut2B(),
        )
        middle2_out2 = onto.Output(
            name="middle2_out2",
            output_of=middle2,
            generic=MidOutUnused(),
        )

        output1 = onto.Function("output1")  # Allows all paths
        output1_inp = onto.Input(
            name="output1_inp",
            mandatory_input_of=output1,
            generic=MidOut(),
        )
        output1_out = onto.Output(
            name="output1_out",
            output_of=output1,
            generic=Out(),
        )

        output2 = onto.Function("output2")  # Must pass through middle1
        output2_inp = onto.Input(
            name="output2_inp",
            mandatory_input_of=output2,
            generic=MidOut1(),
        )
        output2_out = onto.Output(
            name="output2_out",
            output_of=output2,
            generic=Out(),
        )

        output3 = onto.Function("output3")  # Must end at input1
        output3_inp = onto.Input(
            name="output3_inp",
            mandatory_input_of=output3,
            generic=MidOut(),
            requirements=[Inp1()],
        )
        output3_out = onto.Output(
            name="output3_out",
            output_of=output3,
            generic=Out(),
        )

        output4 = onto.Function("output4")  # Only the path middle2 -> input2
        output4_inp = onto.Input(
            name="output4_inp",
            mandatory_input_of=output4,
            generic=MidOut2(),  # Finds middle2_out1;
            # But it only finds _more specific_ output, if these generics are swapped,
            # it finds nothing.
            # Is this really desirable, or do we want anything
            requirements=[Inp2()],
        )
        output4_out = onto.Output(
            name="output4_out",
            output_of=output4,
            generic=Out(),
        )

        # I don't yet test dual inheritance in this example!!!
