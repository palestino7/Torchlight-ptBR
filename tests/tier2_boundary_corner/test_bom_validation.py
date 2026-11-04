"""
tests/tier2_boundary_corner/test_bom_validation.py
Tier 2 Boundary & Corner Tests: BOM Validation
Tests handling of valid UTF-16LE BOM, missing BOM, inverted big-endian BOM,
UTF-8 BOM collisions, and empty files with BOM.
"""

import unittest
from tests.test_helpers import (
    UTF16_LE_BOM,
    create_sample_translation_dat,
    parse_translation_dat
)

UTF8_BOM = b"\xef\xbb\xbf"
UTF16_BE_BOM = b"\xfe\xff"


class TestBOMValidation(unittest.TestCase):

    def test_01_valid_utf16le_bom_accepted(self):
        """Files starting with \\xFF\\xFE must be accepted and parsed correctly."""
        raw = create_sample_translation_dat([("Start", "Iniciar")])
        self.assertTrue(raw.startswith(UTF16_LE_BOM))
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("Start"), "Iniciar")

    def test_02_missing_bom_rejected(self):
        """Files lacking the UTF-16LE BOM must raise a descriptive ValueError."""
        # Raw bytes without BOM
        text = "[TRANSLATION]\r\n<STRING>ORIGINAL:Test\r\n<STRING>TRANSLATION:Teste\r\n[/TRANSLATION]\r\n"
        raw_without_bom = text.encode("utf-16le")
        self.assertFalse(raw_without_bom.startswith(UTF16_LE_BOM))
        
        with self.assertRaises(ValueError) as ctx:
            parse_translation_dat(raw_without_bom)
        self.assertIn("BOM", str(ctx.exception))

    def test_03_utf8_bom_rejected(self):
        """A file incorrectly encoded with UTF-8 BOM (\\xEF\\xBB\\xBF) must be rejected."""
        text = "[TRANSLATION]\n<STRING>ORIGINAL:Test\n<STRING>TRANSLATION:Teste\n[/TRANSLATION]\n"
        raw_utf8 = UTF8_BOM + text.encode("utf-8")
        
        with self.assertRaises(ValueError) as ctx:
            parse_translation_dat(raw_utf8)
        self.assertIn("BOM", str(ctx.exception))

    def test_04_utf16be_inverted_bom_rejected(self):
        """Big-endian UTF-16 BOM (\\xFE\\xFF) must be rejected (game engine requires Little-Endian)."""
        text = "[TRANSLATION]\r\n<STRING>ORIGINAL:Test\r\n<STRING>TRANSLATION:Teste\r\n[/TRANSLATION]\r\n"
        raw_be = UTF16_BE_BOM + text.encode("utf-16be")
        
        with self.assertRaises(ValueError) as ctx:
            parse_translation_dat(raw_be)
        self.assertIn("BOM", str(ctx.exception))

    def test_05_file_with_bom_only_parsed_as_empty(self):
        """A translation.dat containing only the 2-byte BOM must parse to an empty dictionary without crash."""
        raw_bom_only = UTF16_LE_BOM
        parsed = parse_translation_dat(raw_bom_only)
        self.assertEqual(len(parsed), 0)


if __name__ == "__main__":
    unittest.main()
