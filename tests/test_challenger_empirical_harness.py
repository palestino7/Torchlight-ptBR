"""
tests/test_challenger_empirical_harness.py - Empirical Adversarial Challenge Suite (Iteration 2)

Deep empirical challenge tests for:
- Challenge 1: Asset path & extension filtering in tools/extract_strings.py
- Challenge 2: CEGUI XML entity handling in layouts and translation
- Challenge 3: Duplicate key detection in tools/verify_translation.py (DAT and catalog)
- Challenge 4: Multiline text newline escaping (\\n) and fatal rejection of severed fragments
- Challenge 5: Formatting tag validation (|c...|u, specifiers %s/%d, bracket tokens)
- Challenge 6: Numeric regex with leading plus signs (+100)
"""

import html
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
import pytest

from tools.extract_strings import (
    is_valid_translatable_string,
    extract_layout_strings,
    extract_adm_strings,
    NON_TRANSLATABLE_EXTENSIONS,
    CODE_KEYS
)
from tools.compile_translation import (
    escape_xml_attr,
    build_translation_map,
    generate_translation_dat,
    compile_layout_files
)
from tools.verify_translation import TranslationVerifier


# ==============================================================================
# Challenge 1 & 6: Asset Filtering & Numeric Edge Cases
# ==============================================================================

class TestChallenge1And6AssetAndNumericFiltering:
    """Empirical verification of asset filtering and numeric edge cases."""

    def test_live_catalog_has_zero_asset_leaks(self):
        catalog_path = "translation_ptbr/translation_catalog.json"
        assert os.path.exists(catalog_path), f"Catalog not found: {catalog_path}"
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        leaked_extensions = (
            ".dds", ".mesh", ".png", ".ogg", ".wav", ".material", ".skeleton",
            ".layout", ".font", ".ttf", ".dat", ".adm", ".mp3", ".hlsl", ".cg"
        )
        forbidden_prefixes = ("media/", "../", "./", "dataeditor/")

        leaks = []
        for cat_name, entries in catalog.get("categories", {}).items():
            for item in entries:
                orig = item.get("original", "")
                norm = orig.replace("\\", "/").lower()
                if any(norm.endswith(ext) for ext in leaked_extensions):
                    leaks.append((cat_name, item.get("id"), orig, "extension"))
                if norm.startswith(forbidden_prefixes):
                    leaks.append((cat_name, item.get("id"), orig, "prefix"))
                if "/" in norm and " " not in orig:
                    leaks.append((cat_name, item.get("id"), orig, "path_token"))
                if re.match(r"^[+-]?[0-9\.]+$", orig.strip()):
                    leaks.append((cat_name, item.get("id"), orig, "numeric"))

        assert len(leaks) == 0, f"Found {len(leaks)} leaks in live catalog: {leaks[:10]}"

    @pytest.mark.parametrize("ext", NON_TRANSLATABLE_EXTENSIONS)
    @pytest.mark.parametrize("case_mod", [str.lower, str.upper, str.title])
    def test_all_non_translatable_extensions_rejected_any_case(self, ext, case_mod):
        filename = f"asset_file{case_mod(ext)}"
        assert is_valid_translatable_string(filename) is False, f"Failed to reject: {filename}"

    @pytest.mark.parametrize("prefix", ["media", "MEDIA", "Media", "mEdIa"])
    @pytest.mark.parametrize("slash", ["/", "\\", "\\\\"])
    def test_media_prefix_rejected_any_case_any_slash(self, prefix, slash):
        path = f"{prefix}{slash}some_asset"
        assert is_valid_translatable_string(path) is False, f"Failed to reject: {path}"

    @pytest.mark.parametrize("num_str", [
        "+100", "+15", "+0.5", "+0", "+0.0", "+999999",
        "-100", "-15", "-0.5", "-0", "-0.0", "-999999",
        "0", "1", "42", "123.456", "0.001", "-0.001"
    ])
    def test_pure_numbers_rejected_with_any_sign(self, num_str):
        assert is_valid_translatable_string(num_str) is False, f"Failed to reject pure number: {num_str}"

    @pytest.mark.parametrize("translatable_text", [
        "+15 Strength", "Defesa +100", "Health: +50", "Level 1: +10% Damage",
        "Reduz dano em -5%", "Poção de Vida (+500 HP)", "30% of DPS"
    ])
    def test_numbers_within_translatable_text_accepted(self, translatable_text):
        assert is_valid_translatable_string(translatable_text) is True, f"Incorrectly rejected text: {translatable_text}"


# ==============================================================================
# Challenge 2: CEGUI XML Entity Handling
# ==============================================================================

