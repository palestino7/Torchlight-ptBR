"""
tests/test_adversarial_m1.py - Empirical Adversarial Stress-Test Suite for Milestone 1 Tools

Adversarially challenges and stress-tests:
- tools/extract_strings.py
- tools/compile_translation.py
- tools/verify_translation.py

Empirically tests and documents:
1. Binary ADM parser resilience under truncated headers, corrupt versions, huge string counts, integer bounds, null bytes, and fuzzing
2. CEGUI XML layout parsing with adversarial XML injections, malformed tags, and entity handling
3. Text filtering rules, leaked asset paths, and numeric edge cases
4. DAT compilation syntax, BOM UTF-16LE compliance, and multiline text handling
5. Verification tool detection capabilities (missing BOM, invalid UTF-16LE, mismatched tags, duplicate keys, format tags)
6. CLI entry points error handling under missing or invalid files
"""

import html
import json
import os
import random
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import pytest

from tools.extract_strings import (
    extract_adm_strings,
    extract_layout_strings,
    is_valid_translatable_string,
    categorize_file,
    build_catalog,
    STANDARD_CATEGORIES,
    NON_TRANSLATABLE_EXTENSIONS
)
from tools.compile_translation import (
    load_catalog,
    generate_translation_dat,
    compile_layout_files,
    build_translation_map
)
from tools.verify_translation import TranslationVerifier


# ==============================================================================
# 1. Adversarial Stress-Testing: extract_adm_strings
# ==============================================================================

class TestAdversarialExtractAdm:
    """Stress-tests the ADM parser with corrupt binary streams, fuzzing, and extreme boundaries."""

    def test_empty_buffer(self):
        """0-byte buffer must return empty list without crashing."""
        assert extract_adm_strings(b"") == []

    @pytest.mark.parametrize("length", [1, 2, 3, 4, 5, 6, 7])
    def test_truncated_header_boundaries(self, length):
        """Headers truncated before 8-byte minimum boundary must return empty list."""
        assert extract_adm_strings(b"\x01\x00\x00\x00\x05\x00\x00"[:length]) == []

    @pytest.mark.parametrize("invalid_version", [0, 2, 3, 100, 0xFFFFFFFF, 0x80000000])
    def test_unsupported_versions(self, invalid_version):
        """Any version other than 1 must be cleanly rejected."""
        header = struct.pack("<II", invalid_version, 10)
        assert extract_adm_strings(header + b"\x00" * 20) == []

    def test_astronomical_num_strings_with_truncated_data(self):
        """
        Adversarial header claiming 4 billion strings with only 8 bytes of payload.
        Parser must terminate immediately without hanging, looping excessively, or OOMing.
        """
        header = struct.pack("<II", 1, 0xFFFFFFFF)
        payload = header + b"\x01\x02\x03\x04"
        res = extract_adm_strings(payload)
        assert res == []

    def test_astronomical_char_count_buffer_overflow_attempt(self):
        """
        String entry claiming char_count = 0x7FFFFFFF (1.5 billion chars).
        Parser must respect data bounds and not attempt huge memory allocations.
        """
        header = struct.pack("<II", 1, 1)
        bad_entry = struct.pack("<II", 1, 0x7FFFFFFF) + b"ABCD"
        res = extract_adm_strings(header + bad_entry)
        assert res == []

    def test_zero_char_count_entry(self):
        """String entry with char_count = 0 (empty string in ADM table)."""
        header = struct.pack("<II", 1, 1)
        entry = struct.pack("<II", 100, 0)
        res = extract_adm_strings(header + entry)
        assert res == [(100, "")]

    def test_embedded_null_characters_in_adm_string(self):
        """ADM string containing embedded null characters must decode safely."""
        text = "Sword\x00Of\x00Valor\x00"
        text_bytes = text.encode("utf-16le")
        header = struct.pack("<II", 1, 1)
        entry = struct.pack("<II", 101, len(text)) + text_bytes
        res = extract_adm_strings(header + entry)
        assert len(res) == 1
        assert res[0] == (101, text)

    def test_unpaired_utf16_surrogate_in_adm(self):
        """ADM string containing invalid unpaired UTF-16 surrogate bytes must not raise exception."""
        invalid_surrogate_bytes = b"\x00\xd8\x00\xd8"
        header = struct.pack("<II", 1, 1)
        entry = struct.pack("<II", 102, 2) + invalid_surrogate_bytes
        res = extract_adm_strings(header + entry)
        assert len(res) == 1
        assert res[0][0] == 102

    def test_fuzzed_random_adm_payloads(self):
        """100 randomized byte sequences fed to extract_adm_strings must never crash."""
        rng = random.Random(42)
        for _ in range(100):
            payload_len = rng.randint(0, 256)
            payload = rng.randbytes(payload_len)
            result = extract_adm_strings(payload)
            assert isinstance(result, list)


