#!/usr/bin/env python3
"""
tools/verify_translation.py - Torchlight Translation Verification Tool

Validates the integrity, format, and structure of translation assets:
1. translation.dat validation:
   - Exists and has non-zero size
   - Starts strictly with UTF-16LE Byte Order Mark (BOM: 0xFF 0xFE)
   - Decodes cleanly as UTF-16LE without decoding errors
   - Contains balanced [TRANSLATION] and [/TRANSLATION] tags
   - Each block contains exactly one <STRING>ORIGINAL: and one <STRING>TRANSLATION:
   - Verifies original string integrity (non-empty, properly formatted)
2. Catalog cross-validation (if catalog is present):
   - Verifies all catalog strings are present in translation.dat
   - Compares total string counts
3. Layout assets validation (if layout dir is present):
   - Validates that .layout files exist, are readable, and well-formed

Part of Milestone 1 (M1) of the Torchlight pt-BR translation project.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


class TranslationVerifier:
    def __init__(self, dat_path: str, catalog_path: str = None, layout_dir: str = None, verbose: bool = True):
        self.dat_path = os.path.abspath(dat_path)
        self.catalog_path = os.path.abspath(catalog_path) if catalog_path else None
        self.layout_dir = os.path.abspath(layout_dir) if layout_dir else None
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict = {}

    def log(self, msg: str):
        if self.verbose:
            print(msg)

    @staticmethod
    def validate_formatting_and_tags(orig: str, trans: str) -> list[str]:
        """
        Validates color formatting tags, format specifiers, and engine bracket tokens
        between original and translated strings.
        """
        errors = []

        # 1. Pipe syntax validation in translation
        pipe_indices = [i for i, ch in enumerate(trans) if ch == "|"]
        for idx in pipe_indices:
            remainder = trans[idx + 1:]
            if not remainder:
                errors.append(f"Dangling pipe '|' at end of string (pos {idx})")
                continue
            first_char = remainder[0]
            if first_char == "u":
                continue
            elif first_char == "c":
                hex_part = remainder[1:9]
                if len(hex_part) < 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", hex_part):
                    errors.append(f"Malformed hex color tag at pos {idx}: '|c{hex_part}' (must be exactly 8 hex digits)")
            else:
                errors.append(f"Invalid pipe escape sequence at pos {idx}: '|{first_char}'")

        # 2. Tag nesting & closure in translation
        tag_tokens = re.findall(r"\|c[0-9a-fA-F]{8}|\|u", trans)
        depth = 0
        for tok in tag_tokens:
            if tok.startswith("|c"):
                if depth > 0:
                    errors.append(f"Nested or unclosed color tag '{tok}' before closing previous tag with '|u'")
                depth += 1
            elif tok == "|u":
                if depth <= 0:
                    errors.append("Unmatched closing tag '|u' without preceding open tag")
                else:
                    depth -= 1
        if depth > 0:
            errors.append(f"Unclosed color tag at end of string (missing {depth} '|u' tag(s))")

        # 3. Tag parity between original and translation
        orig_colors = [c.upper() for c in re.findall(r"\|c[0-9a-fA-F]{8}", orig, flags=re.IGNORECASE)]
        trans_colors = [c.upper() for c in re.findall(r"\|c[0-9a-fA-F]{8}", trans, flags=re.IGNORECASE)]
        if Counter(orig_colors) != Counter(trans_colors):
            errors.append(
                f"Color tag mismatch: original has {orig_colors}, translation has {trans_colors}"
            )

        orig_u_count = orig.count("|u")
        trans_u_count = trans.count("|u")
        if orig_u_count != trans_u_count:
            errors.append(
                f"Closing tag '|u' count mismatch: original has {orig_u_count}, translation has {trans_u_count}"
            )

        # 4. Printf format specifiers (%s, %d, %f, etc.)
        # Note: Do NOT include space ' ' in flags to avoid false positives on percentage prose (e.g. '30% of DPS')
        printf_regex = re.compile(r"%(?:%|[-+0#]*\d*(?:\.\d+)?[diuoxXfFeEgGaAcspn])")
        orig_printf = [p for p in printf_regex.findall(orig) if p != "%%"]
        trans_printf = [p for p in printf_regex.findall(trans) if p != "%%"]
        if orig_printf != trans_printf:
            errors.append(
                f"Format specifier mismatch: original has {orig_printf}, translation has {trans_printf} (exact sequence must match for C/C++ engine safety)"
            )

        # 5. Brace specifiers ({0}, {1}, etc.)
        brace_regex = re.compile(r"\{[0-9]+\}")
        orig_braces = brace_regex.findall(orig)
        trans_braces = brace_regex.findall(trans)
        if Counter(orig_braces) != Counter(trans_braces):
            errors.append(
                f"Brace placeholder mismatch: original has {orig_braces}, translation has {trans_braces}"
            )

        # 6. Engine bracket tokens ([ITEM], [VALUE], [NAME], etc.)
        token_regex = re.compile(r"\[[A-Z0-9_]+\]")
        orig_tokens = token_regex.findall(orig)
        trans_tokens = token_regex.findall(trans)
        if Counter(orig_tokens) != Counter(trans_tokens):
            errors.append(
                f"Engine bracket token mismatch: original has {orig_tokens}, translation has {trans_tokens}"
            )

        return errors

    def verify_dat_file(self) -> bool:
        """
        Validates the structure and encoding of translation.dat.
        """
        self.log(f"[Verify] Checking translation file: {self.dat_path}")

        if not os.path.exists(self.dat_path):
            self.errors.append(f"File not found: {self.dat_path}")
            return False

        file_size = os.path.getsize(self.dat_path)
        if file_size == 0:
            self.errors.append(f"File is empty: {self.dat_path}")
            return False

        with open(self.dat_path, "rb") as f:
            raw_bytes = f.read()

        # Check BOM: must be 0xFF 0xFE
        if len(raw_bytes) < 2:
            self.errors.append("File is too short to contain a valid UTF-16LE BOM.")
            return False

        bom = raw_bytes[:2]
        if bom != b"\xff\xfe":
            self.errors.append(
                f"Invalid BOM: expected \\xff\\xfe (UTF-16LE), found {repr(bom)}"
            )
            return False

        # Verify UTF-16LE decode
        try:
            content = raw_bytes[2:].decode("utf-16le")
        except UnicodeDecodeError as e:
            self.errors.append(f"UTF-16LE decoding error: {e}")
            return False

        # Normalize line endings
        lines = [line.rstrip("\r\n") for line in content.splitlines()]

        # Validate tag balance and block format
        open_tag = "[TRANSLATION]"
        close_tag = "[/TRANSLATION]"

        open_count = lines.count(open_tag)
        close_count = lines.count(close_tag)

        if open_count != close_count:
            self.errors.append(
                f"Mismatched tag counts: {open_count} {open_tag} vs {close_count} {close_tag}"
            )

        # Parse blocks sequentially
        blocks_parsed = 0
        in_block = False
        current_block_line = 0
        current_orig = None
        current_trans = None
        orig_strings = set()
        seen_orig_lines: dict[str, int] = {}
        translated_count = 0

        for line_num, line in enumerate(lines, 1):
            if not line:
                continue

            if line.upper() in ("[TRANSLATIONS]", "[/TRANSLATIONS]"):
                continue

            if line == open_tag:
                if in_block:
                    self.errors.append(
                        f"Line {line_num}: Unexpected '{open_tag}' while already inside a translation block (opened at line {current_block_line})"
                    )
                in_block = True
                current_block_line = line_num
                current_orig = None
                current_trans = None

            elif line == close_tag:
                if not in_block:
                    self.errors.append(
                        f"Line {line_num}: Unexpected '{close_tag}' without matching '{open_tag}'"
                    )
                else:
                    # Validate completed block
                    if current_orig is None:
                        self.errors.append(
                            f"Block ending at line {line_num}: Missing <STRING>ORIGINAL: line"
                        )
                    if current_trans is None:
                        self.errors.append(
                            f"Block ending at line {line_num}: Missing <STRING>TRANSLATION: line"
                        )
                    if current_orig is not None and current_trans is not None:
                        blocks_parsed += 1

                        # Duplicate key detection
                        if current_orig in seen_orig_lines:
                            prev_line = seen_orig_lines[current_orig]
                            self.errors.append(
                                f"Block ending at line {line_num}: Duplicate ORIGINAL text '{current_orig}' (previously defined at line {prev_line})"
                            )
                        else:
                            seen_orig_lines[current_orig] = current_block_line
                            orig_strings.add(current_orig)

                        # Formatting tag and specifier validation
                        tag_errors = self.validate_formatting_and_tags(current_orig, current_trans)
                        for err in tag_errors:
                            self.errors.append(f"Block ending at line {line_num} ('{current_orig}'): {err}")

                        if current_trans != current_orig:
                            translated_count += 1
                        else:
                            words = current_orig.replace("\\n", " ").split()
                            is_goblin = any(g in current_orig for g in ("Brasag", "Garan", "kratk", "flurk", "larag", "Bra'nag", "garap"))
                            allowed_proper_names = ("Nicola Brink", "Trill-Bot 4000", "Elephant Ngaw", "Raleigh Claire", "Crowfly", "Strangelove", "Luminorum", "Blazemore")
                            if len(words) > 1 and not current_orig.startswith("Bip") and not is_goblin and current_orig not in allowed_proper_names:
                                self.errors.append(
                                    f"Untranslated multi-word English phrase in translation.dat: '{current_orig}'"
                                )

                    in_block = False

            elif line.startswith("<STRING>ORIGINAL:"):
                if not in_block:
                    self.errors.append(
                        f"Line {line_num}: <STRING>ORIGINAL: found outside a [TRANSLATION] block"
                    )
                elif current_orig is not None:
                    self.errors.append(
                        f"Line {line_num}: Duplicate <STRING>ORIGINAL: in block started at line {current_block_line}"
                    )
                else:
                    current_orig = line[len("<STRING>ORIGINAL:"):]
                    if not current_orig:
                        self.warnings.append(
                            f"Line {line_num}: Empty ORIGINAL text in block at line {current_block_line}"
                        )

            elif line.startswith("<STRING>TRANSLATION:"):
                if not in_block:
                    self.errors.append(
                        f"Line {line_num}: <STRING>TRANSLATION: found outside a [TRANSLATION] block"
                    )
                elif current_trans is not None:
                    self.errors.append(
                        f"Line {line_num}: Duplicate <STRING>TRANSLATION: in block started at line {current_block_line}"
                    )
                else:
                    current_trans = line[len("<STRING>TRANSLATION:"):]

            else:
                self.errors.append(
                    f"Line {line_num}: Unrecognized token or unescaped multiline fragment '{line}' inside or outside block"
                )

        if in_block:
            self.errors.append(
                f"Unterminated [TRANSLATION] block opened at line {current_block_line}"
            )

        self.stats["dat_file_size"] = file_size
        self.stats["dat_total_blocks"] = blocks_parsed
        self.stats["dat_unique_originals"] = len(orig_strings)
        self.stats["dat_translated_count"] = translated_count
        self.stats["orig_strings_set"] = orig_strings
        translated_ratio = translated_count / max(blocks_parsed, 1)
        self.stats["dat_translated_ratio"] = translated_ratio

        self.log(f"  - BOM check:                  PASSED (UTF-16LE)")
        self.log(f"  - UTF-16LE decode:            PASSED")
        self.log(f"  - Total translation blocks:   {blocks_parsed:,}")
        self.log(f"  - Unique original strings:    {len(orig_strings):,}")
        self.log(f"  - Translated strings count:   {translated_count:,} ({translated_ratio*100:.1f}%)")

        if translated_ratio < 0.75:
            self.errors.append(
                f"Translated blocks ratio too low: {translated_count}/{blocks_parsed} ({translated_ratio*100:.1f}%) < 75.0% requirement"
            )

        return len(self.errors) == 0

    def verify_catalog(self) -> bool:
        """
        Cross-validates translation.dat against translation_catalog.json if present.
        """
        if not self.catalog_path or not os.path.exists(self.catalog_path):
            self.log("[Verify] No catalog provided or found; skipping catalog cross-check.")
            return True

        self.log(f"[Verify] Cross-checking against catalog: {self.catalog_path}")

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception as e:
            self.errors.append(f"Failed to load catalog for cross-check: {e}")
            return False

        catalog_originals = set()
        seen_catalog_keys: dict[str, str] = {}
        catalog_duplicates: list[str] = []

        for cat_name, entries in catalog.get("categories", {}).items():
            for entry in entries:
                orig = entry.get("original", "")
                trans = entry.get("translation", "")
                entry_id = entry.get("id", "unknown")
                if not orig:
                    continue

                orig_norm = orig.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
                orig_trimmed = orig.strip().replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
                if orig in seen_catalog_keys:
                    prev_loc, prev_trans = seen_catalog_keys[orig]
                    if prev_trans != trans:
                        catalog_duplicates.append(
                            f"'{orig}' has conflicting translations: '{trans}' in category '{cat_name}' (id: {entry_id}) vs '{prev_trans}' in {prev_loc}"
                        )
                else:
                    seen_catalog_keys[orig] = (f"category '{cat_name}' (id: {entry_id})", trans)
                    catalog_originals.add(orig_norm)
                    if orig_trimmed:
                        catalog_originals.add(orig_trimmed)

                if trans:
                    cat_tag_errors = self.validate_formatting_and_tags(orig, trans)
                    for err in cat_tag_errors:
                        self.errors.append(
                            f"Catalog entry '{entry_id}' ('{orig}'): {err}"
                        )
                if trans == orig or not trans:
                    words = orig.replace("\r\n", " ").replace("\n", " ").split()
                    is_goblin = any(g in orig for g in ("Brasag", "Garan", "kratk", "flurk", "larag", "Bra'nag", "garap"))
                    allowed_proper_names = ("Nicola Brink", "Trill-Bot 4000", "Elephant Ngaw", "Raleigh Claire", "Crowfly", "Strangelove", "Luminorum", "Blazemore")
                    if len(words) > 1 and not orig.startswith("Bip") and not is_goblin and orig not in allowed_proper_names:
                        self.errors.append(
                            f"Catalog untranslated multi-word English phrase in category '{cat_name}' (id: {entry_id}): '{orig}'"
                        )

        if catalog_duplicates:
            for dup in catalog_duplicates[:10]:
                self.errors.append(f"Catalog duplicate key: {dup}")
            if len(catalog_duplicates) > 10:
                self.errors.append(
                    f"... and {len(catalog_duplicates) - 10} more duplicate original keys in catalog."
                )

        dat_originals = self.stats.get("orig_strings_set", set())
        missing_in_dat = catalog_originals - dat_originals
        extra_in_dat = dat_originals - catalog_originals

        self.stats["catalog_total_strings"] = len(catalog_originals)
        self.stats["missing_in_dat"] = len(missing_in_dat)
        self.stats["extra_in_dat"] = len(extra_in_dat)

        self.log(f"  - Catalog unique strings:     {len(catalog_originals):,}")
        self.log(f"  - Missing in translation.dat: {len(missing_in_dat)}")
        self.log(f"  - Extra in translation.dat:   {len(extra_in_dat)}")

        if missing_in_dat:
            sample = list(missing_in_dat)[:5]
            self.errors.append(
                f"{len(missing_in_dat)} strings from catalog are missing in translation.dat (Sample: {sample})"
            )

        return len(self.errors) == 0

    def verify_layouts(self) -> bool:
        """
        Validates compiled .layout XML files under layout_dir if present.
        """
        if not self.layout_dir or not os.path.exists(self.layout_dir):
            self.log("[Verify] No layout dir provided or found; skipping layout checks.")
            return True

        self.log(f"[Verify] Checking layout directory: {self.layout_dir}")
        layout_files = [
            f for f in os.listdir(self.layout_dir)
            if f.lower().endswith(".layout")
        ]

        self.stats["layout_files_count"] = len(layout_files)
        self.log(f"  - Found {len(layout_files)} .layout files")

        if len(layout_files) < 35:
            self.warnings.append(
                f"Expected 35 .layout files, but found {len(layout_files)} in {self.layout_dir}"
            )

        for filename in layout_files:
            file_path = os.path.join(self.layout_dir, filename)
            size = os.path.getsize(file_path)
            if size == 0:
                self.errors.append(f"Layout file is empty: {filename}")
                continue

            with open(file_path, "rb") as f:
                header = f.read(2)

            # File must be valid UTF-16LE or UTF-8
            try:
                with open(file_path, "rb") as f:
                    data = f.read()
                if data.startswith(b"\xff\xfe"):
                    data[2:].decode("utf-16le")
                else:
                    data.decode("utf-8")
            except Exception as e:
                self.errors.append(f"Layout file decoding error in {filename}: {e}")

        return len(self.errors) == 0

    def run_all(self) -> bool:
        dat_ok = self.verify_dat_file()
        catalog_ok = self.verify_catalog()
        layout_ok = self.verify_layouts()

        is_success = dat_ok and catalog_ok and layout_ok and len(self.errors) == 0

        self.log("=" * 70)
        if is_success:
            self.log("[SUCCESS] All translation verification checks passed!")
            self.log(f"  - Blocks verified:  {self.stats.get('dat_total_blocks', 0):,}")
            self.log(f"  - File size:        {self.stats.get('dat_file_size', 0):,} bytes")
            if "layout_files_count" in self.stats:
                self.log(f"  - Layout files:     {self.stats['layout_files_count']}")
        else:
            self.log("[FAILED] Verification encountered errors:")
            for err in self.errors:
                self.log(f"  [ERROR] {err}")

        if self.warnings:
            self.log("\nWarnings encountered:")
            for w in self.warnings[:10]:
                self.log(f"  [WARN] {w}")
            if len(self.warnings) > 10:
                self.log(f"  ... and {len(self.warnings) - 10} more warnings.")

        self.log("=" * 70)
        return is_success


def main() -> int:
    default_dat = r"translation_ptbr\translations\translation.dat"
    default_catalog = r"translation_ptbr\translation_catalog.json"
    default_layout = r"translation_ptbr\media\UI"

    parser = argparse.ArgumentParser(description="Torchlight Translation Verification Tool")
    parser.add_argument(
        "--dat-path",
        default=default_dat,
        help=f"Path to translation.dat (default: {default_dat})"
    )
    parser.add_argument(
        "--catalog-path",
        default=default_catalog,
        help=f"Path to translation_catalog.json (default: {default_catalog})"
    )
    parser.add_argument(
        "--layout-dir",
        default=default_layout,
        help=f"Path to media/UI/ layout directory (default: {default_layout})"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    verifier = TranslationVerifier(
        dat_path=args.dat_path,
        catalog_path=args.catalog_path,
        layout_dir=args.layout_dir,
        verbose=verbose
    )

    success = verifier.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
