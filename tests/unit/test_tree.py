from unittest import TestCase

import pyiron_ontology


class TestTree(TestCase):
    def test_construction(self):
        # Just a simple test based on the current status of the ontology to make sure
        # the basics are working
        # Don't take this test too seriously, it's not asserting a promised interface,
        # it's just making sure I can actually do stuff on the CI.

        onto = pyiron_ontology.dynamic.atomistics()
        tree = pyiron_ontology.build_tree(onto.Bulk_modulus)

        while len(tree.children) > 0:
            tree = tree.children[0]

        self.assertEqual(onto["CreateStructureBulk/output/structure"], tree.value)
