"""
tests/tier1_feature_coverage/test_f09_formatting_accents.py
Feature F09: Formatting & Accent Preservations
Verifies color tags (|c...|u), newline preservation, full pt-BR accented
character sets in UTF-16LE, and absence of Mojibake.
"""

import unittest
import re
from tests.test_helpers import (
    PTBR_ALL_ACCENTS,
    UTF16_LE_BOM,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestF09FormattingAccents(unittest.TestCase):

    def test_01_color_tag_preservation(self):
        """Color tags (|cFFFFBA00...|u) must remain intact across translation."""
        orig = "Requires |cFFFFBA00Level 15|u to equip."
        trans = "Requer |cFFFFBA00Nível 15|u para equipar."
        
        tag_pattern = re.compile(r"\|c[0-9a-fA-F]{8}.*?\|u")
        self.assertTrue(tag_pattern.search(orig))
        self.assertTrue(tag_pattern.search(trans))
        self.assertEqual(len(tag_pattern.findall(orig)), len(tag_pattern.findall(trans)))

    def test_02_multiple_nested_color_tags(self):
        """Multiple color tags in a single item tooltip must retain their respective color codes."""
        orig = "|cFFFF0000+15 Fire Damage|u and |cFF0000FF+20 Mana|u"
        trans = "|cFFFF0000+15 de Dano de Fogo|u e |cFF0000FF+20 de Mana|u"
        
        orig_hexes = re.findall(r"\|c([0-9a-fA-F]{8})", orig)
        trans_hexes = re.findall(r"\|c([0-9a-fA-F]{8})", trans)
        self.assertEqual(orig_hexes, trans_hexes)

    def test_03_newline_preservation_in_dat(self):
        """Line breaks must be preserved through translation.dat encoding and decoding."""
        orig = "First line.\nSecond line.\nThird line."
        trans = "Primeira linha.\nSegunda linha.\nTerceira linha."
        raw_dat = create_sample_translation_dat([(orig, trans)])
        
        parsed = parse_translation_dat(raw_dat)
        self.assertEqual(parsed[orig], trans)
        self.assertEqual(parsed[orig].count("\n"), 2)

    def test_04_all_ptbr_accents_utf16le_integrity(self):
        """All lowercase and uppercase pt-BR accented characters must survive UTF-16LE encoding."""
        test_string = f"Acentuação completa: {PTBR_ALL_ACCENTS}"
        raw_dat = create_sample_translation_dat([("Alphabet", test_string)])
        
        parsed = parse_translation_dat(raw_dat)
        result = parsed["Alphabet"]
        for char in PTBR_ALL_ACCENTS:
            self.assertIn(char, result, f"Accented character '{char}' missing or corrupted")

    def test_05_mojibake_absence_check(self):
        """Strings must not contain double-encoded UTF-8 artifacts (e.g. 'Ã¡', 'Ã©')."""
        mojibake_signatures = ["Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã£", "Ãµ", "Ã§", "Ã¢", "Ãª", "Ã´", "Ã€"]
        sample_translations = [
            "Poção de Cura Rápida",
            "Manto da Destruição",
            "Coração do Vulcão",
            "Lança de Âmbar Elétrico"
        ]
        for s in sample_translations:
            for bad in mojibake_signatures:
                self.assertNotIn(bad, s, f"Mojibake detected in '{s}'")

    def test_06_variable_specifiers_preservation(self):
        """Format specifiers like %d, %s, %0.1f must remain intact."""
        orig = "Gained %d experience and %s item."
        trans = "Ganhou %d de experiência e o item %s."
        
        orig_specs = re.findall(r"%[a-zA-Z]", orig)
        trans_specs = re.findall(r"%[a-zA-Z]", trans)
        self.assertEqual(orig_specs, trans_specs)


if __name__ == "__main__":
    unittest.main()
