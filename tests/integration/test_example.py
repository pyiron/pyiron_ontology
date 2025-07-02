import unittest

from pyiron_ontology.example.constructor import ExampleOntology


class TestExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.onto = ExampleOntology().onto

    def test_source_finding(self):
        m1 = set([self.onto.middle1_out1])
        m2 = set([self.onto.middle2_out1])
        m_both = m1.union(m2)
        self.assertSetEqual(m_both, set(self.onto.output1_inp.get_sources()))
        self.assertSetEqual(m1, set(self.onto.output2_inp.get_sources()))
        self.assertSetEqual(m_both, set(self.onto.output3_inp.get_sources()))
        self.assertSetEqual(m2, set(self.onto.output4_inp.get_sources()))

        i1 = set([self.onto.input1_out])
        i2 = set([self.onto.input2_out])
        i_both = i1.union(i2)
        self.assertSetEqual(i_both, set(self.onto.middle1_inp1.get_sources()))
        # Now pass downstream requirements as well
        self.assertSetEqual(
            i1,
            set(
                self.onto.middle1_inp1.get_sources(
                    additional_requirements=self.onto.output3_inp.requirements
                )
            ),
        )
        self.assertSetEqual(
            i2,
            set(
                self.onto.middle2_inp1.get_sources(
                    additional_requirements=self.onto.output4_inp.requirements
                )
            ),
        )
