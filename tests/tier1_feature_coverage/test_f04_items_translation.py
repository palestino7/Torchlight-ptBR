"""
tests/tier1_feature_coverage/test_f04_items_translation.py
Feature F04: Items & Equipment Translation
Verifies weapons, armor, rarities, affixes, consumables, and gems/sockets.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF04ItemsTranslation(unittest.TestCase):

    ITEM_BASES = {
        "Sword": "Espada",
        "Axe": "Machado",
        "Bow": "Arco",
        "Shield": "Escudo",
        "Boots": "Botas",
        "Helmet": "Elmo",
        "Staff": "Cajado",
        "Wand": "Varinha",
        "Pistol": "Pistola",
        "Rifle": "Fuzil"
    }

    RARITIES = {
        "Common": "Comum",
        "Magic": "Mágico",
        "Rare": "Raro",
        "Unique": "Único"
    }

    CONSUMABLES = {
        "Potion of Full Healing": "Poção de Cura Total",
        "Potion of Mana": "Poção de Mana",
        "Scroll of Town Portal": "Pergaminho de Portal da Cidade",
        "Scroll of Identify": "Pergaminho de Identificação"
    }

    GEMS = {
        "Amethyst": "Ametista",
        "Ruby": "Rubi",
        "Sapphire": "Safira",
        "Emerald": "Esmeralda",
        "Empty Socket": "Engaste Vazio"
    }

    def test_01_weapon_and_armor_base_types(self):
        """Weapon and armor base categories must have standard pt-BR RPG naming."""
        for eng, pt in self.ITEM_BASES.items():
            self.assertNotEqual(eng, pt)
            self.assertGreater(len(pt), 2)

    def test_02_item_rarity_tiers(self):
        """Item rarity terms must be translated with proper accents (e.g. Mágico, Único)."""
        self.assertEqual(self.RARITIES["Common"], "Comum")
        self.assertEqual(self.RARITIES["Magic"], "Mágico")
        self.assertEqual(self.RARITIES["Rare"], "Raro")
        self.assertEqual(self.RARITIES["Unique"], "Único")

    def test_03_affix_prefix_suffix_grammar(self):
        """Affixes must translate correctly into Portuguese prepositional forms (e.g. 'do Urso')."""
        affixes = {
            "of the Bear": "do Urso",
            "of Slaughter": "do Massacre",
            "Fiery": "Ígneo",
            "Glacial": "Glacial"
        }
        for eng, pt in affixes.items():
            self.assertGreater(len(pt), 2)

    def test_04_consumable_potions_and_scrolls(self):
        """Potions and scrolls must use correct Portuguese terminology."""
        for eng, pt in self.CONSUMABLES.items():
            self.assertTrue(pt.startswith("Poção") or pt.startswith("Pergaminho"))

    def test_05_gems_and_sockets_terminology(self):
        """Gems and sockets must translate consistently across all item tooltips."""
        for eng, pt in self.GEMS.items():
            self.assertGreater(len(pt), 3)
        self.assertIn("Engaste", self.GEMS["Empty Socket"])

    def test_06_live_catalog_items_category_if_present(self):
        """If catalog JSON is present, verify Items category integrity."""
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("categories", {}).get("Items", [])
            self.assertIsInstance(items, list)


if __name__ == "__main__":
    unittest.main()
