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

        self.assertEqual(
            onto.input2_inp,
            tree.value,
            msg="Output4 has a a requirement for I2(), so ONLY input2 should be showing"
                "up if this requirement correctly gets transitively passed through the"
                "middle layer"
        )

        self.assertEqual(
            len(tree.parent.children),
            1,
            msg="If you broke transitive condition passing, the previous test might "
                "have passed stochastically; this makes sure there was only one"
                "solution available."
        )
