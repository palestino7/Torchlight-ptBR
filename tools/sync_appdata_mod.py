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

    # 3. Remove obsolete caches so the game regenerates/reads cleanly from translation.dat and Pak.zip
    appdata_root = os.path.expandvars(r"%APPDATA%\runic games\torchlight")
    stale_caches = [
        os.path.join(dest_trans, "TRANSLATION.DAT.adm"),
        os.path.join(appdata_root, "masterresourceunits.dat"),
        os.path.join(appdata_root, "masterresourceunits.dat.ADM"),
        os.path.join(appdata_root, "massfile.dat"),
        os.path.join(appdata_root, "massfile.dat.ADM"),
    ]
    for sc in stale_caches:
        if os.path.exists(sc):
            try:
                os.remove(sc)
                print(f"[Sync] Removed stale binary cache: {sc}")
            except Exception as e:
                print(f"[Sync] Warning: could not remove {sc}: {e}")

    # Remove any leftover media/units in mod folder
    mod_units = os.path.join(dest_media, "units")
    if os.path.exists(mod_units):
        shutil.rmtree(mod_units, ignore_errors=True)
        print(f"[Sync] Removed obsolete units override: {mod_units}")

    # 4. Verify critical files
    crit_files = [
        os.path.join(dest_media, "UI", "Torchlight Regular.ttf"),
        os.path.join(dest_media, "UI", "charactercreate.layout"),
        os.path.join(dest_media, "UI", "tipmenu.layout"),
        os.path.join(dest_media, "UI", "questdialogmenu.layout"),
        os.path.join(dest_trans, "translation.dat"),
    ]
    for cf in crit_files:
        assert os.path.exists(cf), f"Missing critical file in mod: {cf}"
        print(f"  [OK] {cf} ({os.path.getsize(cf):,} bytes)")

    print("[Sync] SUCCESS: AppData Traducao_ptBR mod is 100% updated!")

if __name__ == "__main__":
    sync_mod()
