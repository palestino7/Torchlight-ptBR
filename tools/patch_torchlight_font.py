#!/usr/bin/env python3
"""
tools/patch_torchlight_font.py - Localizes Torchlight Regular.ttf with authentic Portuguese accented glyphs.

Problem:
The original Torchlight Regular.ttf font created by Runic Games in 2009 contains cmap entries
for accented Latin-1 characters (ç, ã, é, etc.), but their glyphs have 0 contours (empty),
causing in-game text like "Poção de Mana" to render with missing letters ("Po  o de Mana").

Crucially, Torchlight Regular.ttf ALREADY contains the authentic hand-drawn accent glyphs:
'cedilla', 'acute', 'grave', 'circumflex', 'tilde', 'dieresis', etc., as well as 'dotlessi'.
This script synthesizes complete, fully outlined TrueType glyphs for all Portuguese and Latin-1
accented letters by merging the base letter contours with the authentic accent contours,
preserving 100% of the game's unique cartoon/chunky art style.
"""

import os
import shutil
import zipfile
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from PIL import Image, ImageFont, ImageDraw


def create_merged_glyph(font: TTFont, base_name: str, accent_name: str, dx: float, dy: float, sx: float = 1.0, sy: float = 1.0) -> Glyph:
    glyf = font['glyf']
    base = glyf[base_name]
    accent = glyf[accent_name]

    b_coords, b_endPts, b_flags = base.getCoordinates(glyf)
    a_coords, a_endPts, a_flags = accent.getCoordinates(glyf)

    new_coords = GlyphCoordinates(b_coords)
    a_copy = GlyphCoordinates(a_coords)
    if sx != 1.0 or sy != 1.0:
        a_copy.scale((sx, sy))
    a_copy.translate((dx, dy))
    new_coords.extend(a_copy)

    new_endPts = list(b_endPts) + [p + len(b_coords) for p in a_endPts]
    new_flags = list(b_flags) + list(a_flags)

    new_glyph = Glyph()
    new_glyph.numberOfContours = len(new_endPts)
    new_glyph.coordinates = new_coords
    new_glyph.endPtsOfContours = new_endPts
    new_glyph.flags = new_flags
    new_glyph.program = base.program if hasattr(base, 'program') else None
    new_glyph.recalcBounds(glyf)
    return new_glyph


