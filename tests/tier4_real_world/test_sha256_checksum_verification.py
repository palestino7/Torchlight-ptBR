"""
tests/tier4_real_world/test_sha256_checksum_verification.py
Tier 4 Real-World Workloads: SHA-256 Checksum Verification
Verifies cryptographic checksum generation, multi-file validation,
and bit-flip error detection across distribution artifacts.
"""

import unittest
import tempfile
from pathlib import Path
from tests.test_helpers import calculate_sha256


class TestSHA256ChecksumVerification(unittest.TestCase):

    def test_01_multifile_checksum_generation_and_validation(self):
        """Generate SHA256SUMS.txt for multiple release artifacts and verify them."""
        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td)
            
            f1 = base_dir / "Instalador_Torchlight_PTBR_v1.0.0.exe"
            f1.write_bytes(b"EXE_PAYLOAD_CONTENT_A")
            
            f2 = base_dir / "Instalador_Torchlight_PTBR_v1.0.0.zip"
            f2.write_bytes(b"ZIP_PAYLOAD_CONTENT_B")
            
            sums_file = base_dir / "SHA256SUMS.txt"
            h1 = calculate_sha256(f1)
            h2 = calculate_sha256(f2)
            
            sums_file.write_text(f"{h1} *{f1.name}\n{h2} *{f2.name}\n", encoding="utf-8")
            
            # Read and verify
            for line in sums_file.read_text(encoding="utf-8").strip().splitlines():
                expected_hash, fname = line.split(maxsplit=1)
                clean_name = fname.lstrip("* ").strip()
                computed_hash = calculate_sha256(base_dir / clean_name)
                self.assertEqual(computed_hash, expected_hash)

    def test_02_detect_single_bit_flip_tampering(self):
        """Single bit modification in installer executable must cause checksum mismatch."""
        original_data = bytearray(b"ORIGINAL_RELEASE_EXECUTABLE_BYTES")
        h_orig = calculate_sha256(bytes(original_data))
        
        # Flip a bit
        tampered_data = bytearray(original_data)
        tampered_data[5] ^= 0x01
        h_tampered = calculate_sha256(bytes(tampered_data))
        
        self.assertNotEqual(h_orig, h_tampered)

    def test_03_detect_missing_release_file(self):
        """If a file listed in SHA256SUMS.txt does not exist on disk, detection must report it."""
        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td)
            sums_file = base_dir / "SHA256SUMS.txt"
            dummy_hash = "a" * 64
            sums_file.write_text(f"{dummy_hash} *MissingFile.exe\n", encoding="utf-8")
            
            for line in sums_file.read_text(encoding="utf-8").strip().splitlines():
                _, fname = line.split(maxsplit=1)
                clean_name = fname.lstrip("* ").strip()
                self.assertFalse((base_dir / clean_name).exists())


if __name__ == "__main__":
    unittest.main()
