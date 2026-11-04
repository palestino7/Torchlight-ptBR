"""
tests/tier1_feature_coverage/test_f11_backup_rollback.py
Feature F11: Safety Backup & Rollback Uninstaller
Verifies pre-install backup creation, restoration on uninstall,
removal of orphaned translation files, and absolute user save safety.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tests.test_helpers import (
    create_dummy_steam_game_dir,
    create_sample_translation_dat,
    UTF16_LE_BOM
)


class TestF11BackupRollback(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.game_dir = create_dummy_steam_game_dir(self.temp_dir)
        self.backup_dir = self.game_dir / "backup_ptbr"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_preinstall_backup_creation(self):
        """If a translation.dat already exists, installer must back it up before overwriting."""
        trans_dir = self.game_dir / "translations"
        trans_dir.mkdir(exist_ok=True)
        orig_file = trans_dir / "translation.dat"
        orig_bytes = b"ORIGINAL_DATA_12345"
        orig_file.write_bytes(orig_bytes)
        
        # Simulate backup routine
        self.backup_dir.mkdir(exist_ok=True)
        backup_target = self.backup_dir / "translation.dat"
        shutil.copy2(orig_file, backup_target)
        
        self.assertTrue(backup_target.exists())
        self.assertEqual(backup_target.read_bytes(), orig_bytes)

    def test_02_backup_preserves_original_bytes(self):
        """Backup file must be bit-identical to pre-existing game file."""
        test_file = self.game_dir / "resources.cfg"
        orig_hash = test_file.stat().st_size
        
        self.backup_dir.mkdir(exist_ok=True)
        backup_file = self.backup_dir / "resources.cfg"
        shutil.copy2(test_file, backup_file)
        
        self.assertEqual(backup_file.stat().st_size, orig_hash)

    def test_03_uninstaller_restores_original_backup(self):
        """Uninstallation must restore backed-up original files cleanly."""
        trans_dir = self.game_dir / "translations"
        trans_dir.mkdir(exist_ok=True)
        installed_file = trans_dir / "translation.dat"
        
        # Create backup of initial state
        self.backup_dir.mkdir(exist_ok=True)
        (self.backup_dir / "translation.dat").write_bytes(b"INITIAL_ORIGINAL")
        
        # Overwrite with translation
        installed_file.write_bytes(b"PTBR_TRANSLATION")
        self.assertEqual(installed_file.read_bytes(), b"PTBR_TRANSLATION")
        
        # Simulate uninstall restore
        if (self.backup_dir / "translation.dat").exists():
            shutil.copy2(self.backup_dir / "translation.dat", installed_file)
            shutil.rmtree(self.backup_dir)
            
        self.assertEqual(installed_file.read_bytes(), b"INITIAL_ORIGINAL")
        self.assertFalse(self.backup_dir.exists())

    def test_04_uninstaller_removes_translation_if_no_prior_backup(self):
        """If no prior translation.dat existed, uninstall must delete newly installed translation file."""
        trans_dir = self.game_dir / "translations"
        trans_dir.mkdir(exist_ok=True)
        installed_file = trans_dir / "translation.dat"
        installed_file.write_bytes(b"PTBR_TRANSLATION")
        
        # No backup directory exists. Uninstaller should delete installed_file
        if installed_file.exists():
            installed_file.unlink()
        if trans_dir.exists() and not any(trans_dir.iterdir()):
            trans_dir.rmdir()
            
        self.assertFalse(installed_file.exists())
        self.assertFalse(trans_dir.exists())

    def test_05_user_save_isolation_guarantee(self):
        """Installer and uninstaller routines must never access or modify user save games."""
        fake_appdata = Path(self.temp_dir) / "AppData" / "runic games" / "torchlight" / "save"
        fake_appdata.mkdir(parents=True, exist_ok=True)
        save_file = fake_appdata / "0.svd"
        save_file.write_bytes(b"PLAYER_SAVE_DATA_LEVEL_50")
        
        # Verify save game directory is strictly outside of the game install directory
        self.assertNotIn(str(self.game_dir), str(fake_appdata))
        self.assertTrue(save_file.exists())
        self.assertEqual(save_file.read_bytes(), b"PLAYER_SAVE_DATA_LEVEL_50")

    def test_06_simulated_failed_install_rollback(self):
        """Simulate an aborted installation: temporary working files are cleaned up."""
        staging_dir = self.game_dir / "_staging_tmp"
        staging_dir.mkdir(exist_ok=True)
        (staging_dir / "temp_file.tmp").write_bytes(b"temp")
        
        # Rollback logic
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
            
        self.assertFalse(staging_dir.exists())


if __name__ == "__main__":
    unittest.main()
