#!/usr/bin/env python3
"""
tools/patch_torchlight_exe.py - Torchlight Executable Localizer

Patches Torchlight.exe to localize hardcoded strings:
- Shadows options: "Off", "Lighting Only", "Low", "Medium", "High", "Very High"
  -> "Desligado", "Apenas Iluminação", "Baixo", "Médio", "Alto", "Muito Alto"
- Particles: "Low", "Medium", "High"
  -> "Baixo", "Médio", "Alto"
- TipMenu Title: "Tip" -> "Dica" (UTF-16LE)
- Character Creation screen (CharacterCreate::update @ 0x5b6d10):
  - Class Titles: "Destroyer", "Alchemist", "Vanquisher"
    -> "Destruidor", "Alquimista", "Conquistadora"
  - Class Descriptions -> Portuguese (Windows-1252)

IMPORTANT (ASLR): Torchlight.exe is linked with DYNAMIC_BASE, so the loader
rebases the image at every launch. The original `push imm32` operands patched
below are covered by the relocation table, but injected code placed in slack
space is NOT. Therefore every injected hook is POSITION INDEPENDENT: it gets
EIP via `call $+5 / pop edx` and reaches the c_str() IAT slot and the strings
through offsets relative to itself (the image is rebased as a whole, so such
offsets never change). Earlier revisions used absolute addresses and crashed
with an access violation the moment the character creation screen opened.

The internal unit names ("Destroyer", ...) are never touched, so GetUnit()
keeps working and saves stay compatible.
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
    ("Dica", "Dica\x00".encode("utf-16le")),                     # len 10 (UTF-16LE for TipMenu title)
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

    # Journal/Diary screen (0x5819b5) - "Difficulty:" -> "Dificuldade:"
    (0x180db5, 0xa8ec20, 0xa8092c),

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

# ---------------------------------------------------------------------------
# Character Creation localization
#
# Three engine/loader facts this patch has to respect (each one crashed an
# earlier revision):
#   1. ASLR: the image is rebased on every launch. Injected code lives in slack
#      space WITHOUT relocation entries, so it must be position independent
#      (no absolute addresses at all).
#   2. The loader adds the rebase delta to EVERY 4-byte word listed in the
#      relocation table. Patched bytes must never overlap one of those words
#      (e.g. the operand of `call dword ptr [c_str]` at 0x5b6dc0..0x5b6dc3, or the
#      operand of the last thunk at 0xa5bca7..0xa5bcaa). So the original
#      `call [c_str]` is left untouched and the hook is entered only AFTER it,
#      working on the `const char*` already returned in EAX.
#   3. The true end of .text code is 0xa5bcab (not 0xa5bcaa).
#
# Hook flow (CharacterCreate::update, thiscall string -> CEGUI::String):
#       call [c_str]            ; original, untouched          -> EAX = const char*
#       call hook               ; replaces `push eax; lea ecx,[esp+N]`
#       call [CEGUI::String::String(const char*)]   ; original, untouched
#   hook:  pop edx              ; edx = return address (PIC anchor)
#          ...map EAX to the translated string using `lea eax,[edx+disp]`...
#          push eax / lea ecx,[esp+N]   ; the instructions the call replaced
#          jmp edx              ; resume exactly where the original code continues
# ---------------------------------------------------------------------------
HOOK_RAW = 0x65b0b0          # .text slack (file offset) - zero padding in the original
HOOK_VA = 0xa5bcb0           # same location as preferred VA (image base 0x400000)
HOOK_LIMIT_RAW = 0x65b200    # end of .text raw data
DESC_HOOK_OFF = 0x50         # second hook starts here (first one is < 0x50 bytes)
STR_OFF = 0xA0               # strings start here

# .rdata slack for the two long descriptions that do not fit in the .text slack
RDATA_DESC_RAW = 0x7e6954
RDATA_DESC_VA = 0xbe7754
RDATA_LIMIT_RAW = 0x7e6a00

# Replaced instruction sequences inside CharacterCreate::update:
#   (file offset, VA, original bytes, tail re-executed by the hook, padding nops)
SITE_NAME = (0x1b61c4, 0x5b6dc4, bytes.fromhex("508d4c2468"),
             bytes.fromhex("508d4c2468"))                  # push eax; lea ecx,[esp+0x68]
SITE_DESC = (0x1b6248, 0x5b6e48, bytes.fromhex("508d8c2400010000"),
             bytes.fromhex("508d8c2400010000"))            # push eax; lea ecx,[esp+0x100]

# Older (broken) revisions modified other places. Everything is restored/cleared
# so that an executable patched by an old version is healed by re-running.
ORIG_CSTR_CALL = bytes.fromhex("ff1590c3a50050")  # call dword ptr [0xa5c390]; push eax
STRING_CTOR_CALL = bytes.fromhex("ff1544c0a500")  # call dword ptr [0xa5c044] (CEGUI::String ctor) - anchor
LEGACY_RESTORE = [
    (0x1b6155, bytes.fromhex("e8f64f0100")),   # 0x5b6d55 call 0x5cbd50
    (0x1b61a9, bytes.fromhex("e8a24f0100")),   # 0x5b6da9 call 0x5cbd50
    (0x1b61be, ORIG_CSTR_CALL),                # 0x5b6dbe call [c_str]; push eax
    (0x1b6242, ORIG_CSTR_CALL),                # 0x5b6e42 call [c_str]; push eax
]
LEGACY_ZERO = [
    (0x65b0aa, 0x65b200),      # old hooks/strings in .text slack (0x65b0aa restores a thunk byte = 0)
    (0x7e6954, 0x7e6a00),      # old descriptions in .rdata slack
    (0x7e6a10, 0x7e6b60),      # old strings written into .data (zero in the original)
]

CLASS_NAMES = [b"Destruidor\x00", b"Alquimista\x00", b"Conquistadora\x00"]
DESC_D = "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.\x00".encode("windows-1252")
DESC_A = "O Alquimista canaliza o poder do \xc2mbar para atacar de longe e invocar lacaios.\x00".encode("windows-1252")
DESC_V = "A Conquistadora \xe9 uma atiradora perita e usa armadilhas para debilitar seus inimigos.\x00".encode("windows-1252")


def _build_hook(ret_va, prologue, entries, tail):
    """Assemble one position independent hook.

    ret_va:   VA the hook returns to (= call site + 5). Used as PIC anchor: after
              `pop edx`, EDX == ret_va at run time (whatever the load address).
    prologue: None or (0, char). If it does not match, EAX is passed through.
    entries:  list of (char_offset, char, target_va) mapping EAX -> target string
    tail:     original instructions re-executed by the hook (push eax; lea ...)
    """
    c = bytearray()
    c += b"\x5a"                                    # pop edx            ; edx = return address
    jumps = []                                      # (position of rel8, kind, index)
    if prologue:
        _off, ch = prologue
        c += b"\x80\x38" + bytes([ch])              # cmp byte ptr [eax], ch
        jumps.append((len(c) + 1, "done", None))
        c += b"\x75\x00"                            # jne done
    for i, (off, ch, _tgt) in enumerate(entries):
        if off == 0:
            c += b"\x80\x38" + bytes([ch])          # cmp byte ptr [eax], ch
        else:
            c += b"\x80\x78" + bytes([off, ch])     # cmp byte ptr [eax+off], ch
        jumps.append((len(c) + 1, "entry", i))
        c += b"\x74\x00"                            # je entry_i
    done_off = len(c)
    c += tail                                       # done: push eax; lea ecx,[esp+N]
    c += b"\xff\xe2"                                # jmp edx

    entry_off = []
    for _off, _ch, tgt in entries:
        entry_off.append(len(c))
        c += b"\x8d\x82" + struct.pack("<i", tgt - ret_va)   # lea eax, [edx + (tgt - ret_va)]
        rel = done_off - (len(c) + 2)
        assert -128 <= rel < 0
        c += b"\xeb" + struct.pack("<b", rel)                # jmp done

    for pos, kind, idx in jumps:
        target = done_off if kind == "done" else entry_off[idx]
        rel = target - (pos + 1)
        assert 0 <= rel < 0x80, rel
        c[pos] = rel
    return bytes(c)


def build_class_patch():
    """Return the list of (file_offset, bytes) writes of the class patch."""
    name_hook_va = HOOK_VA
    desc_hook_va = HOOK_VA + DESC_HOOK_OFF
    str_raw = HOOK_RAW + STR_OFF
    str_va = HOOK_VA + STR_OFF

    va_names, off = [], 0
    for n in CLASS_NAMES:
        va_names.append(str_va + off)
        off += len(n)
    va_desc_d = str_va + off
    blob = b"".join(CLASS_NAMES) + DESC_D
    assert str_raw + len(blob) <= HOOK_LIMIT_RAW, "Overflow in .text slack space"
    assert RDATA_DESC_RAW + len(DESC_A) + len(DESC_V) <= RDATA_LIMIT_RAW, "Overflow in .rdata slack space"
    va_desc_a = RDATA_DESC_VA
    va_desc_v = RDATA_DESC_VA + len(DESC_A)

    name_raw, name_va, name_orig, name_tail = SITE_NAME
    desc_raw, desc_va, desc_orig, desc_tail = SITE_DESC
    name_code = _build_hook(name_va + 5, None, [
        (0, ord("D"), va_names[0]), (0, ord("A"), va_names[1]), (0, ord("V"), va_names[2]),
    ], name_tail)
    desc_code = _build_hook(desc_va + 5, (0, ord("T")), [
        (4, ord("D"), va_desc_d), (4, ord("A"), va_desc_a), (4, ord("V"), va_desc_v),
    ], desc_tail)
    assert len(name_code) <= DESC_HOOK_OFF, len(name_code)
    assert DESC_HOOK_OFF + len(desc_code) <= STR_OFF, len(desc_code)

    writes = [
        (HOOK_RAW, name_code),
        (HOOK_RAW + DESC_HOOK_OFF, desc_code),
        (str_raw, blob),
        (RDATA_DESC_RAW, DESC_A + DESC_V),
    ]
    for (raw, va, orig, _tail), hook_va in ((SITE_NAME, name_hook_va), (SITE_DESC, desc_hook_va)):
        patch = b"\xe8" + struct.pack("<i", hook_va - (va + 5))
        patch += b"\x90" * (len(orig) - len(patch))      # pad (nops) to the replaced length
        writes.append((raw, patch))
    return writes


def apply_class_patch(data: bytearray) -> bool:
    """Apply (or re-apply) the character creation patch on `data` in place."""
    # Anchor check: right after each replaced sequence the original code calls
    # CEGUI::String::String(const char*) - bytes no revision ever touched.
    for raw, _va, orig, _tail in (SITE_NAME, SITE_DESC):
        a = raw + len(orig)
        if bytes(data[a:a + len(STRING_CTOR_CALL)]) != STRING_CTOR_CALL:
            print(f"[Warning] Unexpected code near {hex(raw)}: character creation patch skipped")
            return False
    for raw, original in LEGACY_RESTORE:
        data[raw:raw + len(original)] = original
    for a, b in LEGACY_ZERO:
        data[a:b] = b"\x00" * (b - a)
    for raw, blob in build_class_patch():
        data[raw:raw + len(blob)] = blob
    return True


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

    # 2. Patch push opcodes (relocated by the loader, so ASLR-safe)
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

    # 3. Character Creation class names / descriptions (position independent hooks)
    class_ok = apply_class_patch(data)

    # 4. Embed L"Dificuldade:" in .rdata slack space at raw 0x67fb2c (VA 0xa8092c, 26 bytes)
    u16_dificuldade_colon = "Dificuldade:\x00".encode("utf-16le")
    if len(data) > 0x67FB2C + len(u16_dificuldade_colon):
        data[0x67FB2C : 0x67FB2C + len(u16_dificuldade_colon)] = u16_dificuldade_colon

    # 5. In-place string patches
    gold_count = 0
    # Raw 0x67bd84 (ASCII, 6 bytes): b" Gold\0" -> b" Ouro\0"
    if len(data) > 0x67BD84 + 6 and (data[0x67BD84 : 0x67BD84 + 6] == b" Gold\x00" or data[0x67BD84 : 0x67BD84 + 6] == b" Ouro\x00"):
        data[0x67BD84 : 0x67BD84 + 6] = b" Ouro\x00"
        gold_count += 1
    # Raw 0x67e854 (UTF-16LE, 12 bytes): L" Gold\0" -> L" Ouro\0"
    u16_gold = " Gold\x00".encode("utf-16le")
    u16_ouro = " Ouro\x00".encode("utf-16le")
    if len(data) > 0x67E854 + 12 and (data[0x67E854 : 0x67E854 + 12] == u16_gold or data[0x67E854 : 0x67E854 + 12] == u16_ouro):
        data[0x67E854 : 0x67E854 + 12] = u16_ouro
        gold_count += 1

    # Raw 0x668698 (UTF-16LE, 14 bytes): L"Floor \0" -> L"Andar \0" (Scenario entry overlay: e.g. "Minas de Orden" / "Andar 1")
    u16_floor = "Floor \x00".encode("utf-16le")
    u16_andar = "Andar \x00".encode("utf-16le")
    if len(data) > 0x668698 + 14 and (data[0x668698 : 0x668698 + 14] == u16_floor or data[0x668698 : 0x668698 + 14] == u16_andar):
        data[0x668698 : 0x668698 + 14] = u16_andar

    # Raw 0x6801f0 (UTF-16LE, 20 bytes): L" - Floor \0" -> L" - Andar \0"
    u16_dash_floor = " - Floor \x00".encode("utf-16le")
    u16_dash_andar = " - Andar \x00".encode("utf-16le")
    if len(data) > 0x6801F0 + 20 and (data[0x6801F0 : 0x6801F0 + 20] == u16_dash_floor or data[0x6801F0 : 0x6801F0 + 20] == u16_dash_andar):
        data[0x6801F0 : 0x6801F0 + 20] = u16_dash_andar

    # Raw 0x68ddc8 (UTF-16LE, 24 bytes): L"Ancestors:\0\0" -> L"Ancestrais:\0" (Journal/Diary screen)
    u16_ancestors = "Ancestors:\x00\x00".encode("utf-16le")
    u16_ancestrais = "Ancestrais:\x00".encode("utf-16le")
    if len(data) > 0x68DDC8 + 24 and (data[0x68DDC8 : 0x68DDC8 + 22] == "Ancestors:\x00".encode("utf-16le") or data[0x68DDC8 : 0x68DDC8 + 24] == u16_ancestrais):
        data[0x68DDC8 : 0x68DDC8 + 24] = u16_ancestrais

    # Raw 0x68ef2c (UTF-16LE, 24 bytes): L"Difficulty\0\0" -> L"Dificuldade\0"
    u16_difficulty = "Difficulty\x00\x00".encode("utf-16le")
    u16_dificuldade = "Dificuldade\x00".encode("utf-16le")
    if len(data) > 0x68EF2C + 24 and (data[0x68EF2C : 0x68EF2C + 22] == "Difficulty\x00".encode("utf-16le") or data[0x68EF2C : 0x68EF2C + 24] == u16_dificuldade):
        data[0x68EF2C : 0x68EF2C + 24] = u16_dificuldade

    with open(exe_path, "wb") as f:
        f.write(data)

    print(f"[Success] Patched {patched_count}/{len(PATCH_TABLE)} option instructions in {exe_path}")
    print(f"          - Character creation localizer: {'applied' if class_ok else 'SKIPPED'}")
    print(f"          - Floating combat text ' Gold' -> ' Ouro': {gold_count}/2 applied")
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


def emit_c_header(path: str) -> None:
    """Generate tools/patch_class_data.h consumed by patch_torchlight.c."""
    def arr(blob):
        return ", ".join(f"0x{b:02x}" for b in blob)

    def table(name, entries, prefix):
        out = []
        rows = []
        for i, (raw, blob) in enumerate(entries):
            out.append(f"static const unsigned char {prefix}_{i}[] = {{ {arr(blob)} }};")
            rows.append(f"    {{ 0x{raw:x}, {len(blob)}, {prefix}_{i} }},")
        out.append(f"static const ClassWrite {name}[] = {{")
        out += rows
        out.append("};")
        return out

    lines = [
        "/* AUTO-GENERATED by tools/patch_torchlight_exe.py --emit-c. DO NOT EDIT. */",
        "typedef struct { unsigned int raw; unsigned int len; const unsigned char* bytes; } ClassWrite;",
    ]
    lines += table("class_writes", build_class_patch(), "class_blob")
    lines += table("class_restore", LEGACY_RESTORE, "restore_blob")
    lines.append("static const unsigned int class_anchor_raw[] = { 0x%x, 0x%x };" % (
        SITE_NAME[0] + len(SITE_NAME[2]), SITE_DESC[0] + len(SITE_DESC[2])))
    lines.append("static const unsigned char class_anchor_bytes[%d] = { %s };" % (len(STRING_CTOR_CALL), arr(STRING_CTOR_CALL)))
    lines.append("static const unsigned int class_zero[][2] = {")
    for a, b in LEGACY_ZERO:
        lines.append("    { 0x%x, 0x%x }," % (a, b))
    lines.append("};")
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[Emit] Wrote {path}")


def main():
    default_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Torchlight.exe"
    parser = argparse.ArgumentParser(description="Patch Torchlight.exe to localize options dropdowns and UI strings")
    parser.add_argument("--exe", default=default_exe, help=f"Path to Torchlight.exe (default: {default_exe})")
    parser.add_argument("--revert", action="store_true", help="Revert to Torchlight.exe.orig")
    parser.add_argument("--emit-c", metavar="HEADER", help="Write the C header used by tools/patch_torchlight.c and exit")
    args = parser.parse_args()

    if args.emit_c:
        emit_c_header(args.emit_c)
    elif args.revert:
        revert_executable(args.exe)
    else:
        patch_executable(args.exe)


if __name__ == "__main__":
    main()
