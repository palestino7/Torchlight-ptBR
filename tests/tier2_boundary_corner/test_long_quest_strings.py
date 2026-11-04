"""
tests/tier2_boundary_corner/test_long_quest_strings.py
Tier 2 Boundary & Corner Tests: Long Quest Strings & Buffer Limits
Tests handling of extreme string lengths (>1KB, >4KB), multiline dialogues,
and combined formatting tags under heavy textual load.
"""

import unittest
from tests.test_helpers import (
    create_sample_translation_dat,
    parse_translation_dat
)


class TestLongQuestStrings(unittest.TestCase):

    def test_01_quest_text_exceeding_1024_chars(self):
        """Quest narrative text exceeding 1024 characters must parse without truncation."""
        long_text = ("As minas de Torchlight escondem segredos ancestrais. " * 25).strip()
        self.assertGreater(len(long_text), 1024)
        
        raw = create_sample_translation_dat([("LongQuestDesc", long_text)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("LongQuestDesc"), long_text)
        self.assertEqual(len(parsed.get("LongQuestDesc")), len(long_text))

    def test_02_extreme_text_exceeding_4096_chars(self):
        """Very large lore notes or end-game scrolls (>4KB) must parse losslessly."""
        extreme_text = ("O poder do Âmbar corrompe tudo o que toca. " * 100).strip()
        self.assertGreater(len(extreme_text), 4096)
        
        raw = create_sample_translation_dat([("LoreBook", extreme_text)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("LoreBook"), extreme_text)

    def test_03_multiparagraph_quest_dialogue(self):
        """Dialogues with 10+ paragraphs and mixed line breaks must preserve every paragraph."""
        paragraphs = [f"Parágrafo {i}: O herói desceu ao nível {i} das minas de Torchlight." for i in range(1, 15)]
        full_dialogue = "\n\n".join(paragraphs)
        
        raw = create_sample_translation_dat([("StoryIntro", full_dialogue)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("StoryIntro"), full_dialogue)
        self.assertEqual(parsed.get("StoryIntro").count("\n\n"), 13)

    def test_04_long_string_with_embedded_color_tags(self):
        """Long strings with multiple color tags throughout must preserve all tags intact."""
        parts = []
        for i in range(20):
            parts.append(f"Fase {i}: encontre o |cFFFFBA00Item #{i}|u nas ruínas.")
        combined = " ".join(parts)
        
        raw = create_sample_translation_dat([("MultiTagQuest", combined)])
        parsed = parse_translation_dat(raw)
        self.assertEqual(parsed.get("MultiTagQuest"), combined)
        self.assertEqual(parsed.get("MultiTagQuest").count("|cFFFFBA00"), 20)
        self.assertEqual(parsed.get("MultiTagQuest").count("|u"), 20)

    def test_05_power_of_two_buffer_boundaries(self):
        """Verify strings at exact power-of-two boundaries (256, 512, 1024, 2048)."""
        for size in [256, 512, 1024, 2048]:
            boundary_str = "A" * (size - 1) + "Z"
            self.assertEqual(len(boundary_str), size)
            raw = create_sample_translation_dat([(f"Size_{size}", boundary_str)])
            parsed = parse_translation_dat(raw)
            self.assertEqual(len(parsed[f"Size_{size}"]), size)
            self.assertEqual(parsed[f"Size_{size}"][-1], "Z")


if __name__ == "__main__":
    unittest.main()
