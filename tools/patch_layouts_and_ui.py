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

    # Title "Dica" frame position and text (sits comfortably on the top border)
    framec_pattern = r'(<Window Type="GuiLook/ItemText" Name="Framec"\s*>)([\s\S]*?)(<Window Type="GuiLook/ItemText" Name="Frameb")'
    rep_framec = (
        r'\1\n'
        '            <Property Name="UnifiedPosition" Value="{{.5,-71},{.5,-175}}" />\n'
        '            <Property Name="UnifiedSize" Value="{{0,142},{0,28}}" />\n'
        '        <Window Type="GuiLook/StaticText" Name="Title">\n'
        '        <Property Name="HorzTextFormatting" Value="CentreAligned" />\n'
        '        <Property Name="VertFormatting" Value="CentreAligned" />\n'
        '        <Property Name="UnifiedSize" Value="{{0,142},{0,28}}" />\n'
        '\t\t<Property Name="TextColour" Value="FFFFFFFF"/>\n'
        '\t\t<Property Name="Font" Value="SerifBig"/>\n'
        '        <Property Name="Text" Value="Dica" />\n'
        '        </Window>   \n'
        '\t</Window>\n\n\n        '
        r'\3'
    )
    text = re.sub(framec_pattern, rep_framec, text)

    # Frameb size & position (balanced height 295, fits up to 9 lines of tips without clipping or void space)
    frameb_pattern = r'(<Window Type="GuiLook/ItemText" Name="Frameb"\s*>)([\s\S]*?)(<Window Type="GuiLook/StaticText" Name="Dialog")'
    rep_frameb = (
        r'\1\n'
        '\t\t    <Property Name="UnifiedPosition" Value="{{.5,-250},{.5,-160}}" />\n'
        '\t\t    <Property Name="UnifiedSize" Value="{{0,500},{0,295}}" />\n\n\t\t'
        r'\3'
    )
    text = re.sub(frameb_pattern, rep_frameb, text)

    # Dialog static text inside Frameb (wider width 470, height 220, fits long tips cleanly without overflow)
    dialog_pattern = r'(<Window Type="GuiLook/StaticText" Name="Dialog"\s*>)([\s\S]*?)(</Window>)'
    def replace_dialog(m):
        prefix = m.group(1)
        suffix = m.group(3)
        body = """
\t\t    <Property Name="Font" Value="SerifBig" />
\t\t    <Property Name="HorzTextFormatting" Value="WordWrapCentreAligned" />
\t\t    <Property Name="VertFormatting" Value="TopAligned" />
\t\t    <Property Name="UnifiedPosition" Value="{{0,15},{0,20}}" />
\t\t    <Property Name="UnifiedSize" Value="{{0,470},{0,225}}" />
\t\t\t<Property Name="TextColour" Value="FFFFFFFF"/>
\t\t\t<Property Name="MousePassThroughEnabled" Value="True" />
\t\t"""
        return f"{prefix}{body}{suffix}"

    text = re.sub(dialog_pattern, replace_dialog, text)

    # Adjust buttons inside Frameb
    ok_pattern = r'(<Window Type="GuiLook/StandardButton" Name="Ok"\s*>)([\s\S]*?)(</Window>)'
    rep_ok = (
        r'\1\n'
        '            <Property Name="UnifiedPosition" Value="{{.5,-76},{1,-42}}" />\n'
        '            <Property Name="UnifiedSize" Value="{{0,152},{0,28}}" />\n'
        '            <Property Name="Text" Value="Ok"/>\n'
        '\t\t<Property Name="onClick" Value="guiOk"/>\n'
        '    '
        r'\3'
    )
    text = re.sub(ok_pattern, rep_ok, text)

    showtips_pattern = r'(<Window Type="GuiLook/Checkbox" Name="ShowTips"\s*>)([\s\S]*?)(</Window>)'
    rep_showtips = (
        r'\1\n'
        '            <Property Name="Text" Value="Mostrar Dicas" />\n'
        '            <Property Name="UnifiedPosition" Value="{{.5,65},{1,-45}}" />\n'
        '            <Property Name="UnifiedSize" Value="{{0,50},{0,32}}" />\n'
        '        '
        r'\3'
    )
    text = re.sub(showtips_pattern, rep_showtips, text)

    encoded = (b"\xff\xfe" + text.encode("utf-16le")) if is_utf16 else text.encode("utf-8")
    with open(layout_path, "wb") as f:
        f.write(encoded)
    print(f"[LayoutPatch] Patched {layout_path}")


def patch_questdialog(layout_path: str):
    with open(layout_path, "rb") as f:
        raw = f.read()

    is_utf16 = raw.startswith(b"\xff\xfe")
    text = raw[2:].decode("utf-16le") if is_utf16 else raw.decode("utf-8")

    # Clear child text properties so they don't produce double colons with parent badge text
    text = re.sub(r'<Property Name="Text" Value="GP:0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="PO:0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="PO: 0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="XP:0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="XP: 0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="Fame:0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="Fama:0"\s*/>', '<Property Name="Text" Value="" />', text)
    text = re.sub(r'<Property Name="Text" Value="Fama: 0"\s*/>', '<Property Name="Text" Value="" />', text)

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
