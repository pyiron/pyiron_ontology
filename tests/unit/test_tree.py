from unittest import TestCase

import pyiron_ontology


class TestTree(TestCase):
    def test_construction(self):
        # Just a simple test based on the current status of the ontology to make sure
        # the basics are working
        # Don't take this test too seriously, it's not asserting a promised interface,
        # it's just making sure I can actually do stuff on the CI.

        onto = pyiron_ontology.dynamic.example()
        tree = onto.output4_out.get_source_tree()

        while len(tree.children) > 0:
            tree = tree.children[0]


        self.assertTrue(
            tree.value == onto.input2_inp or tree.value == onto.input1_inp,
            # The or value is because there are two leaves and the ordering is
            # stochastic so we can't be sure which one we'll reach.
            msg="Didn't find expected leaf"
        )
