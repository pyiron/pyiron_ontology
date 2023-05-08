import unittest

from pyiron_ontology.atomistics.constructor import AtomisticsOntology
from pyiron_ontology.atomistics.reasoning import AtomisticsReasoner


class TestExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.onto = AtomisticsOntology().onto

    def test_reasoner_instantiation(self):
        AtomisticsReasoner(self.onto)
