#!/usr/bin/env python3
"""
tools/compile_translation.py - Torchlight Translation Compilation Tool

Compiles the translation catalog (translation_catalog.json) into the official game assets:
1. Generates translations/translation.dat encoded strictly in UTF-16LE with BOM (0xFF 0xFE),
   using native Runic Games DAT format:
   [TRANSLATION]
   <STRING>ORIGINAL:<original_english>
   <STRING>TRANSLATION:<portuguese_translation>
   [/TRANSLATION]
2. Generates localized .layout XML files under media/UI/ by extracting base templates
   from Pak.zip and substituting translated text in Property Name="Text" tags,
   preserving each layout's native encoding (UTF-16LE or UTF-8).

Part of Milestone 1 (M1) of the Torchlight pt-BR translation project.
"""

import argparse
import html
import json
import os
import re
import sys
import zipfile
from pathlib import Path


def load_catalog(catalog_path: str) -> dict:
    """
    Loads and validates the translation catalog JSON file.
    """
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Translation catalog not found at: {catalog_path}")

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    if "categories" not in catalog:
        raise ValueError(f"Invalid catalog schema: missing 'categories' key in {catalog_path}")

    return catalog


def escape_xml_attr(val: str) -> str:
    """
    Idempotent XML attribute escaping using standard XML 1.0 predefined entities.
    Unescapes first to eliminate any pre-existing entities, preventing double-escaping.
    """
    norm = html.unescape(val)
    return (
        norm.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


def build_translation_map(catalog: dict, fallback_to_original: bool = True) -> dict[str, str]:
    """
    Constructs a dictionary mapping original_english_string -> translated_string.
    If fallback_to_original is True, untranslated entries (empty string) will use original.
    Supports dual-key matching (both literal unescaped and escaped forms) for layout properties.
    """
    mapping: dict[str, str] = {}
    for cat_name, entries in catalog["categories"].items():
        for entry in entries:
            orig = entry.get("original", "")
            if not orig:
                continue
            trans = entry.get("translation", "")
            if not trans and fallback_to_original:
                trans = orig
            mapping[orig] = trans
            mapping[orig.strip()] = trans.strip()
            # Map unescaped alias for XML entity resilience
            unesc = html.unescape(orig)
            if unesc != orig:
                mapping[unesc] = trans
                mapping[unesc.strip()] = trans.strip()
            # Map newline variants (\r\n vs \n vs literal \n)
            norm_n = orig.replace("\r\n", "\n")
            mapping[norm_n] = trans
            mapping[norm_n.strip()] = trans.strip()
            norm_slash_n = orig.replace("\r\n", "\\n").replace("\n", "\\n")
            mapping[norm_slash_n] = trans
            mapping[norm_slash_n.strip()] = trans.strip()
    return mapping


def generate_translation_dat(
    catalog: dict,
    output_dat_path: str,
    fallback_to_original: bool = True,
    verbose: bool = True
) -> int:
    """
    Compiles translation blocks into translations/translation.dat.
    File format requirements:
    - Encoded strictly in UTF-16LE with BOM (b'\\xff\\xfe').
    - Block structure:
      [TRANSLATION]
      <STRING>ORIGINAL:<original>
      <STRING>TRANSLATION:<translated>
      [/TRANSLATION]
    - Windows CRLF line endings (\\r\\n).
    Returns total number of translation blocks written.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_dat_path)), exist_ok=True)

    blocks: list[str] = []
    seen_originals: set[str] = set()
    total_entries = 0
    translated_entries = 0

    # Iterate categories deterministically
    for cat_name in sorted(catalog["categories"].keys()):
        entries = catalog["categories"][cat_name]
        for entry in entries:
            orig_raw = entry.get("original", "")
            if not orig_raw:
                continue

            # Multiline newline escaping: convert raw \r\n, \r, \n to literal \n
            orig = orig_raw.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")

            trans_raw = entry.get("translation", "")
            if trans_raw:
                translated_entries += 1
                trans = trans_raw.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
            elif fallback_to_original:
                trans = orig
            else:
                continue

            # Emit exact string with whitespace preserved
            if orig not in seen_originals:
                seen_originals.add(orig)
                block = (
                    "[TRANSLATION]\r\n"
                    f"<STRING>ORIGINAL:{orig}\r\n"
                    f"<STRING>TRANSLATION:{trans}\r\n"
                    "[/TRANSLATION]"
                )
                blocks.append(block)
                total_entries += 1

            # Also emit trimmed version if different, ensuring both padded and trimmed lookups resolve
            orig_trimmed = orig_raw.strip().replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
            trans_trimmed = trans_raw.strip().replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n") if trans_raw else orig_trimmed
            if orig_trimmed and orig_trimmed not in seen_originals:
                seen_originals.add(orig_trimmed)
                block = (
                    "[TRANSLATION]\r\n"
                    f"<STRING>ORIGINAL:{orig_trimmed}\r\n"
                    f"<STRING>TRANSLATION:{trans_trimmed}\r\n"
                    "[/TRANSLATION]"
                )
                blocks.append(block)
                total_entries += 1

    content_str = "[TRANSLATIONS]\r\n" + "\r\n".join(blocks) + "\r\n[/TRANSLATIONS]\r\n"
    # UTF-16LE with BOM: prepend b'\xff\xfe'
    encoded_bytes = b"\xff\xfe" + content_str.encode("utf-16le")

    with open(output_dat_path, "wb") as f:
        f.write(encoded_bytes)

    if verbose:
        print(f"[Compiler] Wrote {total_entries} blocks to {output_dat_path}")
        print(f"           - Non-empty translations: {translated_entries}")
        print(f"           - Fallback to original:   {total_entries - translated_entries}")
        print(f"           - Output file size:       {len(encoded_bytes):,} bytes")

    return total_entries


def compile_layout_files(
    catalog: dict,
    pak_path: str,
    output_layout_dir: str,
    fallback_to_original: bool = True,
    verbose: bool = True
) -> int:
    """
    Extracts base .layout XML files from Pak.zip, substitutes translated text
    for Property Name="Text", and writes localized copies into output_layout_dir.
    Preserves each layout's native encoding (UTF-16LE with BOM or UTF-8).
    Returns total number of layout files compiled.
    """
    if not os.path.exists(pak_path):
        raise FileNotFoundError(f"Pak.zip not found at: {pak_path}")

    os.makedirs(output_layout_dir, exist_ok=True)
    translation_map = build_translation_map(catalog, fallback_to_original=fallback_to_original)

    compiled_count = 0
    text_replacements_total = 0

    with zipfile.ZipFile(pak_path, "r") as z:
        for name in z.namelist():
            lower = name.lower().replace("\\", "/")
            if not lower.endswith(".layout"):
                continue

            filename = os.path.basename(name)
            raw_data = z.read(name)

            # Detect encoding
            is_utf16le = raw_data.startswith(b"\xff\xfe")
            if is_utf16le:
                xml_text = raw_data[2:].decode("utf-16le", errors="ignore")
            else:
                xml_text = raw_data.decode("utf-8", errors="ignore")

            # Replace Property Name="Text"|"Tooltip" Value="..." and multiline <Property Name="Text"|"Tooltip">...</Property>
            replacements_in_file = 0

            def replace_attr_property(match: re.Match) -> str:
                nonlocal replacements_in_file
                pname = match.group(1)
                orig_val = match.group(2)
                clean_val = orig_val.strip()
                unescaped_val = html.unescape(clean_val)

                new_val = None
                for cand in [clean_val, unescaped_val, clean_val.replace("\r\n", "\n"), clean_val.replace("\\n", "\n")]:
                    if cand in translation_map:
                        new_val = translation_map[cand]
                        break

                if new_val is not None:
                    if new_val != clean_val and new_val != unescaped_val:
                        replacements_in_file += 1
                        escaped_val = escape_xml_attr(new_val)
                        return f'<Property Name="{pname}" Value="{escaped_val}"'
                return match.group(0)

            def replace_tag_property(match: re.Match) -> str:
                nonlocal replacements_in_file
                pname = match.group(1)
                orig_val = match.group(2)
                clean_val = orig_val.strip()
                unescaped_val = html.unescape(clean_val)

                new_val = None
                for cand in [clean_val, unescaped_val, clean_val.replace("\r\n", "\n"), clean_val.replace("\\n", "\n")]:
                    if cand in translation_map:
                        new_val = translation_map[cand]
                        break

                if new_val is not None:
                    if new_val != clean_val and new_val != unescaped_val:
                        replacements_in_file += 1
                        escaped_val = escape_xml_attr(new_val)
                        return f'<Property Name="{pname}">{escaped_val}</Property>'
                return match.group(0)

            new_xml = re.sub(
                r'<Property\s+Name="(Text|Tooltip)"\s+Value="([^"]*)"',
                replace_attr_property,
                xml_text,
                flags=re.IGNORECASE
            )

            new_xml = re.sub(
                r'<Property\s+Name="(Text|Tooltip)"\s*>([^<]*)</Property\s*>',
                replace_tag_property,
                new_xml,
                flags=re.IGNORECASE
            )

            out_file_path = os.path.join(output_layout_dir, filename)
            if is_utf16le:
                out_bytes = b"\xff\xfe" + new_xml.encode("utf-16le")
            else:
                out_bytes = new_xml.encode("utf-8")

            with open(out_file_path, "wb") as f_out:
                f_out.write(out_bytes)

            compiled_count += 1
            text_replacements_total += replacements_in_file

    apply_layout_geometry_fixes(output_layout_dir)

    if verbose:
        print(f"[Compiler] Processed {compiled_count} .layout files into {output_layout_dir}")
        print(f"           - Total text properties substituted: {text_replacements_total}")
        print(f"           - Applied viewbox and typography geometry fixes")

    return compiled_count


def apply_layout_geometry_fixes(output_layout_dir: str) -> None:
    """
    Applies custom UI viewbox expansions and alignment fixes to compiled layouts:
    - charactercreate.layout: Widens 'Name' ("Nome do Personagem") from 140 to 260px,
      centers it, widens 'PetName' to 200px, widens 'CharacterClassDescription' to 500px,
      and sets default class text to "Destruidor".
    - tipmenu.layout: Sets Title to "Dica", adjusts Dialog width to 450px with 25px margins
      to prevent clipping against ornamental borders.
    - questdialogmenu.layout: Ensures reward stat labels have trailing space ("PO: 0", "XP: 0", "Fama: 0").
    """
    cc_path = os.path.join(output_layout_dir, "charactercreate.layout")
    if os.path.exists(cc_path):
        with open(cc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix CharacterClass
        class_pat = r'(<Window Type="GuiLook/StaticTextOutline" Name="CharacterClass"\s*>)([\s\S]*?)(</Window>)'
        rep_class = (
            r'\1\n'
            '         \t\t   <Property Name="UnifiedPosition" Value="{{.5,-300},{1,-175}}" />\n'
            '         \t\t   <Property Name="UnifiedSize" Value="{{0,600},{0,60}}" />\n'
            '\t\t\t<Property Name="Text" Value="Destruidor" />\n'
            '\t\t\t<Property Name="Font" Value="SerifHuge" />\n'
            '\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />\n'
            '\t\t\t<Property Name="AlwaysOnTop" Value="True" />\n'
            '\t\t    <Property Name="HorzTextFormatting" Value="CentreAligned" />\n'
            r'\t\t  \3'
        )
        content = re.sub(class_pat, rep_class, content)

        # Fix CharacterClassDescription
        desc_pat = r'(<Window Type="GuiLook/StaticText" Name="CharacterClassDescription"\s*>)([\s\S]*?)(</Window>)'
        rep_desc = (
            r'\1\n'
            '         \t\t   <Property Name="UnifiedPosition" Value="{{.5,-250},{1,-140}}" />\n'
            '         \t\t   <Property Name="UnifiedSize" Value="{{0,500},{0,64}}" />\n'
            '\t\t\t<Property Name="Font" Value="SerifSmall" />\n'
            '\t\t\t<Property Name="Text" Value="O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos." />\n'
            '\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />\n'
            '\t\t\t<Property Name="AlwaysOnTop" Value="True" />\n'
            '\t          <Property Name="HorzTextFormatting" Value="WordWrapCentreAligned" />\n'
            r'\t\t  \3'
        )
        content = re.sub(desc_pat, rep_desc, content)

        # Fix Name ("Nome do Personagem")
        name_pat = r'(<Window Type="GuiLook/StaticText" Name="Name"\s*>)([\s\S]*?)(</Window>)'
        rep_name = (
            r'\1\n'
            '            <Property Name="Text" Value="Nome do Personagem" />\n'
            '            <Property Name="UnifiedPosition" Value="{{.5,-130},{1,-88}}" />\n'
            '            <Property Name="UnifiedSize" Value="{{0,260},{0,24}}" />\n'
            '            <Property Name="HorzTextFormatting" Value="CentreAligned" />\n'
            '        <Property Name="MousePassThroughEnabled" Value="True" />\n'
            r'        \3'
        )
        content = re.sub(name_pat, rep_name, content)

        # Fix PetName ("Nome do Mascote")
        pet_pat = r'(<Window Type="GuiLook/StaticText" Name="PetName"\s*>)([\s\S]*?)(</Window>)'
        rep_pet = (
            r'\1\n'
            '            <Property Name="Text" Value="Nome do Mascote" />\n'
            '            <Property Name="UnifiedPosition" Value="{{0,-30},{0,140}}" />\n'
            '            <Property Name="UnifiedSize" Value="{{0,200},{0,24}}" />\n'
            '            <Property Name="HorzTextFormatting" Value="CentreAligned" />\n'
            '        <Property Name="MousePassThroughEnabled" Value="True" />\n'
            r'        \3'
        )
        content = re.sub(pet_pat, rep_pet, content)

        with open(cc_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Fix tipmenu.layout
    tip_path = os.path.join(output_layout_dir, "tipmenu.layout")
    if os.path.exists(tip_path):
        with open(tip_path, "rb") as f:
            raw = f.read()
        is_u16 = raw.startswith(b"\xff\xfe")
        txt = raw[2:].decode("utf-16le") if is_u16 else raw.decode("utf-8")

        # Framec & Title -> Dica
        framec_pattern = r'(<Window Type="GuiLook/ItemText" Name="Framec"\s*>)([\s\S]*?)(<Window Type="GuiLook/ItemText" Name="Frameb")'
        rep_framec = (
            r'\1\n'
            '            <Property Name="UnifiedPosition" Value="{{.5,-71},{.5,-205}}" />\n'
            '            <Property Name="UnifiedSize" Value="{{0,142},{0,28}}" />\n'
            '        <Window Type="GuiLook/StaticText" Name="Title">\n'
            '        <Property Name="HorzTextFormatting" Value="CentreAligned" />\n'
            '        <Property Name="VertFormatting" Value="CentreAligned" />\n'
            '        <Property Name="UnifiedSize" Value="{{0,142},{0,28}}" />\n'
            '\t\t<Property Name="TextColour" Value="FFFFFFFF"/>\n'
            '\t\t<Property Name="Font" Value="SerifBig"/>\n'
            '        <Property Name="Text" Value="Dica" />\n'
            '        </Window>   \n'
            '\t</Window>\n\n\n        '
            r'\3'
        )
        txt = re.sub(framec_pattern, rep_framec, txt)

        # Frameb size & position (height 265 instead of 350, eliminating giant void)
        frameb_pattern = r'(<Window Type="GuiLook/ItemText" Name="Frameb"\s*>)([\s\S]*?)(<Window Type="GuiLook/StaticText" Name="Dialog")'
        rep_frameb = (
            r'\1\n'
            '\t\t    <Property Name="UnifiedPosition" Value="{{.5,-250},{.5,-160}}" />\n'
            '\t\t    <Property Name="UnifiedSize" Value="{{0,500},{0,265}}" />\n\n\t\t'
            r'\3'
        )
        txt = re.sub(frameb_pattern, rep_frameb, txt)

        # Dialog static text inside Frameb
        dialog_pattern = r'(<Window Type="GuiLook/StaticText" Name="Dialog"\s*>)([\s\S]*?)(</Window>)'
        rep_dialog = (
            r'\1\n'
            '\t\t    <Property Name="Font" Value="SerifBig" />\n'
            '\t\t    <Property Name="HorzTextFormatting" Value="WordWrapCentreAligned" />\n'
            '\t\t    <Property Name="VertFormatting" Value="TopAligned" />\n'
            '\t\t    <Property Name="UnifiedPosition" Value="{{0,25},{0,25}}" />\n'
            '\t\t    <Property Name="UnifiedSize" Value="{{0,450},{0,180}}" />\n'
            '\t\t\t<Property Name="TextColour" Value="FFFFFFFF"/>\n'
            '\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />\n'
            '\t\t'
            r'\3'
        )
        txt = re.sub(dialog_pattern, rep_dialog, txt)

        # Adjust buttons inside Frameb
        ok_pattern = r'(<Window Type="GuiLook/StandardButton" Name="Ok"\s*>)([\s\S]*?)(</Window>)'
        rep_ok = (
            r'\1\n'
            '            <Property Name="UnifiedPosition" Value="{{.5,-76},{1,-45}}" />\n'
            '            <Property Name="UnifiedSize" Value="{{0,152},{0,28}}" />\n'
            '            <Property Name="Text" Value="Ok"/>\n'
            '\t\t<Property Name="onClick" Value="guiOk"/>\n'
            '    '
            r'\3'
        )
        txt = re.sub(ok_pattern, rep_ok, txt)

        showtips_pattern = r'(<Window Type="GuiLook/Checkbox" Name="ShowTips"\s*>)([\s\S]*?)(</Window>)'
        rep_showtips = (
            r'\1\n'
            '            <Property Name="Text" Value="Mostrar Dicas" />\n'
            '            <Property Name="UnifiedPosition" Value="{{.5,70},{1,-48}}" />\n'
            '            <Property Name="UnifiedSize" Value="{{0,50},{0,32}}" />\n'
            '        '
            r'\3'
        )
        txt = re.sub(showtips_pattern, rep_showtips, txt)

        out_b = (b"\xff\xfe" + txt.encode("utf-16le")) if is_u16 else txt.encode("utf-8")
        with open(tip_path, "wb") as f:
            f.write(out_b)

    # Fix questdialogmenu.layout (blank child texts to prevent double colons)
    qd_path = os.path.join(output_layout_dir, "questdialogmenu.layout")
    if os.path.exists(qd_path):
        with open(qd_path, "rb") as f:
            raw = f.read()
        is_u16 = raw.startswith(b"\xff\xfe")
        txt = raw[2:].decode("utf-16le") if is_u16 else raw.decode("utf-8")
        txt = re.sub(r'<Property Name="Text" Value="GP:0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="PO:0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="PO: 0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="XP:0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="XP: 0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="Fame:0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="Fama:0"\s*/>', '<Property Name="Text" Value="" />', txt)
        txt = re.sub(r'<Property Name="Text" Value="Fama: 0"\s*/>', '<Property Name="Text" Value="" />', txt)
        out_b = (b"\xff\xfe" + txt.encode("utf-16le")) if is_u16 else txt.encode("utf-8")
        with open(qd_path, "wb") as f:
            f.write(out_b)


def main() -> int:
    default_catalog = r"translation_ptbr\translation_catalog.json"
    default_pak = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
    default_output_dat = r"translation_ptbr\translations\translation.dat"
    default_output_layout = r"translation_ptbr\media\UI"

    parser = argparse.ArgumentParser(description="Torchlight Translation Compilation Tool")
    parser.add_argument(
        "--catalog",
        default=default_catalog,
        help=f"Path to translation_catalog.json (default: {default_catalog})"
    )
    parser.add_argument(
        "--pak-path",
        default=default_pak,
        help=f"Path to Pak.zip for base layout extraction (default: {default_pak})"
    )
    parser.add_argument(
        "--output-dat",
        default=default_output_dat,
        help=f"Path to output translation.dat (default: {default_output_dat})"
    )
    parser.add_argument(
        "--output-layout-dir",
        default=default_output_layout,
        help=f"Path to output media/UI/ layout directory (default: {default_output_layout})"
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Do not fallback to original text for untranslated strings"
    )
    parser.add_argument(
        "--skip-layouts",
        action="store_true",
        help="Skip compiling .layout files from Pak.zip"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()
    verbose = not args.quiet
    fallback = not args.no_fallback

    catalog_path = os.path.abspath(args.catalog)
    pak_path = os.path.abspath(args.pak_path)
    output_dat = os.path.abspath(args.output_dat)
    output_layout = os.path.abspath(args.output_layout_dir)

    if verbose:
        print("=" * 70)
        print(" Torchlight pt-BR Translation Compilation Tool")
        print(f" Catalog:    {catalog_path}")
        print(f" Output DAT: {output_dat}")
        print(f" Output UI:  {output_layout}")
        print("=" * 70)

    try:
        catalog = load_catalog(catalog_path)
    except Exception as e:
        print(f"[Error] Failed to load catalog: {e}", file=sys.stderr)
        return 1

    try:
        blocks_written = generate_translation_dat(
            catalog,
            output_dat,
            fallback_to_original=fallback,
            verbose=verbose
        )
    except Exception as e:
        print(f"[Error] Failed to compile translation.dat: {e}", file=sys.stderr)
        return 1

    layouts_compiled = 0
    if args.skip_layouts or not os.path.exists(pak_path):
        if verbose:
            print("[Compiler] Skipping layout extraction from Pak.zip (using existing localized layouts).")
    else:
        try:
            layouts_compiled = compile_layout_files(
                catalog,
                pak_path,
                output_layout,
                fallback_to_original=fallback,
                verbose=verbose
            )
        except Exception as e:
            print(f"[Error] Failed to compile layout files: {e}", file=sys.stderr)
            return 1

    if verbose:
        print("-" * 50)
        print(f"[Success] Compilation complete:")
        print(f"  - translation.dat: {blocks_written} blocks")
        print(f"  - Localized UI:    {layouts_compiled} .layout files")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
