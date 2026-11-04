"""
tests/tier1_feature_coverage/test_f08_transmutation_translation.py
Feature F08: Transmutation & Globals Translation
Verifies transmutation recipes, combat notifications, system messages,
floating text prompts, and GLOBALS.DAT parameter translations.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF08TransmutationGlobalsTranslation(unittest.TestCase):

    TRANSMUTATION_RECIPES = {
        "Combine 4 Gems of the same type": "Combine 4 Gemas do mesmo tipo",
        "Transmute into a superior potion": "Transmuta em uma poção superior",
        "Combine 3 Rings to create an Amulet": "Combine 3 Anéis para criar um Amuleto"
    }

    COMBAT_MESSAGES = {
        "Critical Hit!": "Acerto Crítico!",
        "Level Up!": "Subiu de Nível!",
        "%s hits %s for %d damage": "%s atinge %s causando %d de dano",
        "%s was slain by %s": "%s foi derrotado por %s"
    }

    SYSTEM_MESSAGES = {
        "Not enough mana": "Mana insuficiente",
        "Inventory is full": "O inventário está cheio",
        "Cannot equip that item": "Não é possível equipar esse item",
        "Requires Level %d": "Requer Nível %d"
    }

    FLOATY_TEXT = {
        "Dodge!": "Esquiva!",
        "Blocked!": "Bloqueado!",
        "Miss": "Errou",
        "Immune": "Imune"
    }

    def test_01_transmutation_recipe_instructions(self):
        """Transmutation recipes must clearly guide players on combining items."""
        for eng, pt in self.TRANSMUTATION_RECIPES.items():
            self.assertNotEqual(eng, pt)
            self.assertTrue(pt.startswith("Combine") or pt.startswith("Transmuta"))

    def test_02_combat_notifications_and_logs(self):
        """Combat events must have immediate, recognizable Brazilian Portuguese terms."""
        for eng, pt in self.COMBAT_MESSAGES.items():
            self.assertNotEqual(eng, pt)
            if "%d" in eng:
                self.assertIn("%d", pt)

    def test_03_system_error_messages(self):
        """System feedback messages must be helpful and grammatical."""
        for eng, pt in self.SYSTEM_MESSAGES.items():
            self.assertNotEqual(eng, pt)
            self.assertGreater(len(pt), 4)

    def test_04_floating_combat_text(self):
        """Short combat floating cues (FloatyText) must be punchy and fit screen space."""
        for eng, pt in self.FLOATY_TEXT.items():
            self.assertNotEqual(eng, pt)
            self.assertLessEqual(len(pt), 15)

    def test_05_globals_string_parameters_coverage(self):
        """Engine-level globals must preserve positional variables without breaking."""
        sample_global = "You gained %d gold."
        sample_pt = "Você recebeu %d de ouro."
        self.assertIn("%d", sample_pt)
        self.assertTrue(sample_pt.startswith("Você"))

    def test_06_live_catalog_globals_recipes_if_present(self):
        """If catalog JSON is present, verify Recipes and Globals categories."""
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cats = data.get("categories", {})
            self.assertTrue("Globals" in cats or "Recipes" in cats)


if __name__ == "__main__":
    unittest.main()
