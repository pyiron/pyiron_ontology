import unittest

class testOmitFilesStillFail(unittest.TestCase):
    def test_failure(self):
        self.assertEqual(0, 1)