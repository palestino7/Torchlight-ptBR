#!/usr/bin/env python3
"""
tools/extract_strings.py - Torchlight Text Extraction Tool

Extracts all translatable strings from Torchlight Pak.zip:
- Parses all .dat.adm binary files using the reverse-engineered ADM string table format.
- Parses all .layout XML files under media/UI/.
- Filters out engine tokens, internal variable names, file paths, and non-translatable tokens.
- Categorizes strings into: UI, Quests, Items, Skills, Affixes, Monsters, Recipes, Globals, Dungeons.
- Saves the extracted catalog to translation_ptbr/translation_catalog.json.

Part of Milestone 1 (M1) of the Torchlight pt-BR translation project.
"""

import argparse
import html
import json
import os
import re
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Known property keys that are code identifiers, not translatable text
CODE_KEYS = {
    'NAME', 'TYPE', 'MIN', 'MAX', 'RANK', 'WEIGHT', 'DURATION', 'ACTIVATION',
    'PASSIVE', 'AFFIX', 'SLOTS_OCCUPY', 'UNITTYPES', 'EFFECT', 'ARMOR', 'DAMAGE',
    'FIRE', 'ICE', 'LIGHTNING', 'POISON', 'LEVEL', 'COST', 'RARITY', 'SPEED',
    'RANGE', 'ICON', 'TEXTURE', 'MESH', 'SKELETON', 'ANIMATION', 'SCALE',
    'COLLISION', 'HEALTH', 'MANA', 'STRENGTH', 'DEXTERITY', 'MAGIC', 'DEFENSE',
    'PARENT_LINE', 'LINE_NAME', 'GUID', 'BASEFILE', 'MODEL', 'MATERIAL',
    'SOUND', 'PARTICLE', 'GRAPH', 'MISSILE', 'USES', 'SLOTS', 'VALUE',
    'BUY_VALUE', 'SELL_VALUE', 'MIN_DAMAGE', 'MAX_DAMAGE', 'UNITTYPE',
    'ITEM_TYPE', 'EQUIP_SLOT', 'CHANCE', 'FREQUENCY', 'RADIUS', 'FALLOFF',
    'LIFETIME', 'VELOCITY', 'ACCELERATION', 'FORCE', 'MASS', 'FRICTION',
    'BOUNCE', 'RESTITUTION', 'DAMPING', 'DRAG', 'TORQUE', 'ANGULAR_VELOCITY'
}

# File extensions that indicate assets, textures, or code files, not text
NON_TRANSLATABLE_EXTENSIONS = (
    ".dds", ".mesh", ".png", ".ogg", ".wav", ".material", ".skeleton",
    ".layout", ".font", ".ttf", ".dat", ".adm", ".mp3", ".hlsl", ".cg"
)

# Standard categories defined by PROJECT.md specification
STANDARD_CATEGORIES = [
    "UI",
    "Quests",
    "Items",
    "Skills",
    "Affixes",
    "Monsters",
    "Recipes",
    "Dungeons",
    "Globals"
]

CATEGORY_PRIORITY = {cat: i for i, cat in enumerate(STANDARD_CATEGORIES)}


def extract_adm_strings(data: bytes) -> list[tuple[int, str]]:
    """
    Extracts all strings from the UTF-16LE string table of a compiled Torchlight ADM file.

    ADM File Structure:
    - 4 bytes uint32: version (must be 1)
    - 4 bytes uint32: num_strings
    - For each string:
      - 4 bytes uint32: token_id
      - 4 bytes uint32: char_count (number of UTF-16 characters)
      - char_count * 2 bytes: UTF-16LE encoded string
    """
    if len(data) < 8:
        return []

    ver, num_strings = struct.unpack_from("<II", data, 0)
    if ver != 1:
        return []

    pos = 8
    data_len = len(data)
    strings = []

    for _ in range(num_strings):
        if pos + 8 > data_len:
            break
        t_id, s_len = struct.unpack_from("<II", data, pos)
        pos += 8
        byte_len = s_len * 2
        if pos + byte_len > data_len:
            break
        try:
            s = data[pos : pos + byte_len].decode("utf-16le", errors="ignore")
            strings.append((t_id, s))
        except Exception:
            pass
        pos += byte_len

    return strings