def patch_font(input_path: str, output_path: str) -> None:
    print(f"[FontPatch] Loading source font from {input_path}...")
    font = TTFont(input_path)
    glyf = font['glyf']
    hmtx = font['hmtx']

    # 1. Lowercase Cedilla: 'c' + 'cedilla'
    # cedilla x center is ~564, c center is ~554. dx = -10, dy = 0 aligns perfectly under the lower curve of c
    glyf['ccedilla'] = create_merged_glyph(font, 'c', 'cedilla', -10, 0)
    hmtx['ccedilla'] = (hmtx['c'][0], glyf['ccedilla'].xMin)

    # Uppercase Cedilla: 'C' + 'cedilla'
    # C center is ~776, cedilla center is ~564. dx = 210, dy = 0, sx=1.15, sy=1.15
    glyf['Ccedilla'] = create_merged_glyph(font, 'C', 'cedilla', 200, 0, sx=1.15, sy=1.15)
    hmtx['Ccedilla'] = (hmtx['C'][0], glyf['Ccedilla'].xMin)

    # 2. Lowercase Top Accents
    # Position accent so its yMin is at base.yMax + gap (gap = 35)
    def add_lower_accent(target_glyph: str, base_glyph: str, accent_glyph: str, extra_dy: float = 0):
        b = glyf[base_glyph]
        a = glyf[accent_glyph]
        bcx = (b.xMin + b.xMax) / 2
        acx = (a.xMin + a.xMax) / 2
        dx = bcx - acx
        dy = (b.yMax + 35 - a.yMin) + extra_dy
        glyf[target_glyph] = create_merged_glyph(font, base_glyph, accent_glyph, dx, dy)
        hmtx[target_glyph] = (hmtx[base_glyph][0], glyf[target_glyph].xMin)

    # For 'i', replace the dot with the accent placed where the dot was
    def add_i_accent(target_glyph: str, accent_glyph: str):
        a = glyf[accent_glyph]
        acx = (a.xMin + a.xMax) / 2
        dx = 335 - acx
        dy = 1150 - a.yMin
        glyf[target_glyph] = create_merged_glyph(font, 'dotlessi', accent_glyph, dx, dy, sx=0.9, sy=0.9)
        hmtx[target_glyph] = (hmtx['i'][0], glyf[target_glyph].xMin)

    # 'a' accents
    add_lower_accent('aacute', 'a', 'acute')
    add_lower_accent('agrave', 'a', 'grave')
    add_lower_accent('atilde', 'a', 'tilde')
    add_lower_accent('acircumflex', 'a', 'circumflex')
    add_lower_accent('adieresis', 'a', 'dieresis')

    # 'e' accents
    add_lower_accent('eacute', 'e', 'acute')
    add_lower_accent('egrave', 'e', 'grave')
    add_lower_accent('ecircumflex', 'e', 'circumflex')
    add_lower_accent('edieresis', 'e', 'dieresis')

    # 'i' accents
    add_i_accent('iacute', 'acute')
    add_i_accent('igrave', 'grave')
    add_i_accent('icircumflex', 'circumflex')
    add_i_accent('idieresis', 'dieresis')

    # 'o' accents
    add_lower_accent('oacute', 'o', 'acute')
    add_lower_accent('ograve', 'o', 'grave')
    add_lower_accent('otilde', 'o', 'tilde')
    add_lower_accent('ocircumflex', 'o', 'circumflex')
    add_lower_accent('odieresis', 'o', 'dieresis')

    # 'u' accents
    add_lower_accent('uacute', 'u', 'acute')
    add_lower_accent('ugrave', 'u', 'grave')
    add_lower_accent('ucircumflex', 'u', 'circumflex')
    add_lower_accent('udieresis', 'u', 'dieresis')

    # 'n' accents
    add_lower_accent('ntilde', 'n', 'tilde')

    # 3. Uppercase Top Accents
    # Scale accent slightly (0.78x) to fit gracefully within typography ascender line
    def add_upper_accent(target_glyph: str, base_glyph: str, accent_glyph: str, target_top: float = 1820):
        b = glyf[base_glyph]
        a = glyf[accent_glyph]
        scale = 0.78
        bcx = (b.xMin + b.xMax) / 2
        acx = ((a.xMin + a.xMax) / 2) * scale
        dx = bcx - acx
        acc_top = a.yMax * scale
        dy = target_top - acc_top
        glyf[target_glyph] = create_merged_glyph(font, base_glyph, accent_glyph, dx, dy, sx=scale, sy=scale)
        hmtx[target_glyph] = (hmtx[base_glyph][0], glyf[target_glyph].xMin)

    # 'A' accents
    add_upper_accent('Aacute', 'A', 'acute')
    add_upper_accent('Agrave', 'A', 'grave')
    add_upper_accent('Atilde', 'A', 'tilde')
    add_upper_accent('Acircumflex', 'A', 'circumflex')
    add_upper_accent('Adieresis', 'A', 'dieresis')

    # 'E' accents
    add_upper_accent('Eacute', 'E', 'acute')
    add_upper_accent('Egrave', 'E', 'grave')
    add_upper_accent('Ecircumflex', 'E', 'circumflex')
    add_upper_accent('Edieresis', 'E', 'dieresis')

    # 'I' accents
    add_upper_accent('Iacute', 'I', 'acute')
    add_upper_accent('Igrave', 'I', 'grave')
    add_upper_accent('Icircumflex', 'I', 'circumflex')
    add_upper_accent('Idieresis', 'I', 'dieresis')

    # 'O' accents
    add_upper_accent('Oacute', 'O', 'acute')
    add_upper_accent('Ograve', 'O', 'grave')
    add_upper_accent('Otilde', 'O', 'tilde')
    add_upper_accent('Ocircumflex', 'O', 'circumflex')
    add_upper_accent('Odieresis', 'O', 'dieresis')

    # 'U' accents
    add_upper_accent('Uacute', 'U', 'acute')
    add_upper_accent('Ugrave', 'U', 'grave')
    add_upper_accent('Ucircumflex', 'U', 'circumflex')
    add_upper_accent('Udieresis', 'U', 'dieresis')

    # 'N' accents
    add_upper_accent('Ntilde', 'N', 'tilde')

    # 4. Safely set ascender metrics so high uppercase accents never get clipped by render engines
    font['hhea'].ascent = 1890
    font['OS/2'].usWinAscent = 1890

    # Ensure output dir exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    font.save(output_path)
    print(f"[FontPatch] Saved patched font to {output_path}")


