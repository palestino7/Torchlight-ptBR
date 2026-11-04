"""
tests/test_helpers.py
Shared test fixtures, binary encoders/decoders, mock generators, and validation helpers
for the Torchlight pt-BR translation test suite.
"""

import os
import sys
import struct
import re
import hashlib
import tempfile
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_STEAM_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Torchlight")

# UTF-16LE BOM constant
UTF16_LE_BOM = b"\xff\xfe"

# Canonical pt-BR accented characters
PTBR_LOWER_ACCENTS = "áéíóúâêôãõçàü"
PTBR_UPPER_ACCENTS = "ÁÉÍÓÚÂÊÔÃÕÇÀÜ"
PTBR_ALL_ACCENTS = PTBR_LOWER_ACCENTS + PTBR_UPPER_ACCENTS


def create_sample_adm_bytes(strings, version=1):
    """
    Builds a synthetic .dat.adm binary payload following Torchlight's
    reverse-engineered asset data model header and string table specification.
    """
    # Header: uint32 version, uint32 num_strings
    buf = bytearray()
    buf.extend(struct.pack("<II", version, len(strings)))
    
    for idx, s in enumerate(strings):
        token_id = 1000 + idx
        s_utf16 = s.encode("utf-16le")
        char_count = len(s)
        # Entry: uint32 token_id, uint32 char_count, wchar_t characters
        buf.extend(struct.pack("<II", token_id, char_count))
        buf.extend(s_utf16)
        
    return bytes(buf)


def parse_adm_bytes(data):
    """
    Parses a .dat.adm binary payload and returns a list of extracted strings.
    """
    if len(data) < 8:
        raise ValueError("Data too short for ADM header (min 8 bytes)")
    
    version, num_strings = struct.unpack_from("<II", data, 0)
    pos = 8
    strings = []
    
    for _ in range(num_strings):
        if pos + 8 > len(data):
            break
        token_id, char_count = struct.unpack_from("<II", data, pos)
        pos += 8
        byte_len = char_count * 2
        if pos + byte_len > len(data):
            break
        raw_chars = data[pos:pos + byte_len]
        pos += byte_len
        s = raw_chars.decode("utf-16le", errors="replace")
        strings.append(s)
        
    return version, strings


def create_sample_translation_dat(entries):
    """
    Generates a byte string for translation.dat in UTF-16LE with BOM (\xFF\xFE).
    entries: list of tuples (original, translation) or dict
    """
    if isinstance(entries, dict):
        entries = list(entries.items())
        
    lines = []
    for orig, trans in entries:
        lines.append("[TRANSLATION]")
        lines.append(f"<STRING>ORIGINAL:{orig}")
        lines.append(f"<STRING>TRANSLATION:{trans}")
        lines.append("[/TRANSLATION]")
        
    text_content = "\r\n".join(lines) + "\r\n"
    return UTF16_LE_BOM + text_content.encode("utf-16le")


def parse_translation_dat(data_or_path):
    """
    Parses a translation.dat file or bytes.
    Validates BOM, decodes UTF-16LE, and returns a dictionary of {original: translation}.
    """
    if isinstance(data_or_path, (str, Path)):
        with open(data_or_path, "rb") as f:
            raw = f.read()
    else:
        raw = data_or_path

    if not raw.startswith(UTF16_LE_BOM):
        raise ValueError("translation.dat missing UTF-16LE BOM (\\xFF\\xFE)")

    content = raw[2:].decode("utf-16le", errors="ignore")
    
    # Check for balanced tags
    open_tags = len(re.findall(r"\[TRANSLATION\]", content, re.IGNORECASE))
    close_tags = len(re.findall(r"\[/TRANSLATION\]", content, re.IGNORECASE))
    if open_tags != close_tags:
        raise ValueError(f"Unbalanced tags: {open_tags} [TRANSLATION] vs {close_tags} [/TRANSLATION]")

    pattern = re.compile(
        r"\[TRANSLATION\]\s*"
        r"<STRING>ORIGINAL:(.*?)\r?\n\s*"
        r"<STRING>TRANSLATION:(.*?)\r?\n\s*"
        r"\[/TRANSLATION\]",
        re.DOTALL
    )

    translations = {}
    for match in pattern.finditer(content):
        orig = match.group(1).strip()
        trans = match.group(2).strip()
        translations[orig] = trans

    return translations


def create_sample_cegui_layout(text_properties):
    """
    Generates a valid CEGUI XML layout document containing specified text properties.
    text_properties: dict of {window_name: text_value}
    """
    root = ET.Element("GUILayout")
    parent_win = ET.SubElement(root, "Window", {
        "Type": "DefaultWindow",
        "Name": "RootFrame"
    })
    
    for win_name, text_val in text_properties.items():
        child = ET.SubElement(parent_win, "Window", {
            "Type": "TaharezLook/Button",
            "Name": win_name
        })
        prop = ET.SubElement(child, "Property", {
            "Name": "Text",
            "Value": text_val
        })
        
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def parse_cegui_layout_texts(xml_bytes_or_str):
    """
    Extracts all Property Name='Text' values from a CEGUI layout.
    """
    if isinstance(xml_bytes_or_str, bytes):
        root = ET.fromstring(xml_bytes_or_str)
    else:
        root = ET.fromstring(xml_bytes_or_str.encode("utf-8"))
        
    texts = {}
    for win in root.iter("Window"):
        win_name = win.attrib.get("Name", "unnamed")
        for prop in win.findall("Property"):
            if prop.attrib.get("Name") == "Text":
                texts[win_name] = prop.attrib.get("Value", "")
    return texts


def calculate_sha256(filepath_or_bytes):
    """Calculates SHA-256 hash of a file or byte string."""
    h = hashlib.sha256()
    if isinstance(filepath_or_bytes, (str, Path)):
        with open(filepath_or_bytes, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    else:
        h.update(filepath_or_bytes)
    return h.hexdigest().lower()


def create_dummy_steam_game_dir(parent_temp_dir):
    """
    Creates a simulated Torchlight installation directory mimicking Steam App 41500.
    """
    game_dir = Path(parent_temp_dir) / "Steam" / "steamapps" / "common" / "Torchlight"
    game_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    (game_dir / "Torchlight.exe").write_bytes(b"MZ" + b"\x00" * 1024)
    (game_dir / "BuildVer.txt").write_bytes(UTF16_LE_BOM + "17685_201001261433".encode("utf-16le"))
    (game_dir / "resources.cfg").write_text("FileSystem=.\nZip=Pak.zip\n", encoding="ascii")
    
    # Create empty/minimal Pak.zip
    import zipfile
    with zipfile.ZipFile(game_dir / "Pak.zip", "w") as z:
        z.writestr("media/UI/mainmenuframe.layout", create_sample_cegui_layout({
            "QuitBtn": "Quit Game",
            "NewCharBtn": "New Character",
            "SettingsBtn": "Settings"
        }))
        z.writestr("media/units/items/sword.dat.adm", create_sample_adm_bytes(["Sword of Valor", "Common Sword"]))
        
    return game_dir
