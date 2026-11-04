#!/usr/bin/env python3
"""
tools/localize_player_units.py - Localizes player class definitions in Torchlight.

The game loads character classes and their descriptions directly from:
- media/units/players/Destroyer/DESTROYER.DAT.adm
- media/units/players/Alchemist/ALCHEMIST.DAT.adm
- media/units/players/Vanquisher/VANQUISHER.DAT.adm

This script extracts these files from Pak.zip, updates their string tables
with official pt-BR translations for DISPLAYNAME, DESCRIPTION, and skill tree tabs,
and writes them to translation_ptbr/media/units/players/ to override Pak.zip.
"""

import os
import shutil
import struct
import zipfile

REPLACEMENTS = {
    "media/units/players/Destroyer/DESTROYER.DAT.adm": {
        41877: "Destruidor",
        41878: "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.",
        41888: "Berserker",
        41889: "Titã",
        41890: "Espectral",
    },
    "media/units/players/Alchemist/ALCHEMIST.DAT.adm": {
        41820: "Alquimista",
        41823: "O Alquimista canaliza o poder do Âmbar para atacar de longe e invocar lacaios ao seu lado.",
        41844: "Arcano",
        41846: "Conhecimento",
        41848: "Batalha",
    },
    "media/units/players/Vanquisher/VANQUISHER.DAT.adm": {
        41900: "Vingadora",
        41902: "A Vingadora é uma atiradora perita e usa armadilhas para confundir e debilitar seus inimigos.",
        41912: "Atiradora",
        41913: "Ladina",
        41914: "Árbitra",
    },
}


def patch_adm_file(raw_data: bytes, token_map: dict[int, str]) -> bytes:
    ver, num_strings = struct.unpack_from("<II", raw_data, 0)
    if ver != 1:
        raise ValueError(f"Unsupported ADM version: {ver}")

    pos = 8
    strings = []
    for _ in range(num_strings):
        t_id, s_len = struct.unpack_from("<II", raw_data, pos)
        pos += 8
        s = raw_data[pos : pos + s_len * 2].decode("utf-16le")
        pos += s_len * 2
        strings.append((t_id, s))

    # Binary tree / node data follows the string table
    node_data = raw_data[pos:]

    # Rebuild string table with replacements
    new_string_table = bytearray()
    for t_id, s in strings:
        if t_id in token_map:
            new_s = token_map[t_id]
            print(f"  Token {t_id}: '{s}' -> '{new_s}'")
        else:
            new_s = s
        encoded = new_s.encode("utf-16le")
        char_count = len(new_s)
        new_string_table += struct.pack("<II", t_id, char_count)
        new_string_table += encoded

    header = struct.pack("<II", 1, len(strings))
    return header + bytes(new_string_table) + node_data


def main():
    pak_path = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
    if not os.path.exists(pak_path):
        raise FileNotFoundError(f"Pak.zip not found at {pak_path}")

    with zipfile.ZipFile(pak_path, "r") as z:
        for rel_path, token_map in REPLACEMENTS.items():
            print(f"[PlayerUnits] Processing {rel_path}...")
            raw = z.read(rel_path)
            patched = patch_adm_file(raw, token_map)

            out_path = os.path.join("translation_ptbr", rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(patched)
            print(f"  Saved to {out_path} ({len(patched)} bytes)")

            # Also deploy directly to local game folder for testing
            game_out_path = os.path.join(r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight", rel_path)
            os.makedirs(os.path.dirname(game_out_path), exist_ok=True)
            with open(game_out_path, "wb") as f:
                f.write(patched)
            print(f"  Deployed to {game_out_path}")

    print("[PlayerUnits] SUCCESS: All player classes localized.")


if __name__ == "__main__":
    main()
