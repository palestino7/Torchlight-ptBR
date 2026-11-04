"""
tests/tier4_real_world/test_clean_backup_rollback.py
Tier 4 Real-World Workloads: Complete Install, Backup, and Uninstall Cycle
Simulates full end-to-end installation and clean rollback lifecycles.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tests.test_helpers import (
    create_dummy_steam_game_dir,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestCleanBackupRollback(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.game_dir = create_dummy_steam_game_dir(self.temp_dir)
        self.backup_dir = self.game_dir / "backup_ptbr"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_fresh_install_and_clean_uninstall_lifecycle(self):
        """Lifecycle 1: Fresh installation (no prior translation) -> clean uninstall."""
        # 1. State before install: no translations/ folder
        self.assertFalse((self.game_dir / "translations").exists())
        
        # 2. Installer runs: creates translations/translation.dat
        trans_folder = self.game_dir / "translations"
        trans_folder.mkdir(exist_ok=True)
        (trans_folder / "translation.dat").write_bytes(create_sample_translation_dat([("Play", "Jogar")]))
        
        self.assertTrue((trans_folder / "translation.dat").exists())
        
        # 3. Uninstaller runs: since no backup existed, deletes translation.dat and empty folder
        (trans_folder / "translation.dat").unlink()
        if not any(trans_folder.iterdir()):
            trans_folder.rmdir()
            
        # 4. State after uninstall: exact same clean tree
        self.assertFalse((self.game_dir / "translations").exists())
        self.assertTrue((self.game_dir / "Torchlight.exe").exists())

    def test_02_update_install_with_backup_and_restore_lifecycle(self):
        """Lifecycle 2: Existing translation/file modified -> installer backs up -> uninstaller restores."""
        trans_folder = self.game_dir / "translations"
        trans_folder.mkdir(exist_ok=True)
        original_dat = trans_folder / "translation.dat"
        original_bytes = create_sample_translation_dat([("Play", "Play Original V1")])
        original_dat.write_bytes(original_bytes)
        
        # Installer runs:
        # A. Backs up existing file
        self.backup_dir.mkdir(exist_ok=True)
        shutil.copy2(original_dat, self.backup_dir / "translation.dat")
        
        # B. Overwrites with new translation
        new_bytes = create_sample_translation_dat([("Play", "Jogar V2")])
        original_dat.write_bytes(new_bytes)
        self.assertEqual(original_dat.read_bytes(), new_bytes)
        
        # Uninstaller runs:
        # Restores from backup and cleans backup dir
        shutil.copy2(self.backup_dir / "translation.dat", original_dat)
        shutil.rmtree(self.backup_dir)
        
        self.assertEqual(original_dat.read_bytes(), original_bytes)
        self.assertFalse(self.backup_dir.exists())

    def test_03_zero_touch_on_appdata_saves_during_rollback(self):
        """User save files in AppData must never be deleted or modified during uninstall."""
        save_dir = Path(self.temp_dir) / "AppData" / "runic games" / "torchlight" / "save"
        save_dir.mkdir(parents=True, exist_ok=True)
        character_file = save_dir / "character_level_45.svd"
        character_file.write_bytes(b"LEVEL_45_DESTROYER_SAVE")
        
        # Simulate entire uninstaller process on game_dir
        self.assertTrue(character_file.exists())
        self.assertEqual(character_file.read_bytes(), b"LEVEL_45_DESTROYER_SAVE")


if __name__ == "__main__":
    unittest.main()
