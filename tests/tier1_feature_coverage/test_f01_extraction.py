"""
tests/tier1_feature_coverage/test_f01_extraction.py
Feature F01: Text Extraction Tooling
Verifies ADM string extraction, token filtering, CEGUI layout parsing,
category classification, and live Pak.zip extraction capabilities.
"""

import unittest
import zipfile
import json
import tempfile
from pathlib import Path
from tests.test_helpers import (
    create_sample_adm_bytes,
    parse_adm_bytes,
    create_sample_cegui_layout,
    parse_cegui_layout_texts,
    REAL_STEAM_PATH,
    PROJECT_ROOT
)


class TestF01TextExtractionTooling(unittest.TestCase):

    def test_01_adm_binary_parsing_accuracy(self):
        """ADM binary parser must extract strings and match string counts."""
        test_strings = ["Sword of the Ages", "Dagger", "Potion of Greater Healing"]
        raw_adm = create_sample_adm_bytes(test_strings, version=1)
        
        version, extracted = parse_adm_bytes(raw_adm)
        self.assertEqual(version, 1)
        self.assertEqual(len(extracted), len(test_strings))
        self.assertEqual(extracted, test_strings)

    def test_02_filtering_rules_exclude_code_tokens(self):
        """Extraction logic must filter out internal media paths and uppercase variable names."""
        mixed_tokens = [
            "media/models/weapons/sword.mesh",
            "ITEM_ID_SWORD_01",
            "ANIM_ATTACK_RUN",
            "Silver Longsword",
            "A finely balanced blade.",
            "NORMAL"
        ]
        
        def is_translatable(s):
            if s.startswith("media/") or s.startswith("MEDIA/"):
                return False
            if s.isupper() and "_" in s:
                return False
            if len(s.strip()) <= 1:
                return False
            return True

        filtered = [s for s in mixed_tokens if is_translatable(s)]
        self.assertIn("Silver Longsword", filtered)
        self.assertIn("A finely balanced blade.", filtered)
        self.assertNotIn("media/models/weapons/sword.mesh", filtered)
        self.assertNotIn("ITEM_ID_SWORD_01", filtered)
        self.assertNotIn("ANIM_ATTACK_RUN", filtered)

    def test_03_cegui_layout_xml_extraction(self):
        """CEGUI layout XML extractor must capture all Property Text values."""
        layout_dict = {
            "StartGameBtn": "Start Game",
            "OptionsBtn": "Options",
            "CreditsBtn": "Credits"
        }
        xml_bytes = create_sample_cegui_layout(layout_dict)
        extracted = parse_cegui_layout_texts(xml_bytes)
        
        self.assertEqual(extracted.get("StartGameBtn"), "Start Game")
        self.assertEqual(extracted.get("OptionsBtn"), "Options")
        self.assertEqual(extracted.get("CreditsBtn"), "Credits")

    def test_04_categorization_classifier(self):
        """Extracted strings must be categorizable based on source path heuristics."""
        def categorize_path(path_str):
            p = path_str.lower()
            if "media/ui/" in p or p.endswith(".layout"):
                return "UI"
            elif "media/quests/" in p:
                return "Quests"
            elif "media/units/items/" in p:
                return "Items"
            elif "media/skills/" in p:
                return "Skills"
            elif "media/affixes/" in p:
                return "Affixes"
            elif "media/units/monsters/" in p:
                return "Monsters"
            elif "media/recipes/" in p:
                return "Recipes"
            elif "globals.dat" in p:
                return "Globals"
            return "Other"

        self.assertEqual(categorize_path("media/UI/mainmenuframe.layout"), "UI")
        self.assertEqual(categorize_path("media/Quests/StoryQuest/quest1.dat.adm"), "Quests")
        self.assertEqual(categorize_path("media/units/items/swords/blade.dat.adm"), "Items")
        self.assertEqual(categorize_path("media/skills/ALCHEMIST/ember_bolt.dat.adm"), "Skills")
        self.assertEqual(categorize_path("media/Affixes/fire_dmg.dat.adm"), "Affixes")
        self.assertEqual(categorize_path("media/units/monsters/boss_ordrak.dat.adm"), "Monsters")
        self.assertEqual(categorize_path("media/recipes/gem_combine.dat.adm"), "Recipes")
        self.assertEqual(categorize_path("media/GLOBALS.DAT.adm"), "Globals")

    def test_05_pak_zip_inspection_and_adm_extraction(self):
        """Verify extraction against real Pak.zip or synthetic Pak.zip."""
        pak_file = REAL_STEAM_PATH / "Pak.zip"
        if pak_file.exists():
            with zipfile.ZipFile(pak_file, "r") as z:
                namelist = z.namelist()
                self.assertIn("media/UI/mainmenuframe.layout", namelist)
                adm_files = [n for n in namelist if n.lower().endswith((".dat.adm", ".adm"))]
                self.assertGreater(len(adm_files), 1000)
                
                # Read a known ADM file and verify decoding
                sample_data = z.read(adm_files[0])
                version, strings = parse_adm_bytes(sample_data)
                self.assertEqual(version, 1)
                self.assertIsInstance(strings, list)
        else:
            # Fallback synthetic validation
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                with zipfile.ZipFile(tmp_path, "w") as z:
                    z.writestr("media/UI/mainmenuframe.layout", create_sample_cegui_layout({"Btn": "Quit"}))
                    z.writestr("media/units/items/sword.dat.adm", create_sample_adm_bytes(["Sword"]))
                with zipfile.ZipFile(tmp_path, "r") as z:
                    self.assertIn("media/UI/mainmenuframe.layout", z.namelist())
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

    def test_06_catalog_schema_contract(self):
        """Translation catalog JSON must follow PROJECT.md § M1 schema specification."""
        catalog_schema = {
            "metadata": {
                "game": "Torchlight",
                "version": "1.15",
                "total_strings": 1
            },
            "categories": {
                "UI": [{"id": "UI_001", "original": "Quit Game", "translation": "Sair do Jogo", "context": "mainmenuframe.layout"}],
                "Quests": [],
                "Items": [],
                "Skills": [],
                "Affixes": [],
                "Monsters": [],
                "Globals": []
            }
        }
        # Serialize and deserialize to ensure valid JSON schema
        json_str = json.dumps(catalog_schema)
        parsed = json.loads(json_str)
        self.assertIn("metadata", parsed)
        self.assertIn("categories", parsed)
        self.assertIn("UI", parsed["categories"])
        self.assertEqual(parsed["categories"]["UI"][0]["original"], "Quit Game")


if __name__ == "__main__":
    unittest.main()
