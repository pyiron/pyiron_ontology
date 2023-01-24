import unittest
import pyiron_ontology


class TestVersion(unittest.TestCase):
    def test_version(self):
        version = pyiron_ontology.__version__
        print(version)
        self.assertTrue(version.startswith('0'))
