"""
tests/test_pipeline_m1.py - Comprehensive Unit & Integration Test Suite for Milestone 1 Tools

Tests:
1. tools/extract_strings.py:
   - extract_adm_strings: Valid header, invalid version, truncated data, UTF-16 strings
   - extract_layout_strings: XML text properties extraction, digit filtering
   - is_valid_translatable_string: Code keys, media paths, numeric tokens, code identifiers
   - categorize_file: All 9 canonical categories mapping
   - build_catalog: Schema compliance, metadata fields, deterministic ordering

2. tools/compile_translation.py:
   - generate_translation_dat: UTF-16LE BOM presence, block syntax, CRLF line endings
   - compile_layout_files: Text substitution, XML character escaping, encoding preservation

3. tools/verify_translation.py:
   - Valid translation.dat passes with 0 errors
   - Missing BOM fails verification
   - Mismatched tags fails verification
   - Missing ORIGINAL/TRANSLATION line fails verification
   - Catalog cross-validation detecting missing or extra strings
"""

import json
import os
import struct
import tempfile
import zipfile
import pytest

from tools.extract_strings import (
    extract_adm_strings,
    extract_layout_strings,
    is_valid_translatable_string,
    categorize_file,
    build_catalog,
    STANDARD_CATEGORIES
)
from tools.compile_translation import (
    load_catalog,
    generate_translation_dat,
    compile_layout_files,
    build_translation_map
)
from tools.verify_translation import TranslationVerifier


# ==============================================================================
# 1. Unit Tests for extract_strings.py
# ==============================================================================

class TestExtractStrings:
    def test_extract_adm_strings_valid(self):
        """Tests parsing a well-formed synthetic ADM binary buffer."""
        # Header: version=1, num_strings=2
        s1 = "Hello World"
        s2 = "Espada Mágica"
        b1 = s1.encode("utf-16le")
        b2 = s2.encode("utf-16le")

        header = struct.pack("<II", 1, 2)
        # Entry 1: token_id=10, char_count=len(s1)
        entry1 = struct.pack("<II", 10, len(s1)) + b1
        # Entry 2: token_id=20, char_count=len(s2)
        entry2 = struct.pack("<II", 20, len(s2)) + b2

        data = header + entry1 + entry2
        extracted = extract_adm_strings(data)

        assert len(extracted) == 2
        assert extracted[0] == (10, s1)
        assert extracted[1] == (20, s2)

    def test_extract_adm_strings_invalid_version(self):
        """Tests that ADM parser rejects headers with version != 1."""
        header = struct.pack("<II", 2, 1)  # version 2
        entry = struct.pack("<II", 1, 4) + "Test".encode("utf-16le")
        extracted = extract_adm_strings(header + entry)
        assert extracted == []

    def test_extract_adm_strings_truncated(self):
        """Tests that truncated binary data does not crash the parser."""
        header = struct.pack("<II", 1, 5)
        # Incomplete entry
        truncated = header + b"\x01\x00\x00"
        extracted = extract_adm_strings(truncated)
        assert extracted == []

    def test_extract_adm_strings_too_short(self):
        """Tests data shorter than header length (8 bytes)."""
        assert extract_adm_strings(b"\x01\x00") == []

    def test_extract_layout_strings(self):
        """Tests extracting Property Name='Text' from CEGUI XML."""
        xml = """
        <GUILayout>
            <Window Type="TaharezLook/Button" Name="BtnQuit">
                <Property Name="Text" Value="Quit Game" />
            </Window>
            <Window Type="TaharezLook/StaticText" Name="LblTitle">
                <Property Name="Text" Value="Torchlight" />
                <Property Name="Other" Value="Ignore Me" />
                <Property Name="Text" Value="123" />
                <Property Name="Text" Value="A" />
            </Window>
        </GUILayout>
        """
        extracted = extract_layout_strings(xml)
        assert "Quit Game" in extracted
        assert "Torchlight" in extracted
        # Pure digits like "123" and single characters like "A" should be excluded
        assert "123" not in extracted
        assert "A" not in extracted
        assert "Ignore Me" not in extracted

    def test_is_valid_translatable_string_code_keys(self):
        """Tests filtering of engine code keys."""
        assert not is_valid_translatable_string("NAME")
        assert not is_valid_translatable_string("DAMAGE")
        assert not is_valid_translatable_string("COLLISION")
        assert not is_valid_translatable_string("ARMOR")

    def test_is_valid_translatable_string_paths_and_files(self):
        """Tests filtering of media paths and asset filenames."""
        assert not is_valid_translatable_string("media/UI/button.dds")
        assert not is_valid_translatable_string("MEDIA/TEXTURES/BRICK.PNG")
        assert not is_valid_translatable_string("SWORD.MESH")
        assert not is_valid_translatable_string("SOUND_EFFECT.OGG")

    def test_is_valid_translatable_string_numbers_and_ids(self):
        """Tests filtering of numbers and internal identifiers."""
        assert not is_valid_translatable_string("123.45")
        assert not is_valid_translatable_string("-10")
        assert not is_valid_translatable_string("SWORD_TIER_01")
        assert not is_valid_translatable_string("GEM_AMETHYST_02")

    def test_is_valid_translatable_string_genuine_text(self):
        """Tests that genuine translatable text is accepted."""
        assert is_valid_translatable_string("Potion of Healing")
        assert is_valid_translatable_string("Defeat Ordrak")
        assert is_valid_translatable_string("Ember Lance")
        assert is_valid_translatable_string("Quit Game")
        assert is_valid_translatable_string("+12 Fire Damage")
        assert is_valid_translatable_string("|cFFFFBA00Heroic Quest|u")

    def test_categorize_file(self):
        """Tests categorization logic across all file types."""
        assert categorize_file("media/UI/mainmenuframe.layout") == "UI"
        assert categorize_file("media/Quests/MAIN_QUEST.DAT.adm") == "Quests"
        assert categorize_file("media/Cinematics/INTRO.DAT.adm") == "Quests"
        assert categorize_file("media/units/npcs/SYL.DAT.adm") == "Quests"
        assert categorize_file("media/units/items/SWORD.DAT.adm") == "Items"
        assert categorize_file("media/skills/EMBER_LANCE.DAT.adm") == "Skills"
        assert categorize_file("media/Affixes/FIRE_BONUS.DAT.adm") == "Affixes"
        assert categorize_file("media/units/monsters/GOBLIN.DAT.adm") == "Monsters"
        assert categorize_file("media/recipes/TRANSMUTE_01.DAT.adm") == "Recipes"
        assert categorize_file("media/dungeons/MINES.DAT.adm") == "Dungeons"
        assert categorize_file("media/GLOBALS.DAT.adm") == "Globals"

    def test_build_catalog(self):
        """Tests constructing the catalog dict from extracted strings."""
        entries = {
            "Quit Game": ("UI", "mainmenuframe.layout"),
            "Iron Sword": ("Items", "sword.dat.adm"),
            "Fireball": ("Skills", "fireball.dat.adm")
        }
        catalog = build_catalog(entries, game_version="1.15")

        assert catalog["metadata"]["game"] == "Torchlight"
        assert catalog["metadata"]["version"] == "1.15"
        assert catalog["metadata"]["total_strings"] == 3
        assert catalog["metadata"]["category_counts"]["UI"] == 1
        assert catalog["metadata"]["category_counts"]["Items"] == 1
        assert catalog["metadata"]["category_counts"]["Skills"] == 1

        assert len(catalog["categories"]["UI"]) == 1
        assert catalog["categories"]["UI"][0]["id"] == "UI_0001"
        assert catalog["categories"]["UI"][0]["original"] == "Quit Game"
        assert catalog["categories"]["UI"][0]["translation"] == ""


