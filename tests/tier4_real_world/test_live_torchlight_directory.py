"""
tests/tier4_real_world/test_live_torchlight_directory.py
Tier 4 Real-World Workloads: Live Torchlight Game Installation Verification
Validates the actual Steam installation at C:\\Program Files (x86)\\Steam\\steamapps\\common\\Torchlight,
including PE executable headers, Pak.zip integrity, and font assets.
"""

import unittest
import zipfile
import struct
from pathlib import Path
from tests.test_helpers import REAL_STEAM_PATH, UTF16_LE_BOM


class TestLiveTorchlightDirectory(unittest.TestCase):

    def test_01_real_game_directory_exists(self):
        """The real Torchlight Steam installation directory must be present on the host."""
        self.assertTrue(
            REAL_STEAM_PATH.exists(),
            f"Expected Steam path not found: {REAL_STEAM_PATH}"
        )

    def test_02_torchlight_exe_pe_header_integrity(self):
        """Torchlight.exe must be a valid Win32 PE executable."""
        exe_path = REAL_STEAM_PATH / "Torchlight.exe"
        self.assertTrue(exe_path.exists())
        
        with open(exe_path, "rb") as f:
            header = f.read(1024)
            
        # Must start with MZ
        self.assertTrue(header.startswith(b"MZ"), "Missing MZ DOS header")
        
        # Read e_lfanew offset to PE header
        pe_offset = struct.unpack_from("<I", header, 0x3C)[0]
        self.assertLess(pe_offset, len(header))
        self.assertEqual(header[pe_offset:pe_offset + 4], b"PE\x00\x00", "Missing PE signature")

    def test_03_pak_zip_integrity_and_member_census(self):
        """Pak.zip must be a valid ZIP archive containing over 20,000 entries."""
        pak_path = REAL_STEAM_PATH / "Pak.zip"
        self.assertTrue(pak_path.exists())
        self.assertGreater(pak_path.stat().st_size, 300_000_000)
        
        with zipfile.ZipFile(pak_path, "r") as z:
            namelist = z.namelist()
            self.assertGreater(len(namelist), 20000)
            self.assertIn("media/UI/mainmenuframe.layout", namelist)
            self.assertTrue(any("globals.dat" in n.lower() for n in namelist))

    def test_04_embedded_truetype_font_assets(self):
        """Pak.zip must contain the three TrueType fonts supporting pt-BR accents."""
        pak_path = REAL_STEAM_PATH / "Pak.zip"
        with zipfile.ZipFile(pak_path, "r") as z:
            namelist = [n.lower() for n in z.namelist()]
            self.assertTrue(any("torchlight regular.ttf" in n for n in namelist))
            self.assertTrue(any("brlnsdb.ttf" in n for n in namelist))
            self.assertTrue(any("consola.ttf" in n for n in namelist))

    def test_05_buildver_txt_version_string(self):
        """BuildVer.txt must be UTF-16LE and contain Steam build number 17685."""
        ver_file = REAL_STEAM_PATH / "BuildVer.txt"
        self.assertTrue(ver_file.exists())
        
        data = ver_file.read_bytes()
        self.assertTrue(data.startswith(UTF16_LE_BOM), "BuildVer.txt missing UTF-16LE BOM")
        text = data[2:].decode("utf-16le")
        self.assertIn("17685", text)


if __name__ == "__main__":
    unittest.main()
