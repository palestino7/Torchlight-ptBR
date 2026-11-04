#!/usr/bin/env python3
"""
tools/sync_appdata_mod.py - Completely syncs translation_ptbr with %APPDATA%/runic games/torchlight/mods/Traducao_ptBR
"""

import os
import shutil

def sync_mod():
    src_media = "translation_ptbr/media"
    src_trans = "translation_ptbr/translations"

    dest_mod = os.path.expandvars(r"%APPDATA%\runic games\torchlight\mods\Traducao_ptBR")
    dest_media = os.path.join(dest_mod, "media")
    dest_trans = os.path.join(dest_mod, "translations")

    os.makedirs(dest_media, exist_ok=True)
    os.makedirs(dest_trans, exist_ok=True)

    # 1. Copy all media recursively
    for root, dirs, files in os.walk(src_media):
        rel = os.path.relpath(root, src_media)
        target_dir = os.path.join(dest_media, rel)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            src_f = os.path.join(root, f)
            dest_f = os.path.join(target_dir, f)
            shutil.copy2(src_f, dest_f)

    print(f"[Sync] Copied media assets to {dest_media}")

    # 2. Copy translations/translation.dat
    shutil.copy2("translation_ptbr/translations/translation.dat", os.path.join(dest_trans, "translation.dat"))
    print(f"[Sync] Copied translation.dat to {dest_trans}")

    # 3. Remove obsolete TRANSLATION.DAT.adm so the game regenerates/reads translation.dat
    adm_path = os.path.join(dest_trans, "TRANSLATION.DAT.adm")
    if os.path.exists(adm_path):
        os.remove(adm_path)
        print(f"[Sync] Removed stale binary cache: {adm_path}")

    # 4. Verify critical files
    crit_files = [
        os.path.join(dest_media, "UI", "Torchlight Regular.ttf"),
        os.path.join(dest_media, "UI", "charactercreate.layout"),
        os.path.join(dest_media, "UI", "tipmenu.layout"),
        os.path.join(dest_media, "UI", "questdialogmenu.layout"),
        os.path.join(dest_media, "masterresourceunits.dat.ADM"),
        os.path.join(dest_trans, "translation.dat"),
    ]
    for cf in crit_files:
        assert os.path.exists(cf), f"Missing critical file in mod: {cf}"
        print(f"  [OK] {cf} ({os.path.getsize(cf):,} bytes)")

    print("[Sync] SUCCESS: AppData Traducao_ptBR mod is 100% updated!")

if __name__ == "__main__":
    sync_mod()