def extract_layout_strings(layout_text: str) -> list[str]:
    """
    Extracts translatable text properties from a CEGUI .layout XML file.
    Matches properties like:
    - <Property Name="Text" Value="..." />
    - <Property Name="Tooltip" Value="..." />
    - <Property Name="Text">...</Property>
    - <Property Name="Tooltip">...</Property>
    Unescapes XML entities so extracted text matches runtime CStringTranslate lookups.
    """
    matches_attr = re.findall(r'<Property\s+Name="(?:Text|Tooltip)"\s+Value="([^"]*)"', layout_text, re.IGNORECASE)
    matches_tag = re.findall(r'<Property\s+Name="(?:Text|Tooltip)"\s*>([^<]*)</Property\s*>', layout_text, re.IGNORECASE)
    results = []
    for m in matches_attr + matches_tag:
        clean = html.unescape(m.strip())
        if clean and len(clean) > 1 and not re.match(r"^[+-]?[0-9\.]+$", clean):
            results.append(clean)
    return results


def is_valid_translatable_string(s: str) -> bool:
    """
    Filters out internal code identifiers, file paths, numbers, and engine keywords.
    Returns True only for genuine translatable player-facing text.
    """
    s_strip = s.strip()
    if not s_strip or len(s_strip) < 2:
        return False

    # 1. Filter known code property keys
    if s_strip.upper() in CODE_KEYS:
        return False

    # Normalize path separators and lowercase for path inspection
    s_norm = s_strip.replace("\\", "/").lower()

    # 2. Filter asset folder prefixes
    if s_norm.startswith(("media/", "../", "./", "dataeditor/")):
        return False

    # 3. Filter asset and binary file extensions (case-insensitive)
    if any(s_norm.endswith(ext.lower()) for ext in NON_TRANSLATABLE_EXTENSIONS):
        return False

    # 4. Filter internal path tokens and texture replacement pairs without spaces (e.g. goblin_archer/goblin_archer)
    if "/" in s_norm and " " not in s_strip:
        return False

    # 5. Filter pure numeric values (floats, negative numbers, positive numbers, integers)
    if re.match(r"^[+-]?[0-9\.]+$", s_strip):
        return False

    # 6. Filter internal code identifiers like GEM_AMETHYST_01 or SWORD_T01
    if re.match(r"^[A-Z0-9_]{3,}$", s_strip) and "_" in s_strip and " " not in s_strip:
        return False

    return True


def categorize_file(file_path: str) -> str:
    """
    Maps a game file path within Pak.zip to one of the 9 canonical translation categories.
    """
    lower = file_path.lower().replace("\\", "/")
    if lower.endswith(".layout"):
        return "UI"
    if "quests/" in lower or "cinematics/" in lower or "units/npcs/" in lower:
        return "Quests"
    if "units/items/" in lower or "media/sets/" in lower:
        return "Items"
    if "skills/" in lower or "perks/" in lower:
        return "Skills"
    if "affixes/" in lower:
        return "Affixes"
    if "units/monsters/" in lower:
        return "Monsters"
    if "recipes/" in lower:
        return "Recipes"
    if "dungeons/" in lower or "levelsets/" in lower or "layouts/" in lower:
        return "Dungeons"
    return "Globals"


def extract_all_from_pak(pak_path: str, verbose: bool = True) -> tuple[dict, dict]:
    """
    Iterates through Pak.zip, parsing all ADM and layout files.
    Returns:
    - best_entries: dict mapping clean_string -> (category, source_file)
    - stats: summary statistics dict
    """
    if not os.path.exists(pak_path):
        raise FileNotFoundError(f"Torchlight Pak.zip not found at: {pak_path}")

    # Map string -> (category, source_file)
    best_entries: dict[str, tuple[str, str]] = {}
    file_counts = Counter()
    total_adm_processed = 0
    total_layout_processed = 0

    with zipfile.ZipFile(pak_path, "r") as z:
        namelist = z.namelist()
        total_files = len(namelist)
        if verbose:
            print(f"[Extract] Scanning {total_files} files inside {pak_path}...")

        for name in namelist:
            if name.endswith("/"):
                continue

            lower = name.lower().replace("\\", "/")

            if lower.endswith(".layout"):
                total_layout_processed += 1
                try:
                    raw = z.read(name)
                    text = raw.decode("utf-8", errors="ignore")
                    strings = extract_layout_strings(text)
                    for s in strings:
                        # UI layout strings have highest priority
                        if s not in best_entries or CATEGORY_PRIORITY["UI"] < CATEGORY_PRIORITY[best_entries[s][0]]:
                            best_entries[s] = ("UI", name)
                    file_counts["UI"] += 1
                except Exception as e:
                    if verbose:
                        print(f"[Warning] Failed parsing layout {name}: {e}")
                continue

            if lower.endswith(".dat.adm"):
                total_adm_processed += 1
                cat = categorize_file(name)
                try:
                    raw = z.read(name)
                    extracted = extract_adm_strings(raw)
                    for t_id, s in extracted:
                        if is_valid_translatable_string(s):
                            clean = s.strip()
                            if clean not in best_entries or CATEGORY_PRIORITY[cat] < CATEGORY_PRIORITY[best_entries[clean][0]]:
                                best_entries[clean] = (cat, name)
                    file_counts[cat] += 1
                except Exception as e:
                    if verbose:
                        print(f"[Warning] Failed parsing ADM {name}: {e}")
                continue

    stats = {
        "total_files_in_pak": total_files,
        "total_adm_processed": total_adm_processed,
        "total_layout_processed": total_layout_processed,
        "files_per_category": dict(file_counts),
        "total_unique_strings": len(best_entries)
    }

    return best_entries, stats


