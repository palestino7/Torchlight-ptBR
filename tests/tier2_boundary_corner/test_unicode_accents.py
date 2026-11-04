"""
tests/tier2_boundary_corner/test_unicode_accents.py
Tier 2 Boundary & Corner Tests: Brazilian Portuguese Unicode Accents
Tests individual accented glyphs, lowercase/uppercase pairs, NFC normalization,
and code point ranges matching Torchlight's TrueType fonts.
"""

import unittest
import unicodedata
from tests.test_helpers import (
    PTBR_LOWER_ACCENTS,
    PTBR_UPPER_ACCENTS,
    PTBR_ALL_ACCENTS,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestUnicodeAccents(unittest.TestCase):

    def test_01_lowercase_accented_characters(self):
        """All lowercase pt-BR accented characters must survive DAT roundtrip."""
        for char in PTBR_LOWER_ACCENTS:
            word = f"teste_{char}_palavra"
            raw = create_sample_translation_dat([(char, word)])
            parsed = parse_translation_dat(raw)
            self.assertEqual(parsed.get(char), word)

    def test_02_uppercase_accented_characters(self):
        """All uppercase pt-BR accented characters must survive DAT roundtrip."""
        for char in PTBR_UPPER_ACCENTS:
            word = f"TITULO_{char}_TEXTO"
            raw = create_sample_translation_dat([(char, word)])
            parsed = parse_translation_dat(raw)
            self.assertEqual(parsed.get(char), word)

    def test_03_case_mapping_preservation(self):
        """Case conversions must preserve accent integrity."""
        sample_upper = "POÇÃO DE RECUPERAÇÃO MÁGICA"
        sample_lower = "poção de recuperação mágica"
        self.assertEqual(sample_upper.lower(), sample_lower)
        self.assertEqual(sample_lower.upper(), sample_upper)

    def test_04_nfc_precomposed_normalization(self):
        """CEGUI font renderer expects precomposed NFC Unicode characters."""
        # Decomposed NFD: 'a' + combining acute
        nfd_str = unicodedata.normalize("NFD", "poção mágica")
        # Precomposed NFC: single code points
        nfc_str = unicodedata.normalize("NFC", nfd_str)
        
        self.assertEqual(len(nfc_str), 12)
        self.assertLess(len(nfc_str), len(nfd_str))
        
        # Ensure DAT serialization uses NFC
        raw = create_sample_translation_dat([("Magic", nfc_str)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("Magic"), nfc_str)

    def test_05_latin1_code_point_range_compliance(self):
        """All accented pt-BR characters must fall within the Latin-1 Supplement range (U+00A0..U+00FF)."""
        for char in PTBR_ALL_ACCENTS:
            cp = ord(char)
            self.assertTrue(
                0x00A0 <= cp <= 0x00FF,
                f"Character {char} (U+{cp:04X}) outside standard Latin-1 range"
            )


if __name__ == "__main__":
    unittest.main()
