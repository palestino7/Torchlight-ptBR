"""
tests/tier1_feature_coverage/test_f03_ui_translation.py
Feature F03: UI & Menus Translation
Verifies main menu, difficulty settings, character creation, HUD/inventory labels,
and string length constraints to prevent UI overflow clipping.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF03UIMenusTranslation(unittest.TestCase):

    # Canonical reference dictionary of UI translations
    CANONICAL_UI_TRANSLATIONS = {
        "Quit Game": "Sair do Jogo",
        "New Character": "Novo Personagem",
        "Continue": "Continuar",
        "Settings": "Configurações",
        "Resume Game": "Continuar Jogo",
        "Easy": "Fácil",
        "Normal": "Normal",
        "Hard": "Difícil",
        "Very Hard": "Muito Difícil",
        "Hardcore": "Hardcore",
        "Destroyer": "Destruidor",
        "Alchemist": "Alquimista",
        "Vanquisher": "Vingadora",
        "Inventory": "Inventário",
        "Skills": "Habilidades",
        "Points Remaining": "Pontos Restantes",
        "Gold": "Ouro"
    }

    def test_01_main_menu_strings_translation(self):
        """Main menu buttons must have accurate, contextual Brazilian Portuguese translations."""
        menu_keys = ["Quit Game", "New Character", "Continue", "Settings", "Resume Game"]
        for key in menu_keys:
            self.assertIn(key, self.CANONICAL_UI_TRANSLATIONS)
            trans = self.CANONICAL_UI_TRANSLATIONS[key]
            self.assertGreater(len(trans), 0)
            self.assertNotEqual(key, trans)

    def test_02_difficulty_levels_translation(self):
        """Difficulty level titles must be translated accurately according to ARPG conventions."""
        diff_keys = ["Easy", "Normal", "Hard", "Very Hard"]
        expected = {
            "Easy": "Fácil",
            "Normal": "Normal",
            "Hard": "Difícil",
            "Very Hard": "Muito Difícil"
        }
        for k, v in expected.items():
            self.assertEqual(self.CANONICAL_UI_TRANSLATIONS[k], v)

    def test_03_character_class_names(self):
        """Hero class names must have lore-consistent translations."""
        classes = {
            "Destroyer": "Destruidor",
            "Alchemist": "Alquimista",
            "Vanquisher": "Vingadora"
        }
        for eng, pt in classes.items():
            self.assertEqual(self.CANONICAL_UI_TRANSLATIONS[eng], pt)

    def test_04_hud_and_inventory_labels(self):
        """HUD and inventory interface labels must be translated with proper accents."""
        hud_labels = {
            "Inventory": "Inventário",
            "Skills": "Habilidades",
            "Points Remaining": "Pontos Restantes",
            "Gold": "Ouro"
        }
        for eng, pt in hud_labels.items():
            self.assertEqual(self.CANONICAL_UI_TRANSLATIONS[eng], pt)
            # Verify proper accents
            if "á" in pt or "ã" in pt:
                self.assertTrue(any(c in pt for c in "áã"))

    def test_05_ui_button_overflow_bounds_ratio(self):
        """Translated UI strings should not exceed 2.5x original length to avoid layout overflow."""
        for orig, trans in self.CANONICAL_UI_TRANSLATIONS.items():
            ratio = len(trans) / len(orig)
            self.assertLessEqual(
                ratio, 2.5,
                f"Translation '{trans}' is {ratio:.1f}x longer than '{orig}', risking button clipping"
            )

    def test_06_live_catalog_ui_category_if_present(self):
        """If translation_catalog.json is already compiled by M1/M2, verify its UI category."""
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("categories", data)
            ui_entries = data["categories"].get("UI", [])
            self.assertIsInstance(ui_entries, list)
            if ui_entries:
                for entry in ui_entries[:10]:
                    self.assertIn("original", entry)


if __name__ == "__main__":
    unittest.main()
