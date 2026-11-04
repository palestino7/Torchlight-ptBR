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

    # 3. Embed Alchemist and Vanquisher descriptions in .rdata slack
    s_desc_a = "O Alquimista canaliza o poder do \xc2mbar para atacar de longe e invocar lacaios.\x00".encode("windows-1252")
    s_desc_v = "A Conquistadora \xe9 uma atiradora perita e usa armadilhas para debilitar seus inimigos.\x00".encode("windows-1252")

    desc_a_raw = 0x7e6954
    desc_a_va = 0xbe7754
    data[desc_a_raw : desc_a_raw + len(s_desc_a)] = s_desc_a

    desc_v_raw = desc_a_raw + len(s_desc_a)
    desc_v_va = desc_a_va + len(s_desc_a)
    data[desc_v_raw : desc_v_raw + len(s_desc_v)] = s_desc_v
    assert desc_v_raw + len(s_desc_v) <= 0x7e6a00, "Overflow in .rdata slack space"

    # 4. Embed Destroyer description in .text slack
    desc_d_raw = 0x65b170
    desc_d_va = 0xa5bd70
    s_desc_d = "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.\x00".encode("windows-1252")
    data[desc_d_raw : desc_d_raw + len(s_desc_d)] = s_desc_d
    assert desc_d_raw + len(s_desc_d) <= 0x65b200, "Overflow in .text slack space"

    # 5. Assemble Hook code in .text slack at 0x65b0c0 (VA 0xa5bcc0)
    hook_raw = 0x65b0c0
    hook_va = 0xa5bcc0

    code = bytearray()
    # Function 1: hook_class_name
    code += b"\xff\x74\x24\x08" # push dword ptr [esp + 8] (arg2)
    code += b"\xff\x74\x24\x08" # push dword ptr [esp + 8] (arg1)
    rel_cbd50 = 0x5cbd50 - (hook_va + len(code) + 5)
    code += b"\xe8" + struct.pack("<i", rel_cbd50) # call 0x5cbd50
    code += b"\x83\xc4\x08"     # add esp, 8

    # Destroyer
    code += b"\x80\x38\x44"     # cmp byte ptr [eax], 'D'
    code += b"\x75\x1d"         # jne check_alch (+29)
    code += b"\xc7\x00\x44\x65\x73\x74"             # mov dword ptr [eax], 'Dest'
    code += b"\xc7\x40\x04\x72\x75\x69\x64"         # mov dword ptr [eax+4], 'ruid'
    code += b"\x66\xc7\x40\x08\x72\x00"             # mov word ptr [eax+8], 'or\0'
    code += b"\xc7\x40\x10\x0a\x00\x00\x00"         # mov dword ptr [eax+16], 10
    code += b"\xc3"             # ret

    # Alchemist
    code += b"\x80\x38\x41"     # cmp byte ptr [eax], 'A'
    code += b"\x75\x1d"         # jne check_vanq (+29)
    code += b"\xc7\x00\x41\x6c\x71\x75"             # mov dword ptr [eax], 'Alqu'
    code += b"\xc7\x40\x04\x69\x6d\x69\x73"         # mov dword ptr [eax+4], 'imis'
    code += b"\x66\xc7\x40\x08\x61\x00"             # mov word ptr [eax+8], 'ta\0'
    code += b"\xc7\x40\x10\x0a\x00\x00\x00"         # mov dword ptr [eax+16], 10
    code += b"\xc3"             # ret

    # Vanquisher
    code += b"\x80\x38\x56"     # cmp byte ptr [eax], 'V'
    code += b"\x75\x25"         # jne done (+37)
    code += b"\xc7\x00\x43\x6f\x6e\x71"             # mov dword ptr [eax], 'Conq'
    code += b"\xc7\x40\x04\x75\x69\x73\x74"         # mov dword ptr [eax+4], 'uist'
    code += b"\xc7\x40\x08\x61\x64\x6f\x72"         # mov dword ptr [eax+8], 'ador'
    code += b"\x66\xc7\x40\x0c\x61\x00"             # mov word ptr [eax+12], 'a\0'
    code += b"\xc7\x40\x10\x0d\x00\x00\x00"         # mov dword ptr [eax+16], 13
    code += b"\xc3"             # ret

    # done
    code += b"\xc3"

    fn1_size = len(code)
    fn2_va = hook_va + fn1_size
    assert fn2_va == 0xa5bd38

    # Function 2: hook_class_desc
    code += b"\xff\x15\x90\xc3\xa5\x00" # call dword ptr [0xa5c390]
    code += b"\x80\x38\x54"             # cmp byte ptr [eax], 'T'
    code += b"\x75\x2a"                 # jne done_desc (+42)
    code += b"\x80\x78\x04\x44"         # cmp byte ptr [eax+4], 'D'
    code += b"\x75\x08"                 # jne check_alch_d (+8)
    code += b"\xb8" + struct.pack("<I", desc_d_va) # mov eax, desc_d_va
    code += b"\xc3"                     # ret

    code += b"\x80\x78\x04\x41"         # cmp byte ptr [eax+4], 'A'
    code += b"\x75\x08"                 # jne check_vanq_d (+8)
    code += b"\xb8" + struct.pack("<I", desc_a_va) # mov eax, desc_a_va
    code += b"\xc3"                     # ret

    code += b"\x80\x78\x04\x56"         # cmp byte ptr [eax+4], 'V'
    code += b"\x75\x08"                 # jne done_desc (+8)
    code += b"\xb8" + struct.pack("<I", desc_v_va) # mov eax, desc_v_va
    code += b"\xc3"                     # ret

    code += b"\xc3"                     # ret

    assert hook_raw + len(code) <= desc_d_raw, "Hook code collides with desc_d"
    data[hook_raw : hook_raw + len(code)] = code

    # 6. Patch call sites in CharacterCreate::update
    site1_raw = 0x1b6155
    rel1 = hook_va - (0x5b6d55 + 5)
    data[site1_raw : site1_raw + 5] = b"\xe8" + struct.pack("<i", rel1)

    site2_raw = 0x1b61a9
    rel2 = hook_va - (0x5b6da9 + 5)
    data[site2_raw : site2_raw + 5] = b"\xe8" + struct.pack("<i", rel2)

    site3_raw = 0x1b6242
    rel3 = fn2_va - (0x5b6e42 + 5)
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