# ==============================================================================
# 2. Adversarial Stress-Testing: extract_layout_strings & CEGUI XML
# ==============================================================================

class TestAdversarialExtractLayout:
    """Stress-tests layout XML extraction with corrupt XML, malformed tags, and injection payloads."""

    def test_malformed_xml_unclosed_tag(self):
        """Parser must not crash when encountering broken XML syntax."""
        broken_xml = '<Property Name="Text" Value="Broken string without closing'
        res = extract_layout_strings(broken_xml)
        assert res == []

    def test_layout_text_with_special_characters_and_entities(self):
        """Layout containing XML entities and special symbols."""
        xml = '<Property Name="Text" Value="HP &amp; MP + 50%" />'
        res = extract_layout_strings(xml)
        assert "HP & MP + 50%" in res
        assert "HP &amp; MP + 50%" not in res

    def test_layout_text_with_multiline_content(self):
        """Layout with multiline text value."""
        xml = '<Property Name="Text" Value="Primeira Linha\nSegunda Linha" />'
        res = extract_layout_strings(xml)
        assert len(res) == 1
        assert "Primeira Linha\nSegunda Linha" in res

    def test_layout_filtering_single_char_and_digits(self):
        """Verifies filtering of purely numeric or single-character values."""
        xml = """
        <Property Name="Text" Value="0" />
        <Property Name="Text" Value="999" />
        <Property Name="Text" Value="X" />
        <Property Name="Text" Value=" " />
        <Property Name="Text" Value="Start Game" />
        """
        res = extract_layout_strings(xml)
        assert res == ["Start Game"]

    def test_extreme_length_layout_text(self):
        """Layout containing extremely large text string (32KB)."""
        huge_text = "A" * 32768
        xml = f'<Property Name="Text" Value="{huge_text}" />'
        res = extract_layout_strings(xml)
        assert len(res) == 1
        assert res[0] == huge_text


# ==============================================================================
# 3. Adversarial Stress-Testing: Filtering & Leaked Asset Verification
# ==============================================================================

