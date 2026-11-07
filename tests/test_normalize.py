import unittest
from ledgerflow.normalize import normalize_reference, description_similarity


class NormalizeTests(unittest.TestCase):
    def test_reference_ignores_separators_and_case(self):
        self.assertEqual(normalize_reference("ref - 123_a"), "REF123A")

    def test_description_overlap(self):
        self.assertEqual(description_similarity("Office supplies", "Supplies for office"), 1.0)

    def test_empty_description_similarity(self):
        self.assertEqual(description_similarity("and the", "invoice"), 0.0)
