"""
tests/tier2_boundary_corner/test_empty_translations.py
Tier 2 Boundary & Corner Tests: Empty and Whitespace Strings
Tests handling of empty translation values, empty original keys,
whitespace-only strings, and punctuation-only entries.
"""

import unittest
from tests.test_helpers import (
    create_sample_translation_dat,
    parse_translation_dat
)


class TestEmptyTranslations(unittest.TestCase):

    def test_01_empty_translation_value(self):
        """Empty translation value should be parsed as empty string without crashing."""
        raw = create_sample_translation_dat([("Untranslated Key", "")])
        parsed = parse_translation_dat(raw)
        self.assertIn("Untranslated Key", parsed)
        self.assertEqual(parsed["Untranslated Key"], "")

    def test_02_whitespace_only_translation(self):
        """Translation consisting solely of whitespace should be safely handled."""
        raw = create_sample_translation_dat([("Space Key", "   ")])
        parsed = parse_translation_dat(raw)
        self.assertIn("Space Key", parsed)
        self.assertEqual(parsed["Space Key"], "")

    def test_03_punctuation_only_strings(self):
        """Punctuation symbols (: + - ...) frequently used in UI separators must parse cleanly."""
        symbols = [(":", ":"), ("+", "+"), ("-", "-"), ("...", "...")]
        raw = create_sample_translation_dat(symbols)
        parsed = parse_translation_dat(raw)
        for orig, trans in symbols:
            self.assertEqual(parsed.get(orig), trans)

    def test_04_single_character_strings(self):
        """Single character entries ('A', '1', '%') must be preserved."""
        chars = [("A", "A"), ("X", "X"), ("0", "0")]
        raw = create_sample_translation_dat(chars)
        parsed = parse_translation_dat(raw)
        for orig, trans in chars:
            self.assertEqual(parsed.get(orig), trans)

    def test_05_internal_spaces_preserved(self):
        """Leading/trailing spacing within sentences must retain proper word separation."""
        raw = create_sample_translation_dat([("Hello World", "Olá Mundo")])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed["Hello World"], "Olá Mundo")


if __name__ == "__main__":
    unittest.main()