def verify_font(font_path: str) -> bool:
    print(f"[FontPatch] Verifying character rendering with Pillow: {font_path}...")
    pil_font = ImageFont.truetype(font_path, 32)
    test_chars = "çãõáéíóúâêôàÇÃÕÁÉÍÓÚÂÊÔÀüÜ"
    missing = []
    for ch in test_chars:
        mask = pil_font.getmask(ch)
        bbox = mask.getbbox()
        if bbox is None:
            missing.append(ch)
            print(f"  [FAIL] {repr(ch)} (U+{ord(ch):04X}) has empty bbox!")
        else:
            print(f"  [OK] {repr(ch)}: size={mask.size}, bbox={bbox}")

    if missing:
        print(f"[FontPatch] FAILED: {len(missing)} characters missing outlines!")
        return False

    # Render comprehensive visual test sheet
    im = Image.new("RGB", (750, 220), (28, 25, 23))
    draw = ImageDraw.Draw(im)
    draw.text((20, 20), "Poção de Vida | Poção de Mana | Ação", font=pil_font, fill=(255, 215, 0))
    draw.text((20, 70), "á é í ó ú â ê ô ã õ à ç ü", font=pil_font, fill=(240, 240, 240))
    draw.text((20, 120), "Á É Í Ó Ú Â Ê Ô Ã Õ À Ç Ü", font=pil_font, fill=(240, 240, 240))
    draw.text((20, 170), "O Destruidor é mestre do combate corpo a corpo", font=pil_font, fill=(200, 220, 255))
    im.save("test_torchlight_font_accents.png")
    print("[FontPatch] Generated visual verification image: test_torchlight_font_accents.png")
    return True


def main():
    pak_path = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip"
    temp_source = "media/UI/Torchlight Regular.ttf"
    if not os.path.exists(temp_source):
        if os.path.exists(pak_path):
            with zipfile.ZipFile(pak_path, "r") as z:
                z.extract("media/UI/Torchlight Regular.ttf", ".")
        else:
            raise FileNotFoundError(f"Cannot find source font or Pak.zip at {pak_path}")

    # Output paths: translation_ptbr and game dir
    target_in_translation = "translation_ptbr/media/UI/Torchlight Regular.ttf"
    target_in_translation_upper = "translation_ptbr/media/UI/Torchlight Regular.TTF"
    target_in_game = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\media\UI\Torchlight Regular.ttf"
    target_in_game_upper = r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight\media\UI\Torchlight Regular.TTF"

    patch_font(temp_source, target_in_translation)

    if os.path.exists(os.path.dirname(target_in_game)):
        if os.path.normcase(os.path.abspath(target_in_translation)) != os.path.normcase(os.path.abspath(target_in_game)):
            shutil.copy2(target_in_translation, target_in_game)
            print(f"[FontPatch] Deployed to local game folder: {target_in_game}")

    success = verify_font(target_in_translation)
    if not success:
        raise RuntimeError("Font verification failed!")
    print("[FontPatch] COMPLETE SUCCESS: All Portuguese characters natively supported!")


if __name__ == "__main__":
    main()