class TestChallenge2XmlEntityHandling:
    """Empirical verification of XML entity unescaping and idempotent re-escaping."""

    def test_extract_layout_strings_unescapes_entities(self):
        xml = '<Property Name="Text" Value="Arundel&apos;s Dreadaxe &amp; &quot;Shield&quot; &lt;Legendary&gt;" />'
        extracted = extract_layout_strings(xml)
        assert len(extracted) == 1
        assert extracted[0] == "Arundel's Dreadaxe & \"Shield\" <Legendary>"

    def test_escape_xml_attr_is_idempotent(self):
        raw = "Arundel's Dreadaxe & \"Shield\" <Legendary>"
        escaped_once = escape_xml_attr(raw)
        assert escaped_once == "Arundel&apos;s Dreadaxe &amp; &quot;Shield&quot; &lt;Legendary&gt;"
        escaped_twice = escape_xml_attr(escaped_once)
        assert escaped_twice == escaped_once, "escape_xml_attr must not double-escape pre-existing entities"

    def test_build_translation_map_dual_key_support(self):
        catalog = {
            "categories": {
                "UI": [
                    {
                        "original": "Arundel's Dreadaxe",
                        "translation": "Machado Terrível de Arundel"
                    }
                ]
            }
        }
        mapping = build_translation_map(catalog, fallback_to_original=True)
        # Both unescaped and escaped forms must be queryable
        assert "Arundel's Dreadaxe" in mapping
        assert mapping["Arundel's Dreadaxe"] == "Machado Terrível de Arundel"

    def test_compile_layout_replaces_both_escaped_and_unescaped_entities(self):
        catalog = {
            "categories": {
                "UI": [
                    {
                        "original": "Arundel's Dreadaxe",
                        "translation": "Machado de Arundel & Glória"
                    }
                ]
            }
        }
        import zipfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            pak_path = os.path.join(tmp_dir, "Pak.zip")
            out_dir = os.path.join(tmp_dir, "media", "UI")

            # Layout with XML entity in attribute
            layout_content = (
                '<GUILayout>\n'
                '  <Window Type="DefaultWindow" Name="Root">\n'
                '    <Property Name="Text" Value="Arundel&apos;s Dreadaxe" />\n'
                '  </Window>\n'
                '</GUILayout>'
            )
            with zipfile.ZipFile(pak_path, "w") as z:
                z.writestr("media/UI/test.layout", layout_content.encode("utf-8"))

            compile_layout_files(catalog, pak_path, out_dir, verbose=False)

            result_file = os.path.join(out_dir, "test.layout")
            assert os.path.exists(result_file)
            with open(result_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Must contain properly escaped translation and be valid XML
            assert "Machado de Arundel &amp; Gl&oacute;ria" not in content  # Not html entities
            assert "Machado de Arundel &amp; Glória" in content
            root = ET.fromstring(content)
            prop = root.find(".//Property[@Name='Text']")
            assert prop is not None
            assert prop.attrib["Value"] == "Machado de Arundel & Glória"


# ==============================================================================
# Challenge 3: Duplicate Key Detection in DAT and Catalog
# ==============================================================================

class TestChallenge3DuplicateKeyDetection:
    """Empirical verification of duplicate original key detection in DAT and catalog."""

    def test_verifier_catches_duplicate_original_in_dat(self):
        raw_dat = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Potion of Life\r\n"
            "<STRING>TRANSLATION:Poção de Vida\r\n"
            "[/TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Mana Potion\r\n"
            "<STRING>TRANSLATION:Poção de Mana\r\n"
            "[/TRANSLATION]\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Potion of Life\r\n"
            "<STRING>TRANSLATION:Poção da Vida Alternativa\r\n"
            "[/TRANSLATION]\r\n"
        )
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe" + raw_dat.encode("utf-16le"))
            tmp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=tmp_path, verbose=False)
            res = verifier.run_all()
            assert res is False, "Verifier must reject duplicate original string in DAT"
            assert any("Duplicate ORIGINAL text 'Potion of Life'" in err for err in verifier.errors)
        finally:
            os.remove(tmp_path)

    def test_verifier_catches_duplicate_original_across_catalog_categories(self):
        catalog = {
            "categories": {
                "UI": [
                    {"id": "UI_0001", "original": "Attack", "translation": "Atacar"}
                ],
                "Skills": [
                    {"id": "Skills_0001", "original": "Attack", "translation": "Ataque"}
                ]
            }
        }
        dat_content = (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Attack\r\n"
            "<STRING>TRANSLATION:Atacar\r\n"
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
            assert res is False, "Verifier must detect duplicate original string across catalog categories"
            assert any("Catalog duplicate key" in err for err in verifier.errors)

    def test_compiler_deduplicates_duplicate_catalog_originals_safely(self):
        catalog = {
            "categories": {
                "Items": [
                    {"id": "Items_0001", "original": "Dagger", "translation": "Adaga"}
                ],
                "Recipes": [
                    {"id": "Recipes_0001", "original": "Dagger", "translation": "Punhal"}
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dat = os.path.join(tmp_dir, "translation.dat")
            blocks = generate_translation_dat(catalog, out_dat, verbose=False)
            # Must write only 1 block to DAT, skipping the duplicate
            assert blocks == 1
            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            assert verifier.verify_dat_file() is True


# ==============================================================================
# Challenge 4: Multiline Text Newline Escaping & Severed Fragments
# ==============================================================================

class TestChallenge4MultilineHandling:
    """Empirical verification of multiline string newline escaping and fragment rejection."""

    @pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"])
    def test_compiler_escapes_all_newline_types(self, line_ending):
        catalog = {
            "categories": {
                "Quests": [
                    {
                        "original": f"Line 1{line_ending}Line 2{line_ending}Line 3",
                        "translation": f"Linha 1{line_ending}Linha 2{line_ending}Linha 3"
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dat = os.path.join(tmp_dir, "translation.dat")
            count = generate_translation_dat(catalog, out_dat, verbose=False)
            assert count == 1

            with open(out_dat, "rb") as f:
                data = f.read()
            text = data[2:].decode("utf-16le")

            assert "<STRING>ORIGINAL:Line 1\\nLine 2\\nLine 3\r\n" in text
            assert "<STRING>TRANSLATION:Linha 1\\nLinha 2\\nLinha 3\r\n" in text

            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            assert verifier.run_all() is True

    @pytest.mark.parametrize("severed_position", [
        # Inside block between ORIGINAL and TRANSLATION
        (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Quest\r\n"
            "Orphaned Mid Fragment\r\n"
            "<STRING>TRANSLATION:Missão\r\n"
            "[/TRANSLATION]\r\n"
        ),
        # Inside block after TRANSLATION
        (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Quest\r\n"
            "<STRING>TRANSLATION:Missão Linha 1\r\n"
            "Missão Linha 2 Quebrada\r\n"
            "[/TRANSLATION]\r\n"
        ),
        # Outside block before [TRANSLATION]
        (
            "Stray Line Fragment\r\n"
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Quest\r\n"
            "<STRING>TRANSLATION:Missão\r\n"
            "[/TRANSLATION]\r\n"
        ),
        # Outside block after [/TRANSLATION]
        (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Quest\r\n"
            "<STRING>TRANSLATION:Missão\r\n"
            "[/TRANSLATION]\r\n"
            "Stray Line Fragment After\r\n"
        )
    ])
    def test_verifier_fatally_rejects_severed_fragments_anywhere(self, severed_position):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe" + severed_position.encode("utf-16le"))
            tmp_path = f.name
        try:
            verifier = TranslationVerifier(dat_path=tmp_path, verbose=False)
            res = verifier.run_all()
            assert res is False, "Verifier must fatally reject severed fragments"
            assert any("Unrecognized token or unescaped multiline fragment" in err for err in verifier.errors)
        finally:
            os.remove(tmp_path)


# ==============================================================================
# Challenge 5: Formatting Tag & Specifier Validation
# ==============================================================================

class TestChallenge5FormattingTagsAndSpecifiers:
    """Empirical verification of formatting tag, specifier, and token validation."""

    def test_valid_formatting_passes_cleanly(self):
        orig = "|cFFFFBA00Level %d %s|u [ITEM]: deals 25% of DPS."
        trans = "|cFFFFBA00Nível %d %s|u [ITEM]: causa 25% de DPS."
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert errors == []

    @pytest.mark.parametrize("bad_trans,expected_err", [
        # Dangling pipe
        ("|cFFFFBA00Gold|", "Dangling pipe"),
        # Short hex
        ("|cFFF00Ouro|u", "Malformed hex color tag"),
        # Invalid hex characters
        ("|cFFFFZZZZOuro|u", "Malformed hex color tag"),
        # Invalid pipe sequence
        ("|xOuro|u", "Invalid pipe escape sequence"),
        # Unclosed color tag
        ("|cFFFFBA00Ouro", "Unclosed color tag"),
        # Unmatched |u without open
        ("Ouro|u", "Unmatched closing tag"),
        # Color mismatch with original
        ("|cFF000000Ouro|u", "Color tag mismatch"),
        # Swapped printf specifiers
        # If orig has %d %s and trans has %s %d
    ])
    def test_corrupted_color_tags_rejected(self, bad_trans, expected_err):
        orig = "|cFFFFBA00Ouro|u"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, bad_trans)
        assert len(errors) > 0
        assert any(expected_err in err for err in errors)

    def test_swapped_printf_specifiers_rejected(self):
        orig = "Rank %d in %s requires %f mana"
        trans = "Rank %s em %d requer %f de mana"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Format specifier mismatch" in err for err in errors)

    def test_missing_printf_specifiers_rejected(self):
        orig = "Value: %d / %d"
        trans = "Valor: %d"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Format specifier mismatch" in err for err in errors)

    def test_prose_percentages_never_falsely_flagged(self):
        orig = "Increases attack speed by 15%, movement by 20%, and armor by 5%."
        trans = "Aumenta velocidade de ataque em 15%, movimento em 20% e armadura em 5%."
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert errors == []

    def test_engine_bracket_tokens_must_match(self):
        orig = "Use [HERO_NAME] to defeat [BOSS_ID] and obtain [REWARD]!"
        trans = "Use [HERO_NAME] para derrotar [BOSS_ID] e obter [RECOMPENSA]!"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Engine bracket token mismatch" in err for err in errors)

    def test_brace_placeholders_must_match(self):
        orig = "Slot {0}: {1} points"
        trans = "Espaço {0}: pontos"
        errors = TranslationVerifier.validate_formatting_and_tags(orig, trans)
        assert len(errors) > 0
        assert any("Brace placeholder mismatch" in err for err in errors)
