"""
tests/tier1_feature_coverage/test_f07_monsters_translation.py
Feature F07: Monsters, Bosses & Lore Translation
Verifies boss titles, champion modifiers, enemy types,
dungeon level descriptions, and lore text against the live translation_catalog.json.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT
from tools.verify_translation import TranslationVerifier


class TestF07MonstersTranslation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found at {catalog_path}")
        with open(catalog_path, "r", encoding="utf-8") as f:
            cls.catalog = json.load(f)
        cls.monsters_entries = cls.catalog.get("categories", {}).get("Monsters", [])
        cls.monsters_map = {e["original"]: e.get("translation", e["original"]) for e in cls.monsters_entries}
        cls.dungeons_entries = cls.catalog.get("categories", {}).get("Dungeons", [])
        cls.dungeons_map = {e["original"]: e.get("translation", e["original"]) for e in cls.dungeons_entries}
        cls.quests_entries = cls.catalog.get("categories", {}).get("Quests", [])
        cls.quests_map = {e["original"]: e.get("translation", e["original"]) for e in cls.quests_entries}

    def test_01_bosses_and_named_characters(self):
        """Major boss names and titles in live catalog must preserve proper nouns while translating titles."""
        boss_checks = [
            ("The Overseer", "O Feitor"),
            ("Brink the Corrupted", "Brink, o Corrompido"),
            ("Corrupted Ancient", "Ancestral Corrompido"),
            ("Blackchurch the Overseer", "Blackchurch, o Feitor"),
            ("Corrupted Shambler", "Andarilho Corrompido"),
        ]
        for eng, expected in boss_checks:
            self.assertIn(eng, self.monsters_map, f"Missing boss in catalog: {eng}")
            pt = self.monsters_map[eng]
            self.assertNotEqual(eng, pt, f"Boss untranslated in catalog: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")
            if "Corrupted" in eng:
                self.assertIn("Corrompido", pt)
            if "Overseer" in eng:
                self.assertIn("Feitor", pt)

    def test_02_champion_monster_modifiers(self):
        """Elite and champion monsters in live catalog must use concise pt-BR adjectives."""
        champion_checks = [
            ("Ratlin Foreman Champion", "Campeão Feitor Ratlin"),
            ("Ratlin Foreman Champion Unique", "Campeão Feitor Ratlin Único"),
        ]
        for eng, expected in champion_checks:
            self.assertIn(eng, self.monsters_map, f"Missing champion monster in catalog: {eng}")
            pt = self.monsters_map[eng]
            self.assertNotEqual(eng, pt, f"Champion monster untranslated: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")
            self.assertIn("Campeão", pt)

    def test_03_standard_enemy_creatures(self):
        """Standard creature names in live catalog must follow proper Portuguese syntax."""
        creature_checks = [
            ("Skeleton Warrior", "Guerreiro Esqueleto"),
            ("Dire Lich", "Lich Atroz"),
            ("Rock Troll", "Troll da Rocha"),
            ("Goblin Hero", "Herói Goblin"),
            ("Pygmy Lord", "Senhor Pigmeu"),
        ]
        for eng, expected in creature_checks:
            self.assertIn(eng, self.monsters_map, f"Missing creature in catalog: {eng}")
            pt = self.monsters_map[eng]
            self.assertNotEqual(eng, pt, f"Creature untranslated: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")

    def test_04_dungeon_level_descriptions(self):
        """Dungeon zone names and features in live catalog must use correct Portuguese translations."""
        dungeon_checks = [
            ("Totem 01", "Totem Sagrado 01"),
            ("Totem 02", "Totem Sagrado 02"),
            ("CAVE", "CAVERNA"),
            ("CRYPT", "CRIPTA"),
            ("Lair", "Covil"),
            ("Maze", "Labirinto"),
        ]
        for eng, expected in dungeon_checks:
            self.assertIn(eng, self.dungeons_map, f"Missing dungeon feature in catalog: {eng}")
            pt = self.dungeons_map[eng]
            self.assertNotEqual(eng, pt, f"Dungeon feature untranslated: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")

    def test_05_lore_notes_and_cinematics(self):
        """Quest and narrative text in live catalog must maintain an epic fantasy tone in idiomatic pt-BR."""
        translated_quests = [
            e for e in self.quests_entries
            if len(e["original"].split()) > 5 and e.get("translation", "") != e["original"]
        ]
        self.assertGreater(
            len(translated_quests), 20,
            f"Too few narrative quest translations in catalog: {len(translated_quests)}"
        )
        for e in translated_quests[:10]:
            orig = e["original"]
            trans = e["translation"]
            self.assertNotEqual(orig, trans)
            errs = TranslationVerifier.validate_formatting_and_tags(orig, trans)
            self.assertEqual(len(errs), 0, f"Tag error in narrative quest {e['id']}: {errs}")

    def test_06_live_catalog_monsters_category_if_present(self):
        """Verify high translation coverage and tag integrity in live Monsters category."""
        total = len(self.monsters_entries)
        self.assertGreater(total, 500, f"Monsters count too low: {total}")

        translated_count = sum(1 for e in self.monsters_entries if e.get("translation", "") != e["original"])
        ratio = translated_count / total
        self.assertGreaterEqual(
            ratio, 0.50,
            f"Monsters translation ratio too low: {translated_count}/{total} ({ratio*100:.1f}%)"
        )

        # Check multi-word untranslated strings (excluding allowed proper names)
        allowed_proper = {"Nicola Brink", "Trill-Bot 4000"}
        untrans_multi = [
            e["original"] for e in self.monsters_entries
            if e.get("translation", "") == e["original"]
            and len(e["original"].split()) > 1
            and not e["original"].startswith("Bip")
            and e["original"] not in allowed_proper
        ]
        self.assertEqual(
            len(untrans_multi), 0,
            f"Found untranslated multi-word monsters in live catalog: {untrans_multi}"
        )


if __name__ == "__main__":
    unittest.main()
