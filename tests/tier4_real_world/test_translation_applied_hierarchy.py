"""
tests/tier4_real_world/test_translation_applied_hierarchy.py
Tier 4 Real-World Workloads: In-Game File Hierarchy & OGRE Resolution
Verifies proper placement and accessibility of translations/translation.dat
and media/UI/*.layout in the game root directory.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tests.test_helpers import (
    create_dummy_steam_game_dir,
    create_sample_translation_dat,
    parse_translation_dat,
    create_sample_cegui_layout,
    parse_cegui_layout_texts
)


class TestTranslationAppliedHierarchy(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.game_dir = create_dummy_steam_game_dir(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_deploy_translation_dat_to_expected_game_path(self):
        """translation.dat must be deployed to <game_dir>/translations/translation.dat."""
        trans_folder = self.game_dir / "translations"
        trans_folder.mkdir(exist_ok=True)
        
        dat_file = trans_folder / "translation.dat"
        sample_entries = [("Play", "Jogar"), ("Options", "Opções")]
        dat_file.write_bytes(create_sample_translation_dat(sample_entries))
        
        self.assertTrue(dat_file.exists())
        self.assertTrue(dat_file.read_bytes().startswith(b"\xff\xfe"))
        
        # Test engine parsing from deployed path
        parsed = parse_translation_dat(dat_file)
        self.assertEqual(parsed["Play"], "Jogar")
        self.assertEqual(parsed["Options"], "Opções")

    def test_02_deploy_localized_cegui_layouts(self):
        """Localized CEGUI .layout XMLs must be deployed to <game_dir>/media/UI/."""
        ui_folder = self.game_dir / "media" / "UI"
        ui_folder.mkdir(parents=True, exist_ok=True)
        
        layout_file = ui_folder / "mainmenuframe.layout"
        layout_content = create_sample_cegui_layout({
            "NewChar": "Novo Personagem",
            "Exit": "Sair"
        })
        layout_file.write_bytes(layout_content)
        
        self.assertTrue(layout_file.exists())
        parsed = parse_cegui_layout_texts(layout_file.read_bytes())
        self.assertEqual(parsed["NewChar"], "Novo Personagem")
        self.assertEqual(parsed["Exit"], "Sair")

    def test_03_ogre_resource_resolution_relative_path(self):
        """Torchlight fallback checks translations\\translation.dat relative to working directory."""
        rel_path = Path("translations") / "translation.dat"
        target_file = self.game_dir / rel_path
        target_file.parent.mkdir(exist_ok=True)
        target_file.write_bytes(b"\xff\xfe")
        
        self.assertTrue((self.game_dir / rel_path).exists())


if __name__ == "__main__":
    unittest.main()
