#!/usr/bin/env python3
"""
tools/generate_assets.py - Visual Asset Generator for Torchlight pt-BR

Generates:
1. docs/images/banner_hero.png (1280x540, dark fantasy amber aesthetic)
2. src/installer/wizard_large.bmp (164x314, Inno Setup wizard banner)
3. src/installer/wizard_small.bmp (55x55, Inno Setup header logo)
4. src/installer/torchlight_ptbr.ico (Multi-resolution Windows application icon)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_IMAGES = PROJECT_ROOT / "docs" / "images"
INSTALLER_DIR = PROJECT_ROOT / "src" / "installer"

DOCS_IMAGES.mkdir(parents=True, exist_ok=True)
INSTALLER_DIR.mkdir(parents=True, exist_ok=True)


def create_banner():
    width, height = 1280, 540
    img = Image.new("RGBA", (width, height), (15, 12, 18, 255))
    draw = ImageDraw.Draw(img)

    # Ambient radial glow in background
    for r in range(400, 0, -10):
        alpha = int(35 * (1.0 - r / 400.0))
        glow_box = [width // 2 - r * 2, height // 2 - r, width // 2 + r * 2, height // 2 + r]
        draw.ellipse(glow_box, fill=(240, 140, 20, alpha))

    # Dark atmospheric gradients
    for y in range(height):
        ratio = y / height
        darkening = int(30 * (abs(ratio - 0.5) * 2))
        draw.line([(0, y), (width, y)], fill=(20 - darkening // 2, 14 - darkening // 3, 24 - darkening // 2, 40))

    # Golden border frame
    border_color = (212, 160, 23, 220)
    draw.rectangle([12, 12, width - 13, height - 13], outline=border_color, width=2)
    draw.rectangle([18, 18, width - 19, height - 19], outline=(140, 95, 10, 160), width=1)

    # Corner decorations
    c_len = 30
    for cx, cy in [(12, 12), (width - 13, 12), (12, height - 13), (width - 13, height - 13)]:
        dx = 1 if cx == 12 else -1
        dy = 1 if cy == 12 else -1
        draw.line([(cx, cy), (cx + dx * c_len, cy)], fill=(255, 215, 0, 255), width=3)
        draw.line([(cx, cy), (cx, cy + dy * c_len)], fill=(255, 215, 0, 255), width=3)

    # Try loading default font or fallback
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 68)
        font_sub = ImageFont.truetype("arialbd.ttf", 34)
        font_tag = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Title shadow and text
    title_text = "TORCHLIGHT"
    sub_text = "TRADUÇÃO PORTUGUÊS DO BRASIL"
    author_text = "Criado por Palestino7 • 100% Traduzido • Instalador Automático"

    # Draw Title with drop shadow and amber highlight
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tw = bbox[2] - bbox[0]
    tx = (width - tw) // 2
    ty = 130

    # Drop shadows
    draw.text((tx + 4, ty + 4), title_text, font=font_title, fill=(0, 0, 0, 240))
    draw.text((tx + 2, ty + 2), title_text, font=font_title, fill=(60, 25, 5, 220))
    # Golden ember gradient text
    draw.text((tx, ty), title_text, font=font_title, fill=(255, 195, 50, 255))

    # Draw Subtitle
    bbox_sub = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw = bbox_sub[2] - bbox_sub[0]
    sx = (width - sw) // 2
    sy = 225
    draw.text((sx + 2, sy + 2), sub_text, font=font_sub, fill=(0, 0, 0, 200))
    draw.text((sx, sy), sub_text, font=font_sub, fill=(230, 230, 240, 255))

    # Divider bar
    dw = 500
    dx = (width - dw) // 2
    draw.line([(dx, 290), (dx + dw, 290)], fill=(212, 160, 23, 200), width=2)
    # Center diamond
    draw.polygon([(width // 2, 284), (width // 2 + 8, 290), (width // 2, 296), (width // 2 - 8, 290)], fill=(255, 215, 0, 255))

    # Draw Author & Features
    bbox_tag = draw.textbbox((0, 0), author_text, font=font_tag)
    aw = bbox_tag[2] - bbox_tag[0]
    ax = (width - aw) // 2
    ay = 320
    draw.text((ax + 1, ay + 1), author_text, font=font_tag, fill=(0, 0, 0, 180))
    draw.text((ax, ay), author_text, font=font_tag, fill=(185, 205, 225, 240))

    # Badge pill at bottom
    badge_text = "Steam Build 17685 • v1.15 • 13.622 Textos • 0 Falso-Positivo"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_tag)
    bw = bbox_b[2] - bbox_b[0]
    bx = (width - bw) // 2
    by = 420
    pill_padding = 16
    draw.rounded_rectangle(
        [bx - pill_padding, by - 6, bx + bw + pill_padding, by + 30],
        radius=14,
        fill=(30, 25, 38, 230),
        outline=(212, 160, 23, 160),
        width=1
    )
    draw.text((bx, by), badge_text, font=font_tag, fill=(255, 215, 120, 255))

    banner_path = DOCS_IMAGES / "banner_hero.png"
    img.save(banner_path, "PNG")
    print(f"Generated hero banner: {banner_path} ({banner_path.stat().st_size} bytes)")


def create_wizard_images():
    # 1. Wizard Large (164 x 314)
    w_large, h_large = 164, 314
    large_img = Image.new("RGB", (w_large, h_large), (22, 18, 28))
    draw_l = ImageDraw.Draw(large_img)

    for y in range(h_large):
        factor = y / h_large
        r = int(22 + 40 * factor)
        g = int(18 + 20 * factor)
        b = int(28 + 10 * factor)
        draw_l.line([(0, y), (w_large, y)], fill=(r, g, b))

    # Amber decorative elements
    draw_l.rectangle([6, 6, w_large - 7, h_large - 7], outline=(160, 110, 20), width=1)
    draw_l.line([(15, 80), (w_large - 16, 80)], fill=(212, 160, 23), width=1)
    draw_l.line([(15, 240), (w_large - 16, 240)], fill=(212, 160, 23), width=1)

    try:
        font_w_t = ImageFont.truetype("arialbd.ttf", 16)
        font_w_s = ImageFont.truetype("arialbd.ttf", 11)
        font_w_p = ImageFont.truetype("arial.ttf", 9)
    except Exception:
        font_w_t = ImageFont.load_default()
        font_w_s = ImageFont.load_default()
        font_w_p = ImageFont.load_default()

    draw_l.text((16, 30), "TORCHLIGHT", font=font_w_t, fill=(255, 200, 50))
    draw_l.text((16, 52), "Tradução pt-BR", font=font_w_s, fill=(240, 240, 240))
    draw_l.text((16, 250), "Por Palestino7", font=font_w_s, fill=(212, 160, 23))
    draw_l.text((16, 268), "Versão 1.0.0", font=font_w_p, fill=(180, 180, 190))
    draw_l.text((16, 282), "Steam v1.15", font=font_w_p, fill=(140, 140, 150))

    large_path = INSTALLER_DIR / "wizard_large.bmp"
    large_img.save(large_path, "BMP")
    print(f"Generated wizard large: {large_path} ({large_path.stat().st_size} bytes)")

    # 2. Wizard Small (55 x 55)
    w_small, h_small = 55, 55
    small_img = Image.new("RGB", (w_small, h_small), (26, 22, 34))
    draw_s = ImageDraw.Draw(small_img)
    draw_s.rectangle([2, 2, w_small - 3, h_small - 3], outline=(212, 160, 23), width=1)
    # Ember flame diamond
    draw_s.polygon([(27, 8), (46, 27), (27, 46), (8, 27)], fill=(220, 120, 15), outline=(255, 215, 0))
    draw_s.polygon([(27, 16), (38, 27), (27, 38), (16, 27)], fill=(255, 210, 50))

    small_path = INSTALLER_DIR / "wizard_small.bmp"
    small_img.save(small_path, "BMP")
    print(f"Generated wizard small: {small_path} ({small_path.stat().st_size} bytes)")


def create_icon():
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    base_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base_img)

    # Circular badge with gradient and gold ring
    draw.ellipse([8, 8, 247, 247], fill=(24, 18, 30, 255), outline=(212, 160, 23, 255), width=8)
    draw.ellipse([22, 22, 233, 233], outline=(140, 95, 15, 200), width=3)

    # Ember flame / diamond emblem in center
    draw.polygon([(128, 40), (200, 128), (128, 216), (56, 128)], fill=(230, 120, 15, 255), outline=(255, 215, 0, 255))
    draw.polygon([(128, 70), (175, 128), (128, 186), (81, 128)], fill=(255, 195, 45, 255))
    draw.polygon([(128, 95), (152, 128), (128, 161), (104, 128)], fill=(255, 245, 150, 255))

    ico_path = INSTALLER_DIR / "torchlight_ptbr.ico"
    base_img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Generated application icon: {ico_path} ({ico_path.stat().st_size} bytes)")


if __name__ == "__main__":
    create_banner()
    create_wizard_images()
    create_icon()
    print("All visual assets generated successfully!")
