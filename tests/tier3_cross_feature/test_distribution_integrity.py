"""
tests/tier3_cross_feature/test_distribution_integrity.py
Tier 3 Cross-Feature Integration: Distribution Package Integrity
Verifies package pipeline: .exe compilation -> .zip packaging -> SHA256 checksums matching,
and detection of altered distribution payloads.
"""

import unittest
import tempfile
import zipfile
from pathlib import Path
from tests.test_helpers import calculate_sha256, PROJECT_ROOT


class TestDistributionIntegrity(unittest.TestCase):

    def test_01_distribution_packaging_and_hashing_flow(self):
        """Simulate packaging an installer .exe into a .zip and generating SHA256SUMS.txt."""
        with tempfile.TemporaryDirectory() as td:
            dist_dir = Path(td) / "dist"
            dist_dir.mkdir()
            
            # 1. Create simulated installer .exe
            exe_file = dist_dir / "Torchlight_Traducao_ptBR_Setup.exe"
            exe_file.write_bytes(b"MZ_DUMMY_INNO_SETUP_COMPILATION_PAYLOAD_12345")
            
            # 2. Package into .zip
            zip_file = dist_dir / "Torchlight_Traducao_ptBR_v1.0.0.zip"
            with zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.write(exe_file, arcname="Torchlight_Traducao_ptBR_Setup.exe")
                
            # 3. Calculate hashes
            exe_hash = calculate_sha256(exe_file)
            zip_hash = calculate_sha256(zip_file)
            
            # 4. Generate SHA256SUMS.txt
            sums_file = dist_dir / "SHA256SUMS.txt"
            sums_content = f"{exe_hash} *{exe_file.name}\n{zip_hash} *{zip_file.name}\n"
            sums_file.write_text(sums_content, encoding="utf-8")
            
            # 5. Verification step
            lines = sums_file.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                h, fn = line.split(maxsplit=1)
                clean_name = fn.lstrip("* ").strip()
                target_path = dist_dir / clean_name
                self.assertTrue(target_path.exists())
                self.assertEqual(calculate_sha256(target_path), h)

    def test_02_detect_tampered_payload_in_distribution(self):
        """Corrupted/modified distribution artifact must fail SHA256 verification."""
        with tempfile.TemporaryDirectory() as td:
            temp_file = Path(td) / "installer.exe"
            temp_file.write_bytes(b"AUTHENTIC_DATA")
            authentic_hash = calculate_sha256(temp_file)
            
            # Alter byte
            temp_file.write_bytes(b"TAMPERED_DATA")
            tampered_hash = calculate_sha256(temp_file)
            
            self.assertNotEqual(authentic_hash, tampered_hash)


if __name__ == "__main__":
    unittest.main()
