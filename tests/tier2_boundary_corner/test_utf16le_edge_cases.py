"""
tests/tier2_boundary_corner/test_utf16le_edge_cases.py
Tier 2 Boundary & Corner Tests: UTF-16LE Edge Cases
Tests handling of odd byte lengths, surrogate pairs, embedded nulls,
line ending variations (CRLF vs LF), and high-volume block scaling.
"""

import unittest
from tests.test_helpers import (
    UTF16_LE_BOM,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestUTF16LEEdgeCases(unittest.TestCase):

    def test_01_odd_byte_length_truncated_stream(self):
        """Odd byte length after BOM represents a corrupted/truncated UTF-16 stream."""
        raw = create_sample_translation_dat([("Key", "Valor")])
        # Append an odd stray byte
        corrupted = raw + b"\x41"
        self.assertEqual(len(corrupted) % 2, 1)
        
        # Parser must gracefully handle truncated odd byte without crashing
        parsed = parse_translation_dat(corrupted)
        self.assertEqual(parsed.get("Key"), "Valor")

    def test_02_surrogate_pairs_handling(self):
        """Unicode characters outside BMP (surrogate pairs) must be preserved if encountered."""
        surrogate_string = "Torchlight ⚔️ 🛡️ Quest"
        raw = create_sample_translation_dat([("Title", surrogate_string)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("Title"), surrogate_string)

    def test_03_embedded_null_byte_tolerance(self):
        """Parser must not terminate early on null characters embedded in raw text."""
        raw = create_sample_translation_dat([("Normal", "Normal text")])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("Normal"), "Normal text")

    def test_04_mixed_line_endings_crlf_and_lf(self):
        """Parser must handle mixed CRLF (\\r\\n) and LF (\\n) line breaks seamlessly."""
        mixed_text = (
            "[TRANSLATION]\n"
            "<STRING>ORIGINAL:One\r\n"
            "<STRING>TRANSLATION:Um\n"
            "[/TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Two\n"
            "<STRING>TRANSLATION:Dois\r\n"
            "[/TRANSLATION]\n"
        )
        raw = UTF16_LE_BOM + mixed_text.encode("utf-16le")
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("One"), "Um")
        self.assertEqual(parsed.get("Two"), "Dois")

    def test_05_high_volume_block_scaling(self):
        """Parser must cleanly process thousands of translation blocks without stack overflow."""
        entries = [(f"Original String #{i}", f"String Traduzida #{i}") for i in range(1500)]
        raw = create_sample_translation_dat(entries)
        parsed = parse_translation_dat(raw)
        self.assertEqual(len(parsed), 1500)
        self.assertEqual(parsed["Original String #999"], "String Traduzida #999")


if __name__ == "__main__":
    unittest.main()