class TestAdversarialFilteringAndCategorization:
    """Stress-tests text validity filtering and category path routing."""

    @pytest.mark.parametrize("invalid_str", [
        "", " ", "\t\n", "A", "1", "123", "-45.67",
        "NAME", "ICON", "TEXTURE", "MESH", "ANIMATION",
        "media/ui/icons/test.png", "MEDIA/GRAPHICS/TEST.DDS",
        "SWORD_T01", "GEM_RUBY_05", "MONSTER_BOSS_01"
    ])
    def test_filtering_rejects_non_translatable_tokens(self, invalid_str):
        assert is_valid_translatable_string(invalid_str) is False

    @pytest.mark.parametrize("valid_str", [
        "Espada Flamejante", "Poção de Vida", "Destroyer",
        "Requer Nível 20", "Sair do Jogo", "Nova Aventura",
        "|cFFFFBA00Ouro|u", "Alchemist's Robe", "Defesa +15"
    ])
    def test_filtering_accepts_valid_translatable_text(self, valid_str):
        assert is_valid_translatable_string(valid_str) is True

    @pytest.mark.parametrize("path,expected_cat", [
        ("media/UI/mainmenu.layout", "UI"),
        ("media/UI/DIALOGS/CHAT.LAYOUT", "UI"),
        ("media/units/items/swords/fire_sword.dat.adm", "Items"),
        ("media/units/monsters/boss_alchemist.dat.adm", "Monsters"),
        ("media/quests/act1/main_quest.dat.adm", "Quests"),
        ("media/skills/destroyer/slash.dat.adm", "Skills"),
        ("media/affixes/magic/elemental.dat.adm", "Affixes"),
        ("media/recipes/transmute_gems.dat.adm", "Recipes"),
        ("media/dungeons/catacombs/level1.dat.adm", "Dungeons"),
        ("media/unknown_dir/misc.dat.adm", "Globals"),
    ])
    def test_categorization_path_mapping(self, path, expected_cat):
        assert categorize_file(path) == expected_cat

    def test_remediation_lowercase_asset_extensions_filtered(self):
        """
        [REMEDIATION VERIFICATION]
        is_valid_translatable_string() correctly filters lowercase asset file extensions
        like 'sound.wav', 'music.ogg', 'font.ttf', 'model.mesh'.
        """
        leaked_files = ["sound.wav", "music.ogg", "font.ttf", "model.mesh", "texture.png"]
        for f in leaked_files:
            assert is_valid_translatable_string(f) is False, f"Expected {f} to be filtered"

    def test_remediation_windows_backslash_paths_filtered(self):
        """
        [REMEDIATION VERIFICATION]
        is_valid_translatable_string() normalizes path separators, filtering Windows
        backslash paths like 'media\\units\\items\\base.dat'.
        """
        windows_path = r"media\units\items\base.dat"
        assert is_valid_translatable_string(windows_path) is False, "Windows backslash paths must be filtered"

    def test_remediation_positive_number_filtering(self):
        r"""
        [REMEDIATION VERIFICATION]
        Regex r'^[+-]?[0-9\.]+$' filters positive numbers with explicit plus sign, e.g. '+100'.
        """
        assert is_valid_translatable_string("+100") is False, "+100 must be filtered"
        assert is_valid_translatable_string("+15") is False
        assert is_valid_translatable_string("+0.5") is False


# ==============================================================================
# 4. Adversarial Stress-Testing: compile_translation.py
# ==============================================================================

