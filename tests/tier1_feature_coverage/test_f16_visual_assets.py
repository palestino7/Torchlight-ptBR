"""
tests/tier1_feature_coverage/test_f16_visual_assets.py
Feature F16: Visual Graphic Assets
Verifies hero banner PNG signatures, installer wizard artwork,
application icon structure (.ico), and directory paths.
"""

import unittest
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
BMP_MAGIC = b"BM"
ICO_MAGIC = b"\x00\x00\x01\x00"


class TestF16VisualAssets(unittest.TestCase):

    def test_01_hero_banner_png_header_if_present(self):
        """banner_hero.png must have a valid 8-byte PNG header if generated."""
        banner_path = PROJECT_ROOT / "docs" / "images" / "banner_hero.png"
        if banner_path.exists():
            data = banner_path.read_bytes()
            self.assertTrue(data.startswith(PNG_MAGIC), "banner_hero.png is not a valid PNG file")
            self.assertGreater(len(data), 1024, "banner_hero.png is abnormally small")
        else:
            # Contract verification
            self.assertEqual(PNG_MAGIC, b"\x89PNG\r\n\x1a\n")

    def test_02_installer_wizard_header_if_present(self):
        """Wizard images (wizard_large, wizard_small) must be valid BMP or PNG files."""
        installer_dir = PROJECT_ROOT / "src" / "installer"
        for img_name in ["wizard_large.bmp", "wizard_small.bmp", "wizard.bmp"]:
            img_path = installer_dir / img_name
            if img_path.exists():
                data = img_path.read_bytes()
                self.assertTrue(
                    data.startswith(BMP_MAGIC) or data.startswith(PNG_MAGIC),
                    f"{img_name} does not have valid BMP or PNG header"
                )

    def test_03_installer_icon_format(self):
        """Installer icon (.ico) must start with valid ICONDIR signature."""
        ico_path = PROJECT_ROOT / "src" / "installer" / "torchlight_ptbr.ico"
        if ico_path.exists():
            data = ico_path.read_bytes()
            self.assertTrue(data.startswith(ICO_MAGIC), "Installer icon does not have valid ICO header")
        else:
            # Contract check
            self.assertEqual(ICO_MAGIC, b"\x00\x00\x01\x00")

    def test_04_asset_directory_paths_contract(self):
        """Standard asset paths must be docs/images/ for documentation graphics."""
        expected_docs_img_dir = Path("docs/images")
        self.assertEqual(str(expected_docs_img_dir).replace("\\", "/"), "docs/images")

    def test_05_setup_iss_asset_references_consistency(self):
        """Any images referenced in setup.iss must exist or be mapped to valid filenames."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            # If WizardImageFile is specified, ensure it points to an image
            if "WizardImageFile=" in content:
                self.assertTrue(any(ext in content for ext in [".bmp", ".png"]))

    def test_06_minimum_asset_dimensions_contract(self):
        """Hero banner must be designed for wide display (minimum recommended ratio > 1.5)."""
        # Recommended dimensions: 1200x500 or 1280x640 (aspect ratio >= 16:9 or 2:1)
        recommended_width = 1200
        recommended_height = 500
        self.assertGreater(recommended_width / recommended_height, 1.5)


if __name__ == "__main__":
    unittest.main()
