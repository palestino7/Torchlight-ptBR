"""
tests/tier4_real_world/test_steam_dummy_install.py
Tier 4 Real-World Workloads: Simulated Steam Installation Environment
Creates a realistic dummy Steam App 41500 directory structure and validates
directory auto-detection, file permissions, and core asset discovery.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from tests.test_helpers import create_dummy_steam_game_dir


class TestSteamDummyInstall(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.game_dir = create_dummy_steam_game_dir(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_simulated_steam_directory_hierarchy(self):
        """Simulated game directory must reproduce Steam 41500 tree faithfully."""
        self.assertTrue((self.game_dir / "Torchlight.exe").exists())
        self.assertTrue((self.game_dir / "Pak.zip").exists())
        self.assertTrue((self.game_dir / "BuildVer.txt").exists())
        self.assertTrue((self.game_dir / "resources.cfg").exists())

    def test_02_detect_game_directory_from_parent(self):
        """Simulate Steam library scanning to discover the Torchlight folder."""
        steam_common = self.game_dir.parent
        self.assertEqual(steam_common.name, "common")
        found_games = [d.name for d in steam_common.iterdir() if d.is_dir()]
        self.assertIn("Torchlight", found_games)

    def test_03_file_write_permissions(self):
        """Ensure installer has write permissions in the target directory."""
        test_probe = self.game_dir / "_probe_write.tmp"
        test_probe.write_text("probe_test", encoding="ascii")
        self.assertTrue(test_probe.exists())
        test_probe.unlink()
        self.assertFalse(test_probe.exists())


if __name__ == "__main__":
    unittest.main()
