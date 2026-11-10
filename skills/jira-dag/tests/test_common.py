import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from jira_common import num


class Num(unittest.TestCase):
    def test_missing_or_blank_is_none(self):
        self.assertIsNone(num(None))
        self.assertIsNone(num(" "))
        self.assertIsNone(num("x"))

    def test_numbers(self):
        self.assertEqual(num("8.2"), 8.2)
        self.assertEqual(num(3), 3.0)
