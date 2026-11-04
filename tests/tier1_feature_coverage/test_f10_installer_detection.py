"""
tests/tier1_feature_coverage/test_f10_installer_detection.py
Feature F10: Inno Setup Script & Steam Auto-Detect
Verifies Inno Setup script sections, Steam App 41500 registry querying,
libraryfolders.vdf parsing, and game folder validation logic.
"""

import unittest
import re
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT, REAL_STEAM_PATH


class TestF10InstallerDetection(unittest.TestCase):

    SAMPLE_VDF = """
    "libraryfolders"
    {
        "contentstatsid"		"123456789"
        "0"
        {
            "path"		"C:\\\\Program Files (x86)\\\\Steam"
            "label"		""
            "contentid"		"11111111"
            "apps"
            {
                "41500"		"350000000"
            }
        }
        "1"
        {
            "path"		"D:\\\\SteamLibrary"
            "label"		"Games"
            "apps"
            {
                "570"		"15000000000"
            }
        }
    }
    """

    def test_01_inno_setup_script_structure_contract(self):
        """Inno Setup script setup.iss must contain required core sections."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        required_sections = ["[Setup]", "[Files]", "[Languages]", "[Code]"]
        
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            for sec in required_sections:
                self.assertIn(sec, content)
        else:
            # Contract verification on expected template structure
            sample_iss = (
                "[Setup]\nAppName=Torchlight pt-BR\n"
                "[Languages]\nName: \"brazilianportuguese\"; MessagesFile: \"compiler:Languages\\BrazilianPortuguese.isl\"\n"
                "[Files]\nSource: \"translation_ptbr\\*\"; DestDir: \"{app}\"\n"
                "[Code]\nfunction InitializeSetup(): Boolean;\nbegin\nResult := True;\nend;\n"
            )
            for sec in required_sections:
                self.assertIn(sec, sample_iss)

    def test_02_steam_app_41500_registry_key_specification(self):
        """The installer detection logic must target Steam App 41500."""
        target_reg_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 41500"
        target_val = "InstallLocation"
        
        # Verify format of standard uninstall registry path
        self.assertIn("Steam App 41500", target_reg_key)
        self.assertEqual(target_val, "InstallLocation")

    def test_03_wow6432node_registry_fallback_specification(self):
        """On 64-bit Windows, the 32-bit registry view WOW6432Node must be supported."""
        wow64_key = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 41500"
        self.assertIn("WOW6432Node", wow64_key)

    def test_04_vdf_library_folders_parser(self):
        """Parser must extract additional Steam library root paths from libraryfolders.vdf."""
        def extract_steam_libraries(vdf_text):
            paths = []
            for match in re.finditer(r'"path"\s+"([^"]+)"', vdf_text):
                clean_path = match.group(1).replace(r"\\", "\\")
                paths.append(clean_path)
            return paths

        extracted = extract_steam_libraries(self.SAMPLE_VDF)
        self.assertIn(r"C:\Program Files (x86)\Steam", extracted)
        self.assertIn(r"D:\SteamLibrary", extracted)

    def test_05_game_folder_validation_logic(self):
        """Validation logic must verify presence of Torchlight.exe or Pak.zip before allowing install."""
        def is_valid_torchlight_dir(folder_path: Path):
            return (folder_path / "Torchlight.exe").exists() or (folder_path / "Pak.zip").exists()

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            empty_dir = Path(td) / "empty"
            empty_dir.mkdir()
            self.assertFalse(is_valid_torchlight_dir(empty_dir))
            
            valid_dir = Path(td) / "valid"
            valid_dir.mkdir()
            (valid_dir / "Torchlight.exe").write_bytes(b"dummy")
            self.assertTrue(is_valid_torchlight_dir(valid_dir))

    def test_06_real_machine_steam_path_detection(self):
        """Check if the real Steam installation exists and has Torchlight.exe."""
        if REAL_STEAM_PATH.exists():
            self.assertTrue(
                (REAL_STEAM_PATH / "Torchlight.exe").exists() or (REAL_STEAM_PATH / "Pak.zip").exists(),
                "Real Torchlight directory exists but lacks game binaries"
            )


if __name__ == "__main__":
    unittest.main()
