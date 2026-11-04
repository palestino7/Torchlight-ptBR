#!/usr/bin/env python3
"""
tools/patch_torchlight_exe.py - Torchlight Executable Localizer

Patches Torchlight.exe to localize the hardcoded settings dropdown options:
- Shadows: "Off", "Lighting Only", "Low", "Medium", "High", "Very High"
  -> "Desligado", "Apenas Iluminação", "Baixo", "Médio", "Alto", "Muito Alto"
- Particles: "Low", "Medium", "High"
  -> "Baixo", "Médio", "Alto"

Works by:
1. Writing the UTF-8 Portuguese strings into .rdata slack space at file offset 0x7e6912 (VA 0xbe7712).
2. Updating the 32-bit push pointer opcodes in the static initializer functions.
3. Automatically backing up the original binary to Torchlight.exe.orig.
"""

import argparse
import os
import shutil
import struct

# New strings mapped to VA addresses in .rdata slack (base raw: 0x7e6912, VA: 0xbe7712)
# Encoded in Windows-1252 / ISO-8859-1 (CEGUI String(const char*) zero-extends bytes to utf32)
SLACK_RAW_START = 0x7e6912
SLACK_VA_START = 0xbe7712

STRINGS_TO_EMBED = [
    ("Desligado", b"Desligado\x00"),                              # len 10
    ("Apenas Iluminação", b"Apenas Ilumina\xe7\xe3o\x00"),        # len 18
    ("Baixo", b"Baixo\x00"),                                      # len 6
    ("Médio", b"M\xe9dio\x00"),                                   # len 6
    ("Alto", b"Alto\x00"),                                        # len 5
    ("Muito Alto", b"Muito Alto\x00"),                            # len 11
]

# Calculate VAs for each string
EMBEDDED_VAS = {}
curr_raw = SLACK_RAW_START
curr_va = SLACK_VA_START
for name, data in STRINGS_TO_EMBED:
    EMBEDDED_VAS[name] = curr_va
    curr_raw += len(data)
    curr_va += len(data)

# Push offsets to update in Torchlight.exe (Build 17685)
# Map (raw_offset, original_bytes, new_va)
PATCH_TABLE = [
    # SettingsMenu::static_init (0x9a1850)
    (0x5a0c55, 0xa89a94, EMBEDDED_VAS["Desligado"]),          # push "Off"
    (0x5a0c65, 0xa89a84, EMBEDDED_VAS["Apenas Iluminação"]),  # push "Lighting Only"
    (0x5a0c7d, 0xa89a80, EMBEDDED_VAS["Baixo"]),              # push "Low"
    (0x5a0c92, 0xa89a78, EMBEDDED_VAS["Médio"]),              # push "Medium"
    (0x5a0ca7, 0xa89a70, EMBEDDED_VAS["Alto"]),               # push "High"
    (0x5a0cbc, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),         # push "Very High"
    (0x5a0d05, 0xa89a80, EMBEDDED_VAS["Baixo"]),              # push "Low" (particles)
    (0x5a0d15, 0xa89a78, EMBEDDED_VAS["Médio"]),              # push "Medium" (particles)
    (0x5a0d2d, 0xa89a70, EMBEDDED_VAS["Alto"]),               # push "High" (particles)

    # TU1 static_init (0x9574b0)
    (0x5568b5, 0xa89a94, EMBEDDED_VAS["Desligado"]),
    (0x5568c5, 0xa89a84, EMBEDDED_VAS["Apenas Iluminação"]),
    (0x5568dd, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x5568f2, 0xa89a78, EMBEDDED_VAS["Médio"]),
    (0x556907, 0xa89a70, EMBEDDED_VAS["Alto"]),
    (0x55691c, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),
    (0x556965, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x556975, 0xa89a78, EMBEDDED_VAS["Médio"]),
    (0x55698d, 0xa89a70, EMBEDDED_VAS["Alto"]),

    # TU3 static_init (0xa27f20)
    (0x627325, 0xa89a94, EMBEDDED_VAS["Desligado"]),
    (0x627335, 0xa89a84, EMBEDDED_VAS["Apenas Iluminação"]),
    (0x62734d, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x627362, 0xa89a78, EMBEDDED_VAS["Médio"]),
    (0x627377, 0xa89a70, EMBEDDED_VAS["Alto"]),
    (0x62738c, 0xa89a64, EMBEDDED_VAS["Muito Alto"]),
    (0x6273e5, 0xa89a80, EMBEDDED_VAS["Baixo"]),
    (0x6273f5, 0xa89a78, EMBEDDED_VAS["Médio"]),
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

    # 1. Write localized strings into slack space
    curr_offset = SLACK_RAW_START
    for name, sbytes in STRINGS_TO_EMBED:
        data[curr_offset : curr_offset + len(sbytes)] = sbytes
        curr_offset += len(sbytes)

    # 2. Patch push opcodes (0x68 followed by 4-byte VA)
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

    with open(exe_path, "wb") as f:
        f.write(data)

    print(f"[Success] Patched {patched_count}/{len(PATCH_TABLE)} instructions in {exe_path}")
    print(f"          - Embedded strings written to {hex(SLACK_RAW_START)} ({len(STRINGS_TO_EMBED)} strings, {curr_offset - SLACK_RAW_START} bytes)")
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
    parser = argparse.ArgumentParser(description="Patch Torchlight.exe to localize options dropdowns")
    parser.add_argument("--exe", default=default_exe, help=f"Path to Torchlight.exe (default: {default_exe})")
    parser.add_argument("--revert", action="store_true", help="Revert to Torchlight.exe.orig")
    args = parser.parse_args()

    if args.revert:
        revert_executable(args.exe)
    else:
        patch_executable(args.exe)


if __name__ == "__main__":
    main()
