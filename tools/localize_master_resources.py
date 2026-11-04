#!/usr/bin/env python3
"""
tools/localize_master_resources.py - Localizes masterresourceunits.dat.ADM for Torchlight.

Torchlight pre-caches all unit definitions (including player classes and descriptions)
in media/masterresourceunits.dat.ADM. This script patches the binary ADM string table
so that the Character Creation screen natively displays Portuguese class names and
descriptions without relying on individual unit files.
"""

import os
import struct
import shutil

REPLACEMENTS = {
    39509: "Alquimista",
    39512: "O Alquimista canaliza o poder do Âmbar para atacar de longe e invocar lacaios ao seu lado.",
    39535: "Conhecimento",
    39568: "Destruidor",
    39569: "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.",
    39578: "Titã",
    39590: "Vencedora",
    39592: "A Vencedora é uma atiradora perita e usa armadilhas para confundir e debilitar seus inimigos.",
    39603: "Ladina",
}

def patch_master_resources(src_path: str) -> bytes:
    with open(src_path, "rb") as f:
        raw_data = f.read()

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

    node_data = raw_data[pos:]

    new_string_table = bytearray()
    replaced_count = 0
    for t_id, s in strings:
        if t_id in REPLACEMENTS:
            new_s = REPLACEMENTS[t_id]
            print(f"  Token {t_id}: '{s}' -> '{new_s}'")
            replaced_count += 1
        else:
            new_s = s
        encoded = new_s.encode("utf-16le")
        char_count = len(new_s)
        new_string_table += struct.pack("<II", t_id, char_count)
        new_string_table += encoded

    print(f"Patched {replaced_count} tokens in masterresourceunits.dat.ADM")
    header = struct.pack("<II", 1, len(strings))
    return header + bytes(new_string_table) + node_data

def main():
    appdata_mru = os.path.expandvars(r"%APPDATA%\runic games\torchlight\masterresourceunits.dat.ADM")
    if not os.path.exists(appdata_mru):
        # Fallback to Pak.zip
        import zipfile
        pak_path = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
        with zipfile.ZipFile(pak_path, "r") as z:
            data = z.read("media/masterresourceunits.dat.ADM")
            with open(appdata_mru, "wb") as f:
                f.write(data)

    patched_bytes = patch_master_resources(appdata_mru)

    # 1. Save to translation_ptbr/media/
    ptbr_dest = "translation_ptbr/media/masterresourceunits.dat.ADM"
    os.makedirs(os.path.dirname(ptbr_dest), exist_ok=True)
    with open(ptbr_dest, "wb") as f:
        f.write(patched_bytes)
    print(f"Saved to {ptbr_dest}")

    # 2. Deploy to local Steam common/Torchlight/media/
    steam_dest = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\media\masterresourceunits.dat.ADM"
    os.makedirs(os.path.dirname(steam_dest), exist_ok=True)
    with open(steam_dest, "wb") as f:
        f.write(patched_bytes)
    print(f"Deployed to {steam_dest}")

    # 3. Deploy to %APPDATA%\runic games\torchlight\masterresourceunits.dat.ADM
    with open(appdata_mru, "wb") as f:
        f.write(patched_bytes)
    print(f"Deployed to {appdata_mru}")

    # 4. Deploy to %APPDATA%\runic games\torchlight\mods\Traducao_ptBR\media\masterresourceunits.dat.ADM
    mod_dest = os.path.expandvars(r"%APPDATA%\runic games\torchlight\mods\Traducao_ptBR\media\masterresourceunits.dat.ADM")
    os.makedirs(os.path.dirname(mod_dest), exist_ok=True)
    with open(mod_dest, "wb") as f:
        f.write(patched_bytes)
    print(f"Deployed to {mod_dest}")

if __name__ == "__main__":
    main()
