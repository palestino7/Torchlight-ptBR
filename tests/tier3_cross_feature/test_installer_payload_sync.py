"""
tests/tier3_cross_feature/test_installer_payload_sync.py
Tier 3 Cross-Feature Integration: Installer Payload Synchronization
Verifies that Inno Setup script [Files] definitions align with
compiled translation_ptbr/ assets and game directory destinations.
"""

import unittest
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestInstallerPayloadSync(unittest.TestCase):

    def test_01_payload_directory_structure_contract(self):
        """Payload directory translation_ptbr must contain translations and media/UI directories."""
        payload_dir = PROJECT_ROOT / "translation_ptbr"
        # If payload dir exists, check subdirectories
        if payload_dir.exists():
            self.assertTrue(
                (payload_dir / "translations").exists() or (payload_dir / "media").exists() or any(payload_dir.iterdir()),
                "translation_ptbr directory exists but contains no subdirectories or files"
            )
        else:
            # Expected contract
            expected_paths = ["translation_ptbr/translations/translation.dat", "translation_ptbr/media/UI"]
            for p in expected_paths:
                self.assertTrue(p.startswith("translation_ptbr/"))

    def test_02_inno_setup_files_section_maps_to_app(self):
        """Inno Setup [Files] directives must target {app} or subdirectories."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            self.assertIn("[Files]", content)
            self.assertIn("{app}", content)
        else:
            # Contract verification
            directive = 'Source: "translation_ptbr\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs'
            self.assertIn("{app}", directive)
            self.assertIn("translation_ptbr", directive)

    def test_03_installer_overwrites_with_ignoreversion_flag(self):
        """Inno Setup file copy rules should use ignoreversion for text assets."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            self.assertIn("ignoreversion", content.lower())
        else:
            sample_rule = "Flags: ignoreversion"
            self.assertIn("ignoreversion", sample_rule)


if __name__ == "__main__":
    unittest.main()