class TestAdversarialCompileTranslation:
    """Stress-tests catalog loading, format escaping, and DAT generation."""

    def test_load_catalog_missing_file(self):
        """Missing catalog file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_catalog("non_existent_catalog_path_999.json")

    def test_load_catalog_malformed_json(self):
        """Corrupted JSON syntax raises json.JSONDecodeError."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            f.write("{invalid_json: 123,")
            temp_path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                load_catalog(temp_path)
        finally:
            os.remove(temp_path)

    def test_load_catalog_missing_categories_key(self):
        """Catalog missing 'categories' root key raises ValueError."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump({"metadata": {"version": "1.15"}}, f)
            temp_path = f.name
        try:
            with pytest.raises(ValueError, match="missing 'categories' key"):
                load_catalog(temp_path)
        finally:
            os.remove(temp_path)

    def test_compile_translation_dat_with_delimiter_injection(self):
        """
        Adversarial payload injection: string containing [TRANSLATION] tags.
        Checks how compile_translation and verify_translation behave with tag injection.
        """
        catalog = {
            "categories": {
                "Quests": [
                    {
                        "original": "Normal Text",
                        "translation": "Texto [/TRANSLATION]\r\n[TRANSLATION]\r\n<STRING>ORIGINAL:Hacked",
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dat = os.path.join(tmp_dir, "translation.dat")
            generate_translation_dat(catalog, out_dat, fallback_to_original=False, verbose=False)
            
            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            result = verifier.run_all()
            assert result is False
            assert len(verifier.errors) > 0

    def test_compile_translation_dat_utf16le_bom_strictness(self):
        """Compiled translation.dat must start strictly with 0xFF 0xFE and use CRLF."""
        catalog = {
            "categories": {
                "UI": [
                    {"original": "Quit", "translation": "Sair"},
                    {"original": "Options", "translation": "Opções"}
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dat = os.path.join(tmp_dir, "translation.dat")
            count = generate_translation_dat(catalog, out_dat, fallback_to_original=False, verbose=False)
            assert count == 2

            with open(out_dat, "rb") as f:
                raw = f.read()

            assert raw.startswith(b"\xff\xfe")
            content = raw[2:].decode("utf-16le")
            assert "\r\n" in content
            assert "<STRING>ORIGINAL:Quit\r\n" in content
            assert "<STRING>TRANSLATION:Sair\r\n" in content

    def test_compile_layout_xml_substitution_and_escaping(self):
        """
        Layout compilation substitutes text and escapes special XML characters (&, <, >, ", ').
        """
        catalog = {
            "categories": {
                "UI": [
                    {
                        "original": "Items & Spells",
                        "translation": "Itens & Feitiços <Poderosos>"
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            pak_path = os.path.join(tmp_dir, "Pak.zip")
            out_ui_dir = os.path.join(tmp_dir, "media", "UI")

            # Mock layout matching catalog original
            mock_xml = (
                '<GUILayout>\n'
                '  <Window Type="Button" Name="Btn">\n'
                '    <Property Name="Text" Value="Items & Spells" />\n'
                '  </Window>\n'
                '</GUILayout>'
            )
            with zipfile.ZipFile(pak_path, "w") as z:
                z.writestr("media/UI/test.layout", mock_xml.encode("utf-8"))

            count = compile_layout_files(catalog, pak_path, out_ui_dir, fallback_to_original=False, verbose=False)
            assert count == 1

            out_layout_file = os.path.join(out_ui_dir, "test.layout")
            with open(out_layout_file, "r", encoding="utf-8") as f:
                compiled_xml = f.read()

            # Must be valid XML parsable by ElementTree
            root = ET.fromstring(compiled_xml)
            assert root is not None
            # Check escaped property value
            assert "&amp;" in compiled_xml
            assert "&lt;" in compiled_xml
            assert "&gt;" in compiled_xml

    def test_remediation_multiline_translation_escapes_newlines(self):
        """
        [REMEDIATION VERIFICATION]
        generate_translation_dat() escapes raw newlines to literal \\n,
        preventing line splits in translation.dat.
        verify_translation.py verifies the block cleanly.
        """
        catalog = {
            "categories": {
                "Quests": [
                    {
                        "original": "Multiline Quest",
                        "translation": "Linha 1\nLinha 2"
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dat = os.path.join(tmp_dir, "translation.dat")
            generate_translation_dat(catalog, out_dat, verbose=False)

            with open(out_dat, "rb") as f:
                raw = f.read()
            text = raw[2:].decode("utf-16le")

            # The DAT file now contains properly escaped newline on a single line
            assert "<STRING>TRANSLATION:Linha 1\\nLinha 2" in text

            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            res = verifier.run_all()
            assert res is True
            assert len(verifier.errors) == 0

    def test_remediation_verifier_catches_unparsed_line_fragments(self):
        """
        [REMEDIATION VERIFICATION]
        verify_translation.py rejects unparsed line fragments / severed multiline text
        with fatal errors.
        """
        raw_broken_dat = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Quest\r\n"
            "<STRING>TRANSLATION:Linha 1\r\n"
            "Linha 2 Severed\r\n"
            "[/TRANSLATION]\r\n"
        )
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe" + raw_broken_dat.encode("utf-16le"))
            tmp = f.name
        try:
            verifier = TranslationVerifier(dat_path=tmp, verbose=False)
            res = verifier.run_all()
            assert res is False
            assert any("Unrecognized token or unescaped multiline fragment 'Linha 2 Severed'" in e for e in verifier.errors)
        finally:
            os.remove(tmp)


# ==============================================================================
# 5. Adversarial Stress-Testing: verify_translation.py
# ==============================================================================

class TestAdversarialVerifyTranslation:
    """Stress-tests the verifier against all forms of corruption and anomalies."""

    def test_verify_nonexistent_file(self):
        """Non-existent translation.dat must fail with 'File not found'."""
        verifier = TranslationVerifier(dat_path="non_existent_file.dat", verbose=False)
        assert verifier.run_all() is False
        assert any("File not found" in e for e in verifier.errors)

    def test_verify_zero_byte_file(self):
        """Empty file (0 bytes) must fail with 'File is empty'."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("empty" in e.lower() for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_single_byte_file(self):
        """File too short for BOM (1 byte) must fail."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff")
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("too short" in e.lower() for e in verifier.errors)
        finally:
            os.remove(temp_path)

    @pytest.mark.parametrize("bad_bom,label", [
        (b"\xef\xbb\xbf", "UTF-8 BOM"),
        (b"\xfe\xff", "UTF-16BE BOM"),
        (b"\x00\x00\xfe\xff", "UTF-32BE BOM"),
        (b"NO", "ASCII text without BOM"),
        (b"\x00\x01", "Arbitrary bytes")
    ])
    def test_verify_rejects_invalid_bom(self, bad_bom, label):
        """Any BOM other than 0xFF 0xFE must be rejected with an Invalid BOM error."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(bad_bom + "[TRANSLATION]\r\n[/TRANSLATION]\r\n".encode("utf-8"))
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Invalid BOM" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_odd_byte_length_utf16le_decode_error(self):
        """Stream with odd number of bytes after BOM must fail UTF-16LE decoding."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe\x61\x00\x62")
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("decoding error" in e.lower() for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_unbalanced_tags_extra_open(self):
        """Extra [TRANSLATION] tag must fail verification."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:A\r\n"
            "<STRING>TRANSLATION:B\r\n"
            "[/TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Mismatched tag counts" in e or "Unterminated" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_unbalanced_tags_extra_close(self):
        """Extra [/TRANSLATION] tag must fail verification."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:A\r\n"
            "<STRING>TRANSLATION:B\r\n"
            "[/TRANSLATION]\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Mismatched tag counts" in e or "without matching" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_nested_open_tags(self):
        """Opening a [TRANSLATION] block inside an already opened block must fail."""
        content = (
            "[TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:A\r\n"
            "<STRING>TRANSLATION:B\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("already inside a translation block" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_missing_original_line(self):
        """Block missing <STRING>ORIGINAL: must fail."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>TRANSLATION:Translation Only\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Missing <STRING>ORIGINAL:" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_missing_translation_line(self):
        """Block missing <STRING>TRANSLATION: must fail."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Original Only\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Missing <STRING>TRANSLATION:" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_duplicate_original_line_in_block(self):
        """Block containing duplicate <STRING>ORIGINAL: must fail."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Original 1\r\n"
            "<STRING>ORIGINAL:Original 2\r\n"
            "<STRING>TRANSLATION:Trans\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Duplicate <STRING>ORIGINAL:" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_duplicate_translation_line_in_block(self):
        """Block containing duplicate <STRING>TRANSLATION: must fail."""
        content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Original\r\n"
            "<STRING>TRANSLATION:Trans 1\r\n"
            "<STRING>TRANSLATION:Trans 2\r\n"
            "[/TRANSLATION]\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("Duplicate <STRING>TRANSLATION:" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_orphan_string_lines_outside_block(self):
        """<STRING>ORIGINAL: or <STRING>TRANSLATION: outside [TRANSLATION] block must fail."""
        content = (
            "<STRING>ORIGINAL:Orphan\r\n"
            "<STRING>TRANSLATION:Orphan Trans\r\n"
        )
        data = b"\xff\xfe" + content.encode("utf-16le")
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(data)
            temp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=temp_path, verbose=False)
            assert verifier.run_all() is False
            assert any("outside a [TRANSLATION] block" in e for e in verifier.errors)
        finally:
            os.remove(temp_path)

    def test_verify_catalog_cross_check_detects_missing_strings(self):
        """Verifier must detect and report catalog strings that are missing from translation.dat."""
        dat_content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Item 1\r\n"
            "<STRING>TRANSLATION:Item 1 pt\r\n"
            "[/TRANSLATION]\r\n"
        )
        catalog = {
            "categories": {
                "Items": [
                    {"original": "Item 1", "translation": "Item 1 pt"},
                    {"original": "Item 2 Missing", "translation": "Item 2 pt"}
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            dat_path = os.path.join(tmp_dir, "translation.dat")
            cat_path = os.path.join(tmp_dir, "catalog.json")

            with open(dat_path, "wb") as f:
                f.write(b"\xff\xfe" + dat_content.encode("utf-16le"))
            with open(cat_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f)

            verifier = TranslationVerifier(dat_path=dat_path, catalog_path=cat_path, verbose=False)
            assert verifier.run_all() is False
            assert any("missing in translation.dat" in e for e in verifier.errors)

    def test_verify_layout_dir_catches_empty_file(self):
        """Verifier must detect empty .layout files inside layout_dir."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dat_content = (
                "[TRANSLATION]\r\n"
                "<STRING>ORIGINAL:OK\r\n"
                "<STRING>TRANSLATION:OK\r\n"
                "[/TRANSLATION]\r\n"
            )
            dat_path = os.path.join(tmp_dir, "translation.dat")
            with open(dat_path, "wb") as f:
                f.write(b"\xff\xfe" + dat_content.encode("utf-16le"))

            layout_dir = os.path.join(tmp_dir, "layouts")
            os.makedirs(layout_dir, exist_ok=True)
            empty_layout = os.path.join(layout_dir, "broken.layout")
            with open(empty_layout, "wb") as f:
                pass

            verifier = TranslationVerifier(dat_path=dat_path, layout_dir=layout_dir, verbose=False)
            assert verifier.run_all() is False
            assert any("Layout file is empty" in e for e in verifier.errors)

    def test_remediation_verifier_detects_duplicate_original_keys(self):
        """
        [REMEDIATION VERIFICATION]
        verify_translation.py tracks original keys and emits fatal errors on duplicate
        [TRANSLATION] blocks for the same original string.
        """
        dat_content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Sword\r\n"
            "<STRING>TRANSLATION:Espada\r\n"
            "[/TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Sword\r\n"
            "<STRING>TRANSLATION:Espada 2\r\n"
            "[/TRANSLATION]\r\n"
        )
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe" + dat_content.encode("utf-16le"))
            tmp = f.name
        try:
            verifier = TranslationVerifier(dat_path=tmp, verbose=False)
            result = verifier.run_all()
            assert result is False, "Verifier must reject duplicate original keys"
            assert any("Duplicate ORIGINAL text 'Sword'" in e for e in verifier.errors)
        finally:
            os.remove(tmp)

    def test_remediation_verifier_catches_corrupt_formatting_tags(self):
        """
        [REMEDIATION VERIFICATION]
        verify_translation.py validates formatting color tags (|c...|u)
        and format specifiers (%s, %d).
        """
        dat_content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Requires |cFFFFBA00Level %d|u\r\n"
            "<STRING>TRANSLATION:Requer |cBrokenHex Nivel %s sem fechar tag\r\n"
            "[/TRANSLATION]\r\n"
        )
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe" + dat_content.encode("utf-16le"))
            tmp = f.name
        try:
            verifier = TranslationVerifier(dat_path=tmp, verbose=False)
            result = verifier.run_all()
            assert result is False
            assert len(verifier.errors) > 0
            assert any("Malformed hex color tag" in e for e in verifier.errors)
        finally:
            os.remove(tmp)

    def test_remediation_percentage_in_prose_not_flagged(self):
        """
        [REMEDIATION VERIFICATION]
        Format specifier regex does not flag prose percentages (e.g. '30% of DPS', '10% chance to stun').
        """
        orig = "Deals 30% of weapon DPS and 10% chance to stun for 3 seconds."
        trans = "Causa 30% do DPS da arma e 10% de chance de atordoar por 3 segundos."
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert errors == []

    def test_remediation_printf_sequence_mismatch_detected(self):
        """
        [REMEDIATION VERIFICATION]
        Swapped printf specifiers (%d then %s vs %s then %d) are rejected for C++ engine safety.
        """
        orig = "Level %d: %s"
        trans = "%s: Nível %d"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Format specifier mismatch" in e for e in errors)

    def test_remediation_bracket_token_mismatch_detected(self):
        """
        [REMEDIATION VERIFICATION]
        Engine bracket tokens ([ITEM], [VALUE]) translated or missing must fail validation.
        """
        orig = "Find [ITEM] at depth [DEPTH]"
        trans = "Encontre [OBJETO] na profundidade [DEPTH]"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Engine bracket token mismatch" in e for e in errors)

    def test_remediation_catalog_duplicate_keys_detected(self):
        """
        [REMEDIATION VERIFICATION]
        Catalog cross-check fails when duplicate original keys appear in catalog.
        """
        catalog = {
            "categories": {
                "UI": [
                    {"id": "UI_0001", "original": "Gold", "translation": "Ouro"}
                ],
                "Items": [
                    {"id": "Items_0001", "original": "Gold", "translation": "Ouro"}
                ]
            }
        }
        dat_content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Gold\r\n"
            "<STRING>TRANSLATION:Ouro\r\n"
            "[/TRANSLATION]\r\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            cat_path = os.path.join(tmp_dir, "catalog.json")
            dat_path = os.path.join(tmp_dir, "translation.dat")
            with open(cat_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f)
            with open(dat_path, "wb") as f:
                f.write(b"\xff\xfe" + dat_content.encode("utf-16le"))

            verifier = TranslationVerifier(dat_path=dat_path, catalog_path=cat_path, verbose=False)
            res = verifier.run_all()
            assert res is False
            assert any("Catalog duplicate key" in e for e in verifier.errors)


# ==============================================================================
# 6. CLI Entry Points & Unhandled Crash Resistance
# ==============================================================================

class TestCLIResilience:
    """Tests CLI entry points under bad parameters to verify clean exits without unhandled tracebacks."""

    def test_extract_strings_cli_help(self):
        cmd = [sys.executable, "tools/extract_strings.py", "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "usage:" in res.stdout.lower()

    def test_extract_strings_cli_missing_pak(self):
        cmd = [sys.executable, "tools/extract_strings.py", "--pak-path", "non_existent_pak.zip", "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 1
        assert "not found" in res.stderr.lower()

    def test_compile_translation_cli_help(self):
        cmd = [sys.executable, "tools/compile_translation.py", "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "usage:" in res.stdout.lower()

    def test_compile_translation_cli_missing_catalog(self):
        cmd = [sys.executable, "tools/compile_translation.py", "--catalog", "non_existent.json", "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 1
        assert "failed to load catalog" in res.stderr.lower()

    def test_verify_translation_cli_help(self):
        cmd = [sys.executable, "tools/verify_translation.py", "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "usage:" in res.stdout.lower()

    def test_verify_translation_cli_missing_dat(self):
        cmd = [sys.executable, "tools/verify_translation.py", "--dat-path", "non_existent.dat", "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 1
