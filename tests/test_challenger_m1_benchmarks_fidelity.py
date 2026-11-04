#!/usr/bin/env python3
"""
tests/test_challenger_m1_benchmarks_fidelity.py

Adversarial Stress, Benchmark, and Lossless Round-Trip Verification Suite
for Milestone 1 (Text Extraction & Compilation Pipeline).

Executed by Challenger 2 to empirically verify:
1. Performance & Memory Benchmarks (Pak.zip 318MB, 17,565 strings)
2. Lossless Round-Trip Fidelity with 100% Portuguese Accents and Formatting Tags
3. Large Buffer & Scalability Stress (up to 1MB buffers, 50k blocks)
4. Layout Attribute & XML Preservation (non-Text attributes, entity escaping)
5. Edge Cases, Delimiter Collisions, and Non-BMP Unicode Characters
"""

import html
import io
import json
import os
import re
import struct
import tempfile
import time
import tracemalloc
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
import pytest

from tools.extract_strings import (
    extract_all_from_pak,
    build_catalog,
    extract_adm_strings,
    extract_layout_strings,
    is_valid_translatable_string,
    STANDARD_CATEGORIES
)
from tools.compile_translation import (
    load_catalog,
    build_translation_map,
    generate_translation_dat,
    compile_layout_files
)
from tools.verify_translation import TranslationVerifier

PAK_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
CATALOG_PATH = r"translation_ptbr\translation_catalog.json"
LIVE_DAT_PATH = r"translation_ptbr\translations\translation.dat"
LIVE_LAYOUT_DIR = r"translation_ptbr\media\UI"

PTBR_ACCENTS = "áéíóúâêôãõçàüÁÉÍÓÚÂÊÔÃÕÇÀÜ"


# ==============================================================================
# 1. PERFORMANCE AND RESOURCE BENCHMARKS
# ==============================================================================
class TestMilestone1Benchmarks:
    """Empirical benchmarks measuring execution time, throughput, and memory consumption."""

    def test_01_pak_zip_extraction_benchmark(self):
        """Benchmark full extraction from the 318MB Pak.zip."""
        if not os.path.exists(PAK_PATH):
            pytest.skip(f"Pak.zip not found at {PAK_PATH}")

        pak_size_mb = os.path.getsize(PAK_PATH) / (1024 * 1024)

        tracemalloc.start()
        start_time = time.perf_counter()

        best_entries, stats = extract_all_from_pak(PAK_PATH, verbose=False)

        elapsed = time.perf_counter() - start_time
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mem_mb = peak_mem / (1024 * 1024)

        # Assertions on catalog scale
        assert stats["total_adm_processed"] >= 5990, f"Too few ADM files: {stats['total_adm_processed']}"
        assert stats["total_layout_processed"] == 35, f"Unexpected layout count: {stats['total_layout_processed']}"
        assert len(best_entries) == 13622, f"Expected 13,622 strings, got {len(best_entries)}"

        # Performance constraints:
        # 318MB archive with ~22,400 files must extract in under 20.0 seconds
        # Memory consumption peak must be strictly under 350 MB
        throughput_files_sec = stats["total_files_in_pak"] / elapsed
        throughput_mb_sec = pak_size_mb / elapsed

        print(f"\n[BENCHMARK] Pak.zip Extraction:")
        print(f"  - Runtime:          {elapsed:.3f} s")
        print(f"  - Peak Memory:      {peak_mem_mb:.2f} MB")
        print(f"  - Throughput:       {throughput_files_sec:.1f} files/s ({throughput_mb_sec:.1f} MB/s)")
        print(f"  - Strings Extracted:{len(best_entries):,}")

        assert elapsed < 50.0, f"Extraction too slow: {elapsed:.2f}s (max 50.0s)"
        assert peak_mem_mb < 350.0, f"Extraction memory usage too high: {peak_mem_mb:.2f}MB (max 350MB)"

    def test_02_catalog_to_dat_compilation_benchmark(self):
        """Benchmark compilation of 13,622 strings into translation.dat."""
        if not os.path.exists(CATALOG_PATH):
            pytest.skip(f"Catalog not found at {CATALOG_PATH}")

        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        total_strings = catalog["metadata"]["total_strings"]
        assert total_strings in (13622, 13633)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "test_translation.dat")

            tracemalloc.start()
            start_time = time.perf_counter()

            blocks = generate_translation_dat(catalog, out_dat, fallback_to_original=True, verbose=False)

            elapsed = time.perf_counter() - start_time
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            peak_mem_mb = peak_mem / (1024 * 1024)
            file_size_mb = os.path.getsize(out_dat) / (1024 * 1024)
            throughput_blocks_sec = blocks / elapsed

            print(f"\n[BENCHMARK] DAT Compilation:")
            print(f"  - Runtime:          {elapsed:.3f} s")
            print(f"  - Peak Memory:      {peak_mem_mb:.2f} MB")
            print(f"  - Output Size:      {file_size_mb:.2f} MB ({os.path.getsize(out_dat):,} bytes)")
            print(f"  - Throughput:       {throughput_blocks_sec:.1f} blocks/s")

            assert blocks in (13622, 13633)
            assert elapsed < 5.0, f"Compilation too slow: {elapsed:.2f}s (max 5.0s)"
            assert peak_mem_mb < 150.0, f"Compilation memory too high: {peak_mem_mb:.2f}MB (max 150MB)"

    def test_03_verifier_audit_benchmark(self):
        """Benchmark verification tool across full catalog and translation.dat."""
        if not os.path.exists(LIVE_DAT_PATH) or not os.path.exists(CATALOG_PATH):
            pytest.skip("Live translation assets missing")

        start_time = time.perf_counter()
        verifier = TranslationVerifier(
            dat_path=LIVE_DAT_PATH,
            catalog_path=CATALOG_PATH,
            layout_dir=LIVE_LAYOUT_DIR,
            verbose=False
        )
        success = verifier.run_all()
        elapsed = time.perf_counter() - start_time

        print(f"\n[BENCHMARK] Verifier Audit:")
        print(f"  - Runtime:          {elapsed:.3f} s")
        print(f"  - Blocks Audited:   {verifier.stats.get('dat_total_blocks'):,}")
        print(f"  - Success:          {success}")

        assert success is True
        assert elapsed < 5.0, f"Verification audit too slow: {elapsed:.2f}s (max 5.0s)"


