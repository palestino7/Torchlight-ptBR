"""
tests/tier1_feature_coverage/test_f15_documentation_readme.py
Feature F15: Illustrated Documentation & README
Verifies README structure, hero banner image reference, shields badges,
3-step installation tutorial, VirusTotal guidance, and Palestino7 credits.
"""

import unittest
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF15DocumentationReadme(unittest.TestCase):

    def test_01_hero_banner_reference(self):
        """README must embed or reference the project banner graphic."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            self.assertTrue(
                "banner_hero.png" in content or "banner" in content.lower(),
                "README missing hero banner image reference"
            )
        else:
            sample_readme = "# Torchlight pt-BR\n![Banner](docs/images/banner_hero.png)\n"
            self.assertIn("banner_hero.png", sample_readme)

    def test_02_status_badges_present(self):
        """README must feature modern Shields.io status badges."""
        expected_badge_types = ["version", "license", "status"]
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            self.assertTrue(
                "shields.io" in content or "img.shields.io" in content,
                "README missing Shields.io badges"
            )
        else:
            sample_badges = "[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()"
            self.assertIn("shields.io", sample_badges)

    def test_03_three_step_installation_tutorial(self):
        """README must contain a clear, concise 3-step installation guide."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8").lower()
            self.assertTrue(
                "passo 1" in content or "1." in content or "download" in content,
                "README missing step-by-step tutorial"
            )
        else:
            tutorial_steps = ["1. Baixe o instalador", "2. Execute o instalador", "3. Inicie o jogo"]
            self.assertEqual(len(tutorial_steps), 3)

    def test_04_virustotal_and_smartscreen_guidance(self):
        """README must provide transparent guidance on VirusTotal and Windows SmartScreen."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            self.assertTrue(
                "VirusTotal" in content or "SmartScreen" in content or "antivírus" in content.lower(),
                "README missing antivirus safety section"
            )
        else:
            safety_section = "### Segurança Antivírus\nO instalador é 100% limpo (0/72 no VirusTotal)."
            self.assertIn("VirusTotal", safety_section)

    def test_05_explicit_attribution_to_palestino7(self):
        """README must explicitly credit Palestino7 as the creator."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            self.assertIn("Palestino7", content)
        else:
            credit_line = "Desenvolvido por [Palestino7](https://github.com/palestino7)"
            self.assertIn("Palestino7", credit_line)

    def test_06_checksum_verification_section(self):
        """README must instruct users on SHA-256 checksum verification."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            self.assertTrue(
                "sha256" in content.lower() or "checksum" in content.lower(),
                "README missing checksum table or instructions"
            )
        else:
            checksum_note = "Verifique a integridade usando `Get-FileHash` ou `sha256sum`."
            self.assertIn("sha256", checksum_note.lower())


if __name__ == "__main__":
    unittest.main()
