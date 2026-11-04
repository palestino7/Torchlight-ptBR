#!/usr/bin/env python3
"""
tools/patch_torchlight_exe.py - Torchlight Executable Localizer

Patches Torchlight.exe to localize hardcoded strings:
- Shadows options: "Off", "Lighting Only", "Low", "Medium", "High", "Very High"
  -> "Desligado", "Apenas Iluminação", "Baixo", "Médio", "Alto", "Muito Alto"
- Particles: "Low", "Medium", "High"
  -> "Baixo", "Médio", "Alto"
- TipMenu Title: "Tip" -> "Dica" (UTF-16LE)
- Character Creation screen:
  - Class Titles: "Destroyer", "Alchemist", "Vanquisher"
    -> "Destruidor", "Alquimista", "Conquistadora"
  - Class Descriptions:
    -> "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos."
    -> "O Alquimista canaliza o poder do Âmbar para atacar de longe e invocar lacaios."
    -> "A Conquistadora é uma atiradora perita e usa armadilhas para debilitar seus inimigos."

Works by:
1. Writing UI option strings into .rdata slack space at file offset 0x7e6912 (VA 0xbe7712).
2. Writing character class descriptions into .rdata and .text slack spaces.
3. Injecting high-performance assembly hooks in .text slack space at 0x65b0c0 (VA 0xa5bcc0).
4. Updating 32-bit pointer opcodes and hooking CharacterCreate::update call sites.
5. Automatically backing up the original binary to Torchlight.exe.orig.
"""

import argparse
import os
import shutil
import struct

SLACK_RAW_START = 0x7e6912
SLACK_VA_START = 0xbe7712

STRINGS_TO_EMBED = [
    ("Desligado", b"Desligado\x00"),                              # len 10
    ("Apenas Iluminacao", b"Apenas Ilumina\xe7\xe3o\x00"),        # len 18
    ("Baixo", b"Baixo\x00"),                                      # len 6
    ("Medio", b"M\xe9dio\x00"),                                   # len 6
    ("Alto", b"Alto\x00"),                                        # len 5
    ("Muito Alto", b"Muito Alto\x00"),                            # len 11
    ("Dica", "Dica\x00".encode("utf-16le")),                     # len 10
]

EMBEDDED_VAS = {}
curr_raw = SLACK_RAW_START
curr_va = SLACK_VA_START
for name, data_bytes in STRINGS_TO_EMBED:
    EMBEDDED_VAS[name] = curr_va
    curr_raw += len(data_bytes)
    curr_va += len(data_bytes)

# Push offsets to update in Torchlight.exe (Build 17685)
PATCH_TABLE = [
    # TipMenu::init (0x5af740) - Modal Title "Tip" -> "Dica"
    (0x1af76a, 0xa8fc0c, EMBEDDED_VAS["Dica"]),

    # SettingsMenu::static_init (0x9a1850)
    (0x5a0c55, 0xa89a94, EMBEDDED_VAS["Desligado"]),
    (0x5a0c65, 0xa89a84, EMBEDDED_VAS["Apenas Iluminacao"]),
    (0x5a0c7d, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x5a0c92, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x5a0ca7, 0xa89a70, EMBEDDED_VAS["Alto"]),
    (0x5a0cbc, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),
    (0x5a0d05, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x5a0d15, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x5a0d2d, 0xa89a70, EMBEDDED_VAS["Alto"]),

    # TU1 static_init (0x9574b0)
    (0x5568b5, 0xa89a94, EMBEDDED_VAS["Desligado"]),
    (0x5568c5, 0xa89a84, EMBEDDED_VAS["Apenas Iluminacao"]),
    (0x5568dd, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x5568f2, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x556907, 0xa89a70, EMBEDDED_VAS["Alto"]),
    (0x55691c, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),
    (0x556965, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x556975, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x55698d, 0xa89a70, EMBEDDED_VAS["Alto"]),

    # TU3 static_init (0xa27f20)
    (0x627325, 0xa89a94, EMBEDDED_VAS["Desligado"]),
    (0x627335, 0xa89a84, EMBEDDED_VAS["Apenas Iluminacao"]),
    (0x62734d, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x627362, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x627377, 0xa89a70, EMBEDDED_VAS["Alto"]),
    (0x62738c, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),
    (0x6273e5, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x6273f5, 0xa89a78, EMBEDDED_VAS["Medio"]),
    (0x62740d, 0xa89a70, EMBEDDED_VAS["Alto"]),
]