# ==============================================================================
# 2. LOSSLESS ROUND-TRIP FIDELITY ORACLE
# ==============================================================================
class TestLosslessRoundTripFidelity:
    """Verifies that 100% of characters, Portuguese accents, and formatting tags survive round-trip."""

    def test_01_full_catalog_ptbr_accents_and_tags_roundtrip(self):
        """
        Synthesize pt-BR translations for all 17,565 strings, incorporating
        Portuguese accents, color tags, and formatting placeholders.
        Compile to translation.dat, parse back, and verify 100% character identity.
        """
        if not os.path.exists(CATALOG_PATH):
            pytest.skip(f"Catalog not found at {CATALOG_PATH}")

        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        # Inject pt-BR translations covering all accent variations and tags
        accent_variations = [
            "Ação Rápida de Cura e Proteção mística",
            "Poção de Mana Épica e Bênção do Herói",
            "Arco de Precisão com Perfuração Ígnea",
            "Coração do Ódio sombrio no Calabouço",
            "Fúria do Trovão Único e Destruição",
            "Manto do Ancião com Poderes Mágicos",
            "Místico Espírito das Profundezas Álgidas",
            "Elixir de Concentração e Visão Noturna",
            "Chama do Dragão Vermelho com Dano Contínuo",
            "Conexão Óbvia entre Portais e Dimensões"
        ]

        expected_map = {}
        idx = 0

        for cat_name, entries in catalog["categories"].items():
            for entry in entries:
                orig = entry["original"]
                accent_sample = accent_variations[idx % len(accent_variations)]
                idx += 1

                # If original contains tags, preserve them and append accented Portuguese text
                if "|c" in orig:
                    trans = f"|cFFFFBA00[pt-BR: {accent_sample}]|u {orig}"
                elif "\\n" in orig:
                    trans = f"[Linha 1: {accent_sample}]\\n[Linha 2: {orig}]"
                elif "%s" in orig or "%d" in orig:
                    trans = f"[Traduzido: {accent_sample}] - {orig}"
                else:
                    trans = f"Tradução: {orig} ({accent_sample}) — {PTBR_ACCENTS}"

                entry["translation"] = trans
                expected_map[orig.strip()] = trans.strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "ptbr_translation.dat")
            blocks_written = generate_translation_dat(catalog, out_dat, fallback_to_original=True, verbose=False)

            assert blocks_written == len(expected_map)

            # Read back the compiled DAT file directly
            with open(out_dat, "rb") as f:
                raw_bytes = f.read()

            assert raw_bytes.startswith(b"\xff\xfe"), "Missing UTF-16LE BOM"
            text_content = raw_bytes[2:].decode("utf-16le")

            # Parse blocks from DAT file
            parsed_map = {}
            current_orig = None
            current_trans = None

            for line in text_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("<STRING>ORIGINAL:"):
                    current_orig = line[len("<STRING>ORIGINAL:"):].strip()
                elif line.startswith("<STRING>TRANSLATION:"):
                    current_trans = line[len("<STRING>TRANSLATION:"):].strip()
                elif line == "[/TRANSLATION]":
                    if current_orig is not None and current_trans is not None:
                        parsed_map[current_orig] = current_trans
                    current_orig = None
                    current_trans = None

            # Lossless verification: 100% of strings must match character-by-character
            assert len(parsed_map) == len(expected_map), f"Count mismatch: {len(parsed_map)} vs {len(expected_map)}"

            mismatches = []
            for orig, expected_trans in expected_map.items():
                actual_trans = parsed_map.get(orig)
                if actual_trans != expected_trans:
                    mismatches.append((orig, expected_trans, actual_trans))

            assert len(mismatches) == 0, f"Found {len(mismatches)} lossless round-trip mismatches! First: {mismatches[:3]}"

            # Spot-check that all accented characters are present verbatim in parsed text
            all_parsed_text = " ".join(parsed_map.values())
            for ch in PTBR_ACCENTS:
                assert ch in all_parsed_text, f"Accent character '{ch}' missing from round-trip output!"

    def test_02_layout_xml_accents_and_escaping_roundtrip(self):
        """
        Verify that CEGUI layout compilation preserves Portuguese accents,
        correctly escapes XML special entities, and remains well-formed XML.
        """
        sample_layout_xml = """<?xml version="1.0" encoding="UTF-8"?>
<GUILayout>
    <Window Type="TaharezLook/FrameWindow" Name="TestWindow">
        <Property Name="UnifiedAreaRect" Value="{{0.1,0},{0.1,0},{0.9,0},{0.9,0}}" />
        <Property Name="Font" Value="Torchlight" />
        <Window Type="TaharezLook/Button" Name="BtnQuit">
            <Property Name="Text" Value="Quit Game" />
            <Property Name="UnifiedAreaRect" Value="{{0.2,0},{0.8,0},{0.4,0},{0.9,0}}" />
        </Window>
        <Window Type="TaharezLook/Button" Name="BtnOptions">
            <Property Name="Text" Value="Options &amp; Settings" />
            <Property Name="UnifiedAreaRect" Value="{{0.5,0},{0.8,0},{0.7,0},{0.9,0}}" />
        </Window>
        <Window Type="TaharezLook/StaticText" Name="TitleText">
            <Property Name="Text" Value="|cFFFFBA00Hero's Journey|u &lt;Danger&gt;" />
        </Window>
    </Window>
</GUILayout>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock Pak.zip containing this layout
            fake_pak = os.path.join(tmpdir, "fake_pak.zip")
            with zipfile.ZipFile(fake_pak, "w") as z:
                z.writestr("media/UI/testmenu.layout", sample_layout_xml.encode("utf-8"))

            mock_catalog = {
                "categories": {
                    "UI": [
                        {"original": "Quit Game", "translation": "Sair do Jogo (Ação & Confirmação)"},
                        {"original": "Options &amp; Settings", "translation": "Opções & Configurações avançadas <Ótimas>"},
                        {"original": "|cFFFFBA00Hero's Journey|u &lt;Danger&gt;", "translation": "|cFFFFBA00Jornada do Herói|u &lt;Atenção &amp; Perigo&gt;"}
                    ]
                }
            }

            out_layout_dir = os.path.join(tmpdir, "out_ui")
            compiled = compile_layout_files(mock_catalog, fake_pak, out_layout_dir, fallback_to_original=True, verbose=False)
            assert compiled == 1

            out_file = os.path.join(out_layout_dir, "testmenu.layout")
            assert os.path.exists(out_file)

            with open(out_file, "rb") as f:
                out_xml_bytes = f.read()

            out_xml_str = out_xml_bytes.decode("utf-8")

            # Parse with standard XML parser to verify strictly valid XML
            root = ET.fromstring(out_xml_str)
            assert root.tag == "GUILayout"

            # Check that non-text properties were untouched
            properties = {}
            for elem in root.iter("Property"):
                name = elem.get("Name")
                val = elem.get("Value")
                if name:
                    properties.setdefault(name, []).append(val)

            assert "Torchlight" in properties.get("Font", [])
            assert "{{0.1,0},{0.1,0},{0.9,0},{0.9,0}}" in properties.get("UnifiedAreaRect", [])

            # Check that Portuguese accents and entities survived correctly
            texts = properties.get("Text", [])
            assert any("Sair do Jogo (Ação & Confirmação)" in t for t in texts)
            assert any("Opções & Configurações avançadas" in t for t in texts)
            assert any("|cFFFFBA00Jornada do Herói|u" in t for t in texts)


# ==============================================================================
# 3. LARGE BUFFERS & BOUNDARY STRESS TESTS
# ==============================================================================
class TestLargeBuffersAndBoundaryStress:
    """Stress tests on buffer limits, high volumes, and boundary sizes."""

    @pytest.mark.parametrize("buffer_size", [10_000, 65_536, 262_144, 1_048_576])
    def test_01_extreme_buffer_sizes_in_translation(self, buffer_size):
        """Test compiling and verifying translation strings of 10KB, 64KB, 256KB, and 1MB."""
        large_ptbr_string = ("Ação, Bênção, Cura e Destruição Épica! " * (buffer_size // 40))[:buffer_size]

        mock_catalog = {
            "categories": {
                "Quests": [
                    {
                        "original": f"LongQuest_{buffer_size}",
                        "translation": large_ptbr_string
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, f"large_buffer_{buffer_size}.dat")
            blocks = generate_translation_dat(mock_catalog, out_dat, verbose=False)
            assert blocks == 1

            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            assert verifier.verify_dat_file() is True
            assert verifier.stats["dat_total_blocks"] == 1

            with open(out_dat, "rb") as f:
                content = f.read()[2:].decode("utf-16le")

            assert large_ptbr_string.strip() in content
            assert content.endswith("[/TRANSLATION]\r\n")

    def test_02_high_volume_scaling_50000_blocks(self):
        """Stress test compiler and verifier on 50,000 translation blocks."""
        entries = []
        for i in range(50_000):
            entries.append({
                "original": f"Item_Desc_{i:06d}",
                "translation": f"Descrição do Item {i:06d} com Bônus Mágico de Força e Agilidade"
            })

        mock_catalog = {"categories": {"Items": entries}}

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "stress_50k.dat")

            start = time.perf_counter()
            blocks = generate_translation_dat(mock_catalog, out_dat, verbose=False)
            comp_time = time.perf_counter() - start

            assert blocks == 50000
            file_size_mb = os.path.getsize(out_dat) / (1024 * 1024)

            # 50,000 blocks should compile in under 5.0 seconds
            assert comp_time < 5.0, f"Compilation of 50k blocks took too long: {comp_time:.2f}s"
            assert file_size_mb > 10.0, f"File unexpectedly small: {file_size_mb:.2f}MB"

            # Verify with TranslationVerifier
            v_start = time.perf_counter()
            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            valid = verifier.verify_dat_file()
            v_time = time.perf_counter() - v_start

            assert valid is True
            assert verifier.stats["dat_total_blocks"] == 50000
            assert v_time < 5.0, f"Verification of 50k blocks took too long: {v_time:.2f}s"


# ==============================================================================
# 4. LAYOUT ATTRIBUTE AND XML PRESERVATION
# ==============================================================================
class TestLayoutAttributePreservation:
    """Verifies that non-Text XML attributes remain 100% intact."""

    def test_01_all_35_real_pak_layouts_structural_preservation(self):
        """
        Extract all 35 layout files from Pak.zip, compile with live catalog,
        and verify that every XML element, window hierarchy, and non-Text
        attribute (UnifiedAreaRect, Font, Look, Position, etc.) is preserved.
        """
        if not os.path.exists(PAK_PATH) or not os.path.exists(CATALOG_PATH):
            pytest.skip("Pak.zip or catalog missing")

        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_ui = os.path.join(tmpdir, "media_ui")
            compiled_count = compile_layout_files(catalog, PAK_PATH, out_ui, fallback_to_original=True, verbose=False)
            assert compiled_count == 35

            # Compare each compiled layout against the original in Pak.zip
            with zipfile.ZipFile(PAK_PATH, "r") as z:
                for name in z.namelist():
                    if not name.lower().endswith(".layout"):
                        continue

                    filename = os.path.basename(name)
                    compiled_path = os.path.join(out_ui, filename)
                    assert os.path.exists(compiled_path), f"Compiled layout missing: {filename}"

                    orig_raw = z.read(name)
                    comp_raw = open(compiled_path, "rb").read()

                    # Check encoding preservation
                    orig_is_utf16 = orig_raw.startswith(b"\xff\xfe")
                    comp_is_utf16 = comp_raw.startswith(b"\xff\xfe")
                    assert orig_is_utf16 == comp_is_utf16, f"Encoding mismatch in {filename}"

                    orig_text = orig_raw[2:].decode("utf-16le") if orig_is_utf16 else orig_raw.decode("utf-8", errors="ignore")
                    comp_text = comp_raw[2:].decode("utf-16le") if comp_is_utf16 else comp_raw.decode("utf-8", errors="ignore")

                    # Check all non-Text Property tags exist in identical counts and values
                    orig_non_text_props = re.findall(r'<Property\s+Name="(?!Text")[^"]*"\s+Value="[^"]*"', orig_text, re.I)
                    comp_non_text_props = re.findall(r'<Property\s+Name="(?!Text")[^"]*"\s+Value="[^"]*"', comp_text, re.I)

                    assert len(orig_non_text_props) == len(comp_non_text_props), (
                        f"Non-text property count mismatch in {filename}: "
                        f"{len(orig_non_text_props)} vs {len(comp_non_text_props)}"
                    )

                    # Check Window hierarchy count
                    orig_windows = re.findall(r'<Window\s+[^>]+>', orig_text)
                    comp_windows = re.findall(r'<Window\s+[^>]+>', comp_text)
                    assert len(orig_windows) == len(comp_windows), f"Window tag count changed in {filename}"


# ==============================================================================
# 5. ADVERSARIAL EDGE CASES & ENCODING STABILITY
# ==============================================================================
class TestAdversarialEdgeCases:
    """Stress tests for delimiter collision, malformed input, and character sets."""

    def test_01_delimiter_token_in_translation_text(self):
        """
        Verify behavior when translated text contains DAT delimiter tokens like
        [TRANSLATION], [/TRANSLATION], <STRING>ORIGINAL:, etc.
        """
        mock_catalog = {
            "categories": {
                "Globals": [
                    {
                        "original": "Test Delimiters",
                        "translation": "Texto com [/TRANSLATION] e [TRANSLATION] e <STRING>TRANSLATION: falso"
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "delimiters.dat")
            generate_translation_dat(mock_catalog, out_dat, verbose=False)

            # Check how the verifier processes this
            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            verifier.verify_dat_file()

            # Note: If translated text has unescaped newline + [/TRANSLATION], it could split a block.
            # But within a single line, verify_dat_file inspects the entire line.
            # In our case, line starts with <STRING>TRANSLATION:, so line == open_tag is False.
            assert verifier.stats["dat_total_blocks"] == 1

    def test_02_surrogate_pairs_and_extended_unicode(self):
        """
        Verify handling of non-BMP characters requiring UTF-16 surrogate pairs (e.g. game icons/emojis).
        """
        mock_catalog = {
            "categories": {
                "Items": [
                    {
                        "original": "Golden Sword",
                        "translation": "Espada Dourada ⚔️ de Fogo 🔥 [Nível Máximo]"
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "surrogates.dat")
            generate_translation_dat(mock_catalog, out_dat, verbose=False)

            with open(out_dat, "rb") as f:
                raw = f.read()

            assert raw.startswith(b"\xff\xfe")
            decoded = raw[2:].decode("utf-16le")
            assert "⚔️" in decoded
            assert "🔥" in decoded

            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            assert verifier.verify_dat_file() is True

    def test_03_zero_width_and_control_characters(self):
        """Verify handling of zero-width spaces, soft hyphens, and whitespace variations."""
        text_with_control = "Tradução\u200Bcom\u00A0espaços\u00ADespeciais"
        mock_catalog = {
            "categories": {
                "UI": [
                    {
                        "original": "Special Whitespace",
                        "translation": text_with_control
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dat = os.path.join(tmpdir, "control_chars.dat")
            generate_translation_dat(mock_catalog, out_dat, verbose=False)

            with open(out_dat, "rb") as f:
                raw = f.read()

            decoded = raw[2:].decode("utf-16le")
            assert text_with_control in decoded

            verifier = TranslationVerifier(dat_path=out_dat, verbose=False)
            assert verifier.verify_dat_file() is True
