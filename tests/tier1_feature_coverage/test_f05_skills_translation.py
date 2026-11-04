"""
tests/tier1_feature_coverage/test_f05_skills_translation.py
Feature F05: Skills & Spells Translation
Verifies Alchemist, Destroyer, Vanquisher skills, spell scrolls, and
preservation of dynamic printf-style format specifiers and tokens against
the live translation_catalog.json.
"""

import unittest
import json
import re
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT
from tools.verify_translation import TranslationVerifier


class TestF05SkillsTranslation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found at {catalog_path}")
        with open(catalog_path, "r", encoding="utf-8") as f:
            cls.catalog = json.load(f)
        cls.skills_entries = cls.catalog.get("categories", {}).get("Skills", [])
        cls.skills_map = {e["original"]: e.get("translation", e["original"]) for e in cls.skills_entries}

    def test_01_alchemist_skill_names(self):
        """Alchemist skill tree translations in live catalog must be lore-accurate with proper accents."""
        alchemist_checks = [
            ("Ember Bolt", "Dardo de Âmbar"),
            ("Ember Lance", "Lança de Âmbar"),
            ("Summon Alchemical Golem", "Invocar Golem Alquímico"),
            ("Ember Wave", "Onda de Âmbar"),
        ]
        for eng, expected in alchemist_checks:
            self.assertIn(eng, self.skills_map, f"Missing skill in catalog: {eng}")
            pt = self.skills_map[eng]
            self.assertNotEqual(eng, pt, f"Skill untranslated in catalog: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")
            self.assertTrue(any(c in pt for c in "áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ"), f"Missing accent in {pt}")

    def test_02_destroyer_skill_names(self):
        """Destroyer melee skills in live catalog must use dynamic martial pt-BR verbs and nouns."""
        destroyer_checks = [
            ("Death Rush", "Investida Mortal"),
            ("Blast Wave", "Onda de Impacto"),
            ("Soul Rend", "Despedaçar Alma"),
            ("Wind Wall", "Muralha de Vento"),
        ]
        for eng, expected in destroyer_checks:
            self.assertIn(eng, self.skills_map, f"Missing skill in catalog: {eng}")
            pt = self.skills_map[eng]
            self.assertNotEqual(eng, pt, f"Skill untranslated in catalog: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")

    def test_03_vanquisher_ranged_skills(self):
        """Vanquisher ranged skills in live catalog must translate archery and firearm abilities accurately."""
        vanquisher_checks = [
            ("Ricochet", "Ricochete"),
            ("Explosive Shot", "Disparo Explosivo"),
            ("Arrow Hail", "Chuva de Flechas"),
            ("Drain Trap", "Armadilha de Dreno"),
        ]
        for eng, expected in vanquisher_checks:
            self.assertIn(eng, self.skills_map, f"Missing skill in catalog: {eng}")
            pt = self.skills_map[eng]
            self.assertNotEqual(eng, pt, f"Skill untranslated in catalog: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")

    def test_04_spell_scrolls_translation(self):
        """Spell scrolls and skill actions must have clear and concise pt-BR names in live catalog."""
        spells_checks = [
            ("CAST SKILL", "CONJURAR HABILIDADE"),
            ("KNOCK BACK", "REPULSÃO"),
            ("LIFE STEAL", "ROUBO DE VIDA"),
            ("AOE Shock", "Choque em Área"),
        ]
        for eng, expected in spells_checks:
            self.assertIn(eng, self.skills_map, f"Missing term in catalog: {eng}")
            pt = self.skills_map[eng]
            self.assertNotEqual(eng, pt, f"Term untranslated in catalog: {eng}")
            self.assertEqual(pt, expected, f"Unexpected translation for {eng}: {pt} != {expected}")

    def test_05_dynamic_format_specifier_preservation(self):
        """Skill entries with format specifiers (%d, %0.1f, %s) and bracket tokens must match 1:1 in live catalog."""
        tag_errors = []
        for entry in self.skills_entries:
            orig = entry["original"]
            trans = entry.get("translation", orig)
            errs = TranslationVerifier.validate_formatting_and_tags(orig, trans)
            if errs:
                tag_errors.append((entry["id"], orig, trans, errs))

        self.assertEqual(
            len(tag_errors), 0,
            f"Encountered tag or format specifier mismatch in Skills: {tag_errors[:5]}"
        )

    def test_06_live_catalog_skills_category_if_present(self):
        """Verify high translation coverage and presence of pt-BR accented characters in Skills category."""
        total = len(self.skills_entries)
        self.assertGreater(total, 500, f"Skills count too low: {total}")

        translated_count = sum(1 for e in self.skills_entries if e.get("translation", "") != e["original"])
        ratio = translated_count / total
        self.assertGreaterEqual(
            ratio, 0.60,
            f"Skills translation ratio too low: {translated_count}/{total} ({ratio*100:.1f}%)"
        )

        accented_count = sum(
            1 for e in self.skills_entries
            if any(c in e.get("translation", "") for c in "áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ")
        )
        self.assertGreater(
            accented_count, 100,
            f"Accented pt-BR vowels count in Skills too low: {accented_count}"
        )


if __name__ == "__main__":
    unittest.main()