def build_catalog(
    best_entries: dict[str, tuple[str, str]],
    game_version: str = "1.15"
) -> dict:
    """
    Constructs the structured catalog according to PROJECT.md interface contract:
    {
      "metadata": {
        "game": "Torchlight",
        "version": "1.15",
        "total_strings": 17565,
        "extracted_at": "...",
        "category_counts": { ... }
      },
      "categories": {
        "UI": [...],
        ...
      }
    }
    """
    grouped: dict[str, list[dict]] = {cat: [] for cat in STANDARD_CATEGORIES}

    # First group by category and sort strings deterministically
    strings_by_cat = defaultdict(list)
    for string, (cat, context) in best_entries.items():
        strings_by_cat[cat].append((string, context))

    category_counts = {}
    for cat in STANDARD_CATEGORIES:
        items = strings_by_cat[cat]
        # Deterministic sort: shortest first, then alphabetical
        items.sort(key=lambda x: (len(x[0]), x[0]))
        category_counts[cat] = len(items)

        for idx, (string, context) in enumerate(items, 1):
            entry_id = f"{cat}_{idx:04d}"
            grouped[cat].append({
                "id": entry_id,
                "original": string,
                "translation": "",
                "context": context
            })

    catalog = {
        "metadata": {
            "game": "Torchlight",
            "version": game_version,
            "total_strings": len(best_entries),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "category_counts": category_counts
        },
        "categories": grouped
    }

    return catalog


def main() -> int:
    default_pak = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
    default_output = r"translation_ptbr\translation_catalog.json"

    parser = argparse.ArgumentParser(description="Torchlight Text Extraction Tool")
    parser.add_argument(
        "--pak-path",
        default=default_pak,
        help=f"Path to Torchlight Pak.zip (default: {default_pak})"
    )
    parser.add_argument(
        "--output-catalog",
        default=default_output,
        help=f"Path to output translation_catalog.json (default: {default_output})"
    )
    parser.add_argument(
        "--game-version",
        default="1.15",
        help="Game engine version (default: 1.15)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    pak_path = os.path.abspath(args.pak_path)
    output_catalog = os.path.abspath(args.output_catalog)

    if verbose:
        print("=" * 70)
        print(" Torchlight pt-BR Text Extraction Tool")
        print(f" Source: {pak_path}")
        print(f" Output: {output_catalog}")
        print("=" * 70)

    try:
        best_entries, stats = extract_all_from_pak(pak_path, verbose=verbose)
    except Exception as e:
        print(f"[Error] Failed extracting from Pak.zip: {e}", file=sys.stderr)
        return 1

    catalog = build_catalog(best_entries, game_version=args.game_version)

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(output_catalog), exist_ok=True)

    with open(output_catalog, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    if verbose:
        print("\nExtraction Summary:")
        print(f"  ADM Files Processed:    {stats['total_adm_processed']}")
        print(f"  Layout Files Processed: {stats['total_layout_processed']}")
        print(f"  Total Unique Strings:   {stats['total_unique_strings']}")
        print("-" * 50)
        for cat in STANDARD_CATEGORIES:
            count = catalog["metadata"]["category_counts"][cat]
            print(f"  Category {cat:12} : {count:6d} strings")
        print("-" * 50)
        print(f"[Success] Catalog saved to: {output_catalog}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
