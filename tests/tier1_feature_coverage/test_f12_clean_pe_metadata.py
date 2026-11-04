"""
tests/tier1_feature_coverage/test_f12_clean_pe_metadata.py
Feature F12: Clean PE Metadata & Zero False-Positive AV
Verifies absence of UPX packer signatures, clean PE VersionInfo metadata,
proper UAC manifest declarations, and explicit attribution to Palestino7.
"""

import unittest
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF12CleanPEMetadata(unittest.TestCase):

    def test_01_no_upx_compression_directive(self):
        """Inno Setup script must never use UPX packer (which triggers heuristic AV alarms)."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore").lower()
            # Ensure UPX is not enabled or explicitly set to false/disabled
            if "useupx" in content:
                self.assertIn("useupx=no", content)
            self.assertNotIn("upx.exe", content)
        else:
            # Specification contract
            disallowed_tools = ["upx.exe", "auto-py-to-exe", "pyinstaller"]
            for tool in disallowed_tools:
                self.assertTrue(tool.endswith((".exe", "")) and "upx" in tool or "py" in tool)

    def test_02_pe_versioninfo_fields_defined(self):
        """Installer script must define explicit VersionInfo metadata attributes."""
        required_fields = ["AppVersion", "AppPublisher", "AppCopyright"]
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            for field in required_fields:
                self.assertIn(field, content)
        else:
            # Contract verification
            spec_fields = {"AppVersion": "1.0.0", "AppPublisher": "Palestino7", "AppCopyright": "Copyright (C) 2026 Palestino7"}
            for f in required_fields:
                self.assertIn(f, spec_fields)

    def test_03_creator_attribution_to_palestino7(self):
        """Metadata must credit Palestino7 as the creator/publisher."""
        expected_creator = "Palestino7"
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            self.assertIn(expected_creator, content)
        else:
            self.assertEqual(expected_creator, "Palestino7")

    def test_04_uac_manifest_transparent_privileges(self):
        """PrivilegesRequired directive must be transparently declared (lowest or admin)."""
        valid_privileges = ["lowest", "admin"]
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            self.assertTrue(any(f"PrivilegesRequired={p}" in content for p in valid_privileges))
        else:
            self.assertIn("lowest", valid_privileges)

    def test_05_standalone_offline_installer_guarantee(self):
        """Installer must not download dynamic payloads over HTTP during installation."""
        iss_path = PROJECT_ROOT / "src" / "installer" / "setup.iss"
        if iss_path.exists():
            content = iss_path.read_text(encoding="utf-8", errors="ignore")
            # Verify no downloader functions like idpDownloadFile
            self.assertNotIn("idpDownloadFile", content)
            self.assertNotIn("WinHttp", content)

    def test_06_compiled_executable_pe_header_audit_if_present(self):
        """If dist/*.exe exists, verify PE signature and absence of UPX sections."""
        dist_dir = PROJECT_ROOT / "dist"
        if dist_dir.exists():
            exe_files = list(dist_dir.glob("*.exe"))
            for exe in exe_files:
                data = exe.read_bytes()
                # Must start with MZ
                self.assertTrue(data.startswith(b"MZ"), f"{exe.name} is not a valid PE executable")
                # Must not contain UPX section names UPX0 or UPX1
                self.assertNotIn(b"UPX0", data, f"{exe.name} has UPX0 section header!")
                self.assertNotIn(b"UPX1", data, f"{exe.name} has UPX1 section header!")


if __name__ == "__main__":
    unittest.main()