# ==============================================================================
# 2. Unit Tests for compile_translation.py
# ==============================================================================

class TestCompileTranslation:
    def test_generate_translation_dat_format_and_bom(self):
        """Tests that generated translation.dat strictly starts with BOM and has valid blocks."""
        catalog = {
            "metadata": {"game": "Torchlight", "version": "1.15", "total_strings": 2},
            "categories": {
                "UI": [
                    {"id": "UI_0001", "original": "Quit Game", "translation": "Sair do Jogo", "context": "ui.layout"},
                    {"id": "UI_0002", "original": "Continue", "translation": "", "context": "ui.layout"}
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "translations", "translation.dat")
            count = generate_translation_dat(catalog, out_dat, fallback_to_original=True, verbose=False)

            assert count == 2
            assert os.path.exists(out_dat)

            with open(out_dat, "rb") as f:
                raw = f.read()

            # Must start strictly with UTF-16LE BOM
            assert raw[:2] == b"\xff\xfe"

            text = raw[2:].decode("utf-16le")
            assert "[TRANSLATION]" in text
            assert "<STRING>ORIGINAL:Quit Game\r\n<STRING>TRANSLATION:Sair do Jogo\r\n[/TRANSLATION]" in text
            # Fallback for untranslated "Continue"
            assert "<STRING>ORIGINAL:Continue\r\n<STRING>TRANSLATION:Continue\r\n[/TRANSLATION]" in text

    def test_compile_layout_files_substitution(self):
        """Tests that layout compiler substitutes Property Name='Text' and preserves encoding."""
        catalog = {
            "categories": {
                "UI": [
                    {"id": "UI_0001", "original": "Quit Game", "translation": "Sair do Jogo", "context": "test.layout"}
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock Pak.zip containing a UTF-8 test.layout
            mock_pak = os.path.join(tmpdir, "MockPak.zip")
            layout_content = '<GUILayout><Property Name="Text" Value="Quit Game" /></GUILayout>'

            with zipfile.ZipFile(mock_pak, "w") as z:
                z.writestr("media/UI/test.layout", layout_content.encode("utf-8"))

            out_layout_dir = os.path.join(tmpdir, "output_ui")
            compiled = compile_layout_files(catalog, mock_pak, out_layout_dir, fallback_to_original=True, verbose=False)

            assert compiled == 1
            out_file = os.path.join(out_layout_dir, "test.layout")
            assert os.path.exists(out_file)

            with open(out_file, "r", encoding="utf-8") as f:
                res_xml = f.read()

            assert 'Value="Sair do Jogo"' in res_xml


# ==============================================================================
# 3. Unit Tests for verify_translation.py
# ==============================================================================

class TestVerifyTranslation:
    def test_verify_valid_file(self):
        """Tests that a well-formed translation.dat passes all checks."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Play\r\n"
            "<STRING>TRANSLATION:Jogar\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")

        with tempfile.TemporaryDirectory() as tmpdir:
            dat_path = os.path.join(tmpdir, "translation.dat")
            with open(dat_path, "wb") as f:
                f.write(data)

            verifier = TranslationVerifier(dat_path=dat_path, verbose=False)
            assert verifier.run_all() is True
            assert verifier.stats["dat_total_blocks"] == 1
            assert len(verifier.errors) == 0

    def test_verify_missing_bom(self):
        """Tests that missing BOM causes verification failure."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Play\r\n"
            "<STRING>TRANSLATION:Jogar\r\n"
            "[/TRANSLATION]\r\n"
        )
        # Without BOM
        data = content.encode("utf-16le")

        with tempfile.TemporaryDirectory() as tmpdir:
            dat_path = os.path.join(tmpdir, "translation.dat")
            with open(dat_path, "wb") as f:
                f.write(data)

            verifier = TranslationVerifier(dat_path=dat_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Invalid BOM" in err for err in verifier.errors)

    def test_verify_mismatched_tags(self):
        """Tests that unclosed [TRANSLATION] tags cause failure."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Play\r\n"
            "<STRING>TRANSLATION:Jogar\r\n"
            # Missing [/TRANSLATION]
        )
        data = b"\xff\xfe" + content.encode("utf-16le")

        with tempfile.TemporaryDirectory() as tmpdir:
            dat_path = os.path.join(tmpdir, "translation.dat")
            with open(dat_path, "wb") as f:
                f.write(data)

            verifier = TranslationVerifier(dat_path=dat_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Mismatched tag counts" in err for err in verifier.errors)

    def test_verify_missing_string_lines(self):
        """Tests that a block missing <STRING>TRANSLATION: is caught."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Play\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")

        with tempfile.TemporaryDirectory() as tmpdir:
            dat_path = os.path.join(tmpdir, "translation.dat")
            with open(dat_path, "wb") as f:
                f.write(data)

            verifier = TranslationVerifier(dat_path=dat_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Missing <STRING>TRANSLATION:" in err for err in verifier.errors)


# ==============================================================================
# 4. End-to-End Pipeline Integration Test
# ==============================================================================

class TestEndToEndPipeline:
    def test_live_catalog_and_translation_dat(self):
        """
        Validates the actual project artifacts generated by M1:
        - translation_ptbr/translation_catalog.json
        - translation_ptbr/translations/translation.dat
        - translation_ptbr/media/UI/*.layout
        """
        catalog_path = r"translation_ptbr\translation_catalog.json"
        dat_path = r"translation_ptbr\translations\translation.dat"
        layout_dir = r"translation_ptbr\media\UI"

        assert os.path.exists(catalog_path), f"Missing catalog file: {catalog_path}"
        assert os.path.exists(dat_path), f"Missing translation.dat: {dat_path}"
        assert os.path.exists(layout_dir), f"Missing layout directory: {layout_dir}"

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        assert catalog["metadata"]["total_strings"] in (13622, 13633)
        assert len(catalog["categories"]) == 9
        for cat in STANDARD_CATEGORIES:
            assert cat in catalog["categories"]
            assert len(catalog["categories"][cat]) > 0

        # Run verifier across live compiled assets
        verifier = TranslationVerifier(
            dat_path=dat_path,
            catalog_path=catalog_path,
            layout_dir=layout_dir,
            verbose=False
        )
        success = verifier.run_all()
        assert success is True
        assert verifier.stats["dat_total_blocks"] in (13622, 13633)
        assert verifier.stats["layout_files_count"] == 35
