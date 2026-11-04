#!/usr/bin/env python3
"""
tools/patch_layouts_and_ui.py - Updates layout XML files with UI/viewbox fixes.

Fixes:
1. charactercreate.layout:
   - Sets default class name to "Destruidor"
   - Sets default description to "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos."
   - Expands CharacterClassDescription width to 500px so it wraps cleanly
   - Expands Name ("Nome do Personagem") width from 140px to 260px and centers it, preventing text clipping
   - Expands PetName ("Nome do Mascote") width from 140px to 200px and centers it
2. tipmenu.layout:
   - Sets modal Title to "Dica"
   - Adjusts Dialog position and width to 450px with 25px margins, preventing text from clipping against the ornamental border
3. questdialogmenu.layout:
   - Ensures reward stats labels have trailing spaces before numbers: "PO: 0", "XP: 0", "Fama: 0"
"""

import os
import shutil
import re

def patch_charactercreate(layout_path: str):
    with open(layout_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix CharacterClass block
    class_pattern = r'(<Window Type="GuiLook/StaticTextOutline" Name="CharacterClass"\s*>)([\s\S]*?)(</Window>)'
    def replace_class(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
         \t\t   <Property Name="UnifiedPosition" Value="{{.5,-300},{1,-175}}" />
         \t\t   <Property Name="UnifiedSize" Value="{{0,600},{0,60}}" />
\t\t\t<Property Name="Text" Value="Destruidor" />
\t\t\t<Property Name="Font" Value="SerifHuge" /> 
\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />
\t\t\t<Property Name="AlwaysOnTop" Value="True" />
\t\t    <Property Name="HorzTextFormatting" Value="CentreAligned" />
\t\t  """
        return f"{prefix}{body}{suffix}"

    content = re.sub(class_pattern, replace_class, content)

    # 2. Fix CharacterClassDescription block
    desc_pattern = r'(<Window Type="GuiLook/StaticText" Name="CharacterClassDescription"\s*>)([\s\S]*?)(</Window>)'
    def replace_desc(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
         \t\t   <Property Name="UnifiedPosition" Value="{{.5,-250},{1,-140}}" />
         \t\t   <Property Name="UnifiedSize" Value="{{0,500},{0,64}}" />
\t\t\t<Property Name="Font" Value="SerifSmall" /> 
\t\t\t<Property Name="Text" Value="O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos." />
\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />
\t\t\t<Property Name="AlwaysOnTop" Value="True" />
\t          <Property Name="HorzTextFormatting" Value="WordWrapCentreAligned" />
\t\t  """
        return f"{prefix}{body}{suffix}"

    content = re.sub(desc_pattern, replace_desc, content)

    # 3. Fix Name window ("Nome do Personagem")
    name_pattern = r'(<Window Type="GuiLook/StaticText" Name="Name"\s*>)([\s\S]*?)(</Window>)'
    def replace_name(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
            <Property Name="Text" Value="Nome do Personagem" />
            <Property Name="UnifiedPosition" Value="{{.5,-130},{1,-88}}" />
            <Property Name="UnifiedSize" Value="{{0,260},{0,24}}" />
            <Property Name="HorzTextFormatting" Value="CentreAligned" />
        <Property Name="MousePassThroughEnabled" Value="True" />
        """
        return f"{prefix}{body}{suffix}"

    content = re.sub(name_pattern, replace_name, content)

    # 4. Fix PetName window ("Nome do Mascote")
    pet_pattern = r'(<Window Type="GuiLook/StaticText" Name="PetName"\s*>)([\s\S]*?)(</Window>)'
    def replace_pet(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
            <Property Name="Text" Value="Nome do Mascote" />
            <Property Name="UnifiedPosition" Value="{{0,-30},{0,140}}" />
            <Property Name="UnifiedSize" Value="{{0,200},{0,24}}" />
            <Property Name="HorzTextFormatting" Value="CentreAligned" />
        <Property Name="MousePassThroughEnabled" Value="True" />
        """
        return f"{prefix}{body}{suffix}"

    content = re.sub(pet_pattern, replace_pet, content)

    with open(layout_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[LayoutPatch] Patched {layout_path}")


def patch_tipmenu(layout_path: str):
    with open(layout_path, "rb") as f:
        raw = f.read()

    is_utf16 = raw.startswith(b"\xff\xfe")
    text = raw[2:].decode("utf-16le") if is_utf16 else raw.decode("utf-8")

    # Add Text="Dica" to Title if not already there
    title_pattern = r'(<Window Type="GuiLook/StaticText" Name="Title"\s*>)([\s\S]*?)(</Window>)'
    def replace_title(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
        <Property Name="HorzTextFormatting" Value="CentreAligned" />
        <Property Name="VertFormatting" Value="CentreAligned" />
        <Property Name="UnifiedSize" Value="{{0,142},{0,28}}" />
\t\t<Property Name="TextColour" Value="FFFFFFFF"/>
\t\t<Property Name="Font" Value="SerifBig"/>
        <Property Name="Text" Value="Dica" />
        """
        return f"{prefix}{body}{suffix}"

    text = re.sub(title_pattern, replace_title, text)

    # Adjust Dialog position and size
    dialog_pattern = r'(<Window Type="GuiLook/StaticText" Name="Dialog"\s*>)([\s\S]*?)(</Window>)'
    def replace_dialog(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
\t\t    <Property Name="Font" Value="SerifBig" />
\t\t    <Property Name="HorzTextFormatting" Value="WordWrapCentreAligned" />
\t\t    <Property Name="VertFormatting" Value="TopAligned" />
\t\t    <Property Name="UnifiedPosition" Value="{{0,25},{0,25}}" />
\t\t    <Property Name="UnifiedSize" Value="{{0,450},{0,260}}" />
\t\t\t<Property Name="TextColour" Value="FFFFFFFF"/>
\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />
\t\t"""
        return f"{prefix}{body}{suffix}"

    text = re.sub(dialog_pattern, replace_dialog, text)

    encoded = (b"\xff\xfe" + text.encode("utf-16le")) if is_utf16 else text.encode("utf-8")
    with open(layout_path, "wb") as f:
        f.write(encoded)
    print(f"[LayoutPatch] Patched {layout_path}")


def patch_questdialog(layout_path: str):
    with open(layout_path, "rb") as f:
        raw = f.read()

    is_utf16 = raw.startswith(b"\xff\xfe")
    text = raw[2:].decode("utf-16le") if is_utf16 else raw.decode("utf-8")

    # Ensure spaces after colons
    text = text.replace('Value="PO:0"', 'Value="PO: 0"')
    text = text.replace('Value="XP:0"', 'Value="XP: 0"')
    text = text.replace('Value="Fame:0"', 'Value="Fama: 0"')
    text = text.replace('Value="Fama:0"', 'Value="Fama: 0"')

    encoded = (b"\xff\xfe" + text.encode("utf-16le")) if is_utf16 else text.encode("utf-8")
    with open(layout_path, "wb") as f:
        f.write(encoded)
    print(f"[LayoutPatch] Patched {layout_path}")


def main():
    cc_path = "translation_ptbr/media/UI/charactercreate.layout"
    tip_path = "translation_ptbr/media/UI/tipmenu.layout"
    qd_path = "translation_ptbr/media/UI/questdialogmenu.layout"

    patch_charactercreate(cc_path)
    patch_tipmenu(tip_path)
    patch_questdialog(qd_path)

    # Also deploy to local game folder for immediate testing
    game_ui = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\media\UI"
    if os.path.exists(game_ui):
        shutil.copy2(cc_path, os.path.join(game_ui, "charactercreate.layout"))
        shutil.copy2(tip_path, os.path.join(game_ui, "tipmenu.layout"))
        shutil.copy2(qd_path, os.path.join(game_ui, "questdialogmenu.layout"))
        print(f"[LayoutPatch] Deployed updated layout files to {game_ui}")

    print("[LayoutPatch] SUCCESS: All layout fixes applied.")


if __name__ == "__main__":
    main()
