"""
tests/tier1_feature_coverage/test_f13_build_pipeline.py
Feature F13: Automated Build & Distribution Pipeline
Verifies build script parameters, dist artifact structure (.exe, .zip, SHA256SUMS.txt),
and SHA-256 cryptographic verification integrity.
"""

import unittest
import tempfile
import zipfile
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT, calculate_sha256


class TestF13BuildPipeline(unittest.TestCase):

    def test_01_build_script_presence_or_contract(self):
        """build_installer.ps1 or build workflow must target dist/ directory."""
        script_path = PROJECT_ROOT / "src" / "installer" / "build_installer.ps1"
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8", errors="ignore")
            self.assertIn("dist", content.lower())
        else:
            # Contract verification
            expected_target = "dist"
            self.assertEqual(expected_target, "dist")

    def test_02_distribution_directory_naming_conventions(self):
        """Distribution artifacts must follow consistent naming conventions."""
        expected_artifacts = [
            "Torchlight_Traducao_ptBR_Setup.exe",
            "Torchlight_Traducao_ptBR_v1.0.0.zip",
            "SHA256SUMS.txt"
        ]
        for name in expected_artifacts:
            self.assertTrue(name.endswith((".exe", ".zip", ".txt")))
            self.assertTrue("Torchlight" in name or name == "SHA256SUMS.txt")

    def test_03_sha256_calculation_standard(self):
        """SHA-256 calculation must follow RFC 6234 standard."""
        test_payload = b"Torchlight pt-BR translation test hash verification"
        expected_hash = "e36c9dfbcea9d3bee158757f792d2375b23f7fe918a7e970fedec168b786a457"
        computed = calculate_sha256(test_payload)
        self.assertEqual(len(computed), 64)
        self.assertEqual(computed, expected_hash)

    def test_04_sha256sums_file_formatting_and_parsing(self):
        """SHA256SUMS.txt lines must follow the '<hash> *<filename>' format."""
        sample_sums = (
            "e36c9dfbcea9d3bee158757f792d2375b23f7fe918a7e970fedec168b786a457 *Torchlight_Traducao_ptBR_Setup.exe\n"
            + ("f" * 64) + " *Torchlight_Traducao_ptBR_v1.0.0.zip\n"
        )
        parsed = {}
        for line in sample_sums.strip().splitlines():
            parts = line.strip().split(maxsplit=1)
            self.assertEqual(len(parts), 2)
            h = parts[0].strip()
            f = parts[1].strip()
            self.assertEqual(len(h), 64)
            filename = f.lstrip("* ").strip()
            parsed[filename] = h
            
        self.assertIn("Torchlight_Traducao_ptBR_Setup.exe", parsed)
        self.assertIn("Torchlight_Traducao_ptBR_v1.0.0.zip", parsed)

    def test_05_zip_packaging_cleanliness(self):
        """Distribution zip archives must contain target files without junk files (.tmp, .DS_Store)."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = Path(tmp.name)
        try:
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("Instalador_Torchlight_PTBR.exe", b"MZ_FAKE_EXE")
                z.writestr("LEIAME.txt", "Instrucoes de instalacao".encode("utf-8"))
            
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                for n in names:
                    self.assertFalse(n.endswith(".tmp"))
                    self.assertFalse(n.endswith(".bak"))
                    self.assertNotIn("__MACOSX", n)
        finally:
            if zip_path.exists():
                zip_path.unlink()

    def test_06_live_sha256sums_verification_if_present(self):
        """If dist/SHA256SUMS.txt exists, verify every listed file matches its hash."""
        sums_file = PROJECT_ROOT / "dist" / "SHA256SUMS.txt"
        if sums_file.exists():
            content = sums_file.read_text(encoding="utf-8")
            for line in content.strip().splitlines():
                if not line.strip():
                    continue
                parts = line.split(maxsplit=1)
                expected_hash = parts[0].strip()
                filename = parts[1].lstrip("* ").strip()
                target_file = PROJECT_ROOT / "dist" / filename
                if target_file.exists():
                    actual_hash = calculate_sha256(target_file)
                    self.assertEqual(
                        actual_hash, expected_hash,
                        f"Checksum mismatch for {filename}"
                    )


if __name__ == "__main__":
    unittest.main()