def patch_executable(exe_path: str, backup: bool = True) -> bool:
    if not os.path.exists(exe_path):
        print(f"[Error] File not found: {exe_path}")
        return False

    with open(exe_path, "rb") as f:
        data = bytearray(f.read())

    # Verify executable build
    if len(data) != 10717328:
        print(f"[Warning] Unexpected binary size: {len(data)} (expected 10,717,328 for Steam Build 17685)")

    # Create backup if requested
    backup_path = exe_path + ".orig"
    if backup and not os.path.exists(backup_path):
        shutil.copy2(exe_path, backup_path)
        print(f"[Backup] Created backup at {backup_path}")

    # 1. Write localized strings into .rdata slack space
    curr_offset = SLACK_RAW_START
    for name, sbytes in STRINGS_TO_EMBED:
        data[curr_offset : curr_offset + len(sbytes)] = sbytes
        curr_offset += len(sbytes)

    # 2. Patch push opcodes
    patched_count = 0
    for raw_offset, orig_va, new_va in PATCH_TABLE:
        opcode = data[raw_offset]
        current_va = struct.unpack_from("<I", data, raw_offset + 1)[0]
        if opcode != 0x68:
            print(f"[Warning] Offset {hex(raw_offset)} has opcode {hex(opcode)} (expected 0x68 'push')")
            continue
        if current_va != orig_va and current_va != new_va:
            print(f"[Warning] Offset {hex(raw_offset)} has target {hex(current_va)} (expected {hex(orig_va)})")
            continue

        struct.pack_into("<I", data, raw_offset + 1, new_va)
        patched_count += 1

    # 3. Localized character class names and descriptions in .data slack space (0x7e6a10, VA 0xbe8010)
    data_slack_raw = 0x7e6a10
    data_slack_va = 0xbe8010

    s_destruidor = b"Destruidor\x00"
    s_alquimista = b"Alquimista\x00"
    s_conquistadora = b"Conquistadora\x00"
    s_desc_d = "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.\x00".encode("windows-1252")
    s_desc_a = "O Alquimista canaliza o poder do \xc2mbar para atacar de longe e invocar lacaios.\x00".encode("windows-1252")
    s_desc_v = "A Conquistadora \xe9 uma atiradora perita e usa armadilhas para debilitar seus inimigos.\x00".encode("windows-1252")

    strings_data = [
        ("s_dest", s_destruidor),
        ("s_alch", s_alquimista),
        ("s_vanq", s_conquistadora),
        ("s_desc_d", s_desc_d),
        ("s_desc_a", s_desc_a),
        ("s_desc_v", s_desc_v),
    ]

    vas_data = {}
    cur_r = data_slack_raw
    cur_v = data_slack_va
    for sname, sbytes in strings_data:
        vas_data[sname] = cur_v
        data[cur_r : cur_r + len(sbytes)] = sbytes
        cur_r += len(sbytes)
        cur_v += len(sbytes)
    assert cur_r <= 0x7e6ee0, "Overflow in .data slack space"

    # 4. Clean hook functions in .text slack space at 0x65b0aa (VA 0xa5bcaa)
    # Hook 1: Intercepts c_str() call for class name and substitutes translated pointer
    # Hook 2: Intercepts c_str() call for class description and substitutes translated pointer
    hook_raw = 0x65b0aa
    hook_va = 0xa5bcaa

    hook_bytes = bytearray([
        # 0x00: hook_class_name
        0xff, 0x15, 0x90, 0xc3, 0xa5, 0x00, # call dword ptr [0xa5c390]
        0x80, 0x38, 0x44,                   # cmp byte ptr [eax], 'D'
        0x74, 0x0b,                         # je .Lname_dest (+11 -> 0x16)
        0x80, 0x38, 0x41,                   # cmp byte ptr [eax], 'A'
        0x74, 0x0c,                         # je .Lname_alch (+12 -> 0x1c)
        0x80, 0x38, 0x56,                   # cmp byte ptr [eax], 'V'
        0x74, 0x0d,                         # je .Lname_vanq (+13 -> 0x22)
        0xc3,                               # ret (0x15)
        # 0x16: .Lname_dest
        0xb8,
    ])
    hook_bytes += struct.pack("<I", vas_data["s_dest"])
    hook_bytes += bytearray([0xc3]) # ret (0x1b)

    # 0x1c: .Lname_alch
    hook_bytes += bytearray([0xb8])
    hook_bytes += struct.pack("<I", vas_data["s_alch"])
    hook_bytes += bytearray([0xc3]) # ret (0x21)

    # 0x22: .Lname_vanq
    hook_bytes += bytearray([0xb8])
    hook_bytes += struct.pack("<I", vas_data["s_vanq"])
    hook_bytes += bytearray([0xc3]) # ret (0x27)

    assert len(hook_bytes) == 0x28

    # 0x28: hook_class_desc
    hook_bytes += bytearray([
        0xff, 0x15, 0x90, 0xc3, 0xa5, 0x00, # call dword ptr [0xa5c390] (0x28)
        0x80, 0x38, 0x54,                   # cmp byte ptr [eax], 'T' (0x2e)
        0x75, 0x12,                         # jne .Ldesc_done (+18 -> 0x45)
        0x80, 0x78, 0x04, 0x44,             # cmp byte ptr [eax+4], 'D' (0x33)
        0x74, 0x0d,                         # je .Ldesc_dest (+13 -> 0x46)
        0x80, 0x78, 0x04, 0x41,             # cmp byte ptr [eax+4], 'A' (0x39)
        0x74, 0x0d,                         # je .Ldesc_alch (+13 -> 0x4c)
        0x80, 0x78, 0x04, 0x56,             # cmp byte ptr [eax+4], 'V' (0x3f)
        0x74, 0x0d,                         # je .Ldesc_vanq (+13 -> 0x52)
        # 0x45: .Ldesc_done
        0xc3,                               # ret
        # 0x46: .Ldesc_dest
        0xb8,
    ])
    hook_bytes += struct.pack("<I", vas_data["s_desc_d"])
    hook_bytes += bytearray([0xc3]) # ret (0x4b)

    # 0x4c: .Ldesc_alch
    hook_bytes += bytearray([0xb8])
    hook_bytes += struct.pack("<I", vas_data["s_desc_a"])
    hook_bytes += bytearray([0xc3]) # ret (0x51)

    # 0x52: .Ldesc_vanq
    hook_bytes += bytearray([0xb8])
    hook_bytes += struct.pack("<I", vas_data["s_desc_v"])
    hook_bytes += bytearray([0xc3]) # ret (0x57)

    assert len(hook_bytes) == 0x58
    assert hook_raw + len(hook_bytes) <= 0x65b200, "Overflow in .text slack space"
    data[hook_raw : hook_raw + len(hook_bytes)] = hook_bytes

    # 5. Patch call sites in CharacterCreate::update
    # Site 2 at 0x5b6dbe (raw 0x1b61be): call hook_class_name; push eax; nop
    site2_raw = 0x1b61be
    site2_va = 0x5b6dbe
    rel2 = hook_va - (site2_va + 5)
    data[site2_raw : site2_raw + 7] = b"\xe8" + struct.pack("<i", rel2) + b"\x50\x90"

    # Site 3 at 0x5b6e42 (raw 0x1b6242): call hook_class_desc; push eax; nop
    site3_raw = 0x1b6242
    site3_va = 0x5b6e42
    rel3 = (hook_va + 0x28) - (site3_va + 5)
    data[site3_raw : site3_raw + 7] = b"\xe8" + struct.pack("<i", rel3) + b"\x50\x90"

    with open(exe_path, "wb") as f:
        f.write(data)

    print(f"[Success] Patched {patched_count}/{len(PATCH_TABLE)} option instructions in {exe_path}")
    print("          - Injected CharacterCreate class titles & descriptions localizer")
    print(f"          - Embedded strings written to {hex(SLACK_RAW_START)}")
    return True


def revert_executable(exe_path: str) -> bool:
    backup_path = exe_path + ".orig"
    if not os.path.exists(backup_path):
        print(f"[Error] Backup file not found: {backup_path}")
        return False
    shutil.copy2(backup_path, exe_path)
    print(f"[Revert] Restored {exe_path} from {backup_path}")
    return True


def main():
    default_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Torchlight.exe"
    parser = argparse.ArgumentParser(description="Patch Torchlight.exe to localize options dropdowns and UI strings")
    parser.add_argument("--exe", default=default_exe, help=f"Path to Torchlight.exe (default: {default_exe})")
    parser.add_argument("--revert", action="store_true", help="Revert to Torchlight.exe.orig")
    args = parser.parse_args()

    if args.revert:
        revert_executable(args.exe)
    else:
        patch_executable(args.exe)


if __name__ == "__main__":
    main()
