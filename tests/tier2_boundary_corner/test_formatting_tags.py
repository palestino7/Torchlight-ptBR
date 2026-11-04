"""
tests/tier2_boundary_corner/test_formatting_tags.py
Tier 2 Boundary & Corner Tests: Formatting Tags & Corruption
Tests color tag validation (|c...|u), hex code lengths, unclosed tag resilience,
lowercase vs uppercase hex codes, and newline escape integrity.
"""

import unittest
import re


class TestFormattingTags(unittest.TestCase):

    def validate_formatting_tags(self, text):
        """
        Validates that all |c tags have matching |u terminators and exactly 8 hex characters.
        Returns a list of errors found.
        """
        errors = []
        open_tags = list(re.finditer(r"\|c([^|]*)", text))
        close_tags = list(re.finditer(r"\|u", text))
        
        for match in open_tags:
            hex_part = match.group(1)[:8]
            if len(hex_part) < 8 or not all(c in "0123456789abcdefABCDEF" for c in hex_part):
                errors.append(f"Invalid hex color in tag: {match.group(0)}")
                
        if len(open_tags) != len(close_tags):
            errors.append(f"Mismatched tag count: {len(open_tags)} |c vs {len(close_tags)} |u")
            
        return errors

    def test_01_valid_color_tags(self):
        """Valid |cFFFFBA00Text|u should pass with 0 errors."""
        sample = "Requer |cFFFFBA00Nível 20|u para equipar."
        errors = self.validate_formatting_tags(sample)
        self.assertEqual(len(errors), 0)

    def test_02_detect_short_hex_code(self):
        """Color tag with only 6 hex characters instead of 8 must be flagged as error."""
        corrupted = "Requer |cFF0000Vermelho|u texto."
        errors = self.validate_formatting_tags(corrupted)
        self.assertTrue(any("Invalid hex" in e for e in errors))

    def test_03_detect_unclosed_color_tag(self):
        """Opening tag |c without matching |u must be flagged."""
        unclosed = "Requer |cFFFFBA00Nível 20 sem fechar."
        errors = self.validate_formatting_tags(unclosed)
        self.assertTrue(any("Mismatched tag" in e for e in errors))

    def test_04_hex_code_case_insensitivity(self):
        """Game engine accepts both uppercase and lowercase hex digits in |c tags."""
        upper = "|cFFFFBA00Ouro|u"
        lower = "|cffffba00Ouro|u"
        self.assertEqual(len(self.validate_formatting_tags(upper)), 0)
        self.assertEqual(len(self.validate_formatting_tags(lower)), 0)

    def test_05_nested_color_tags(self):
        """Nested or sequential color tags must have equal open and close counts."""
        nested = "|cFFFF0000Fogo |cFF0000FFGelo|u Fogo|u"
        errors = self.validate_formatting_tags(nested)
        self.assertEqual(len(errors), 0)

    def test_06_literal_backslash_n_versus_newline(self):
        """Distinguish actual line feed (\n) from literal backslash-n string ('\\n')."""
        real_newline = "Linha 1\nLinha 2"
        escaped_literal = "Linha 1\\nLinha 2"
        self.assertEqual(len(real_newline.splitlines()), 2)
        self.assertEqual(len(escaped_literal.splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
