"""
tests/tier1_feature_coverage/test_f02_compilation.py
Feature F02: String Compilation Tooling
Verifies translation.dat UTF-16LE with BOM generation, block formatting,
CEGUI .layout XML compilation, and catalog-to-binary round-trip fidelity.
"""

import unittest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from tests.test_helpers import (
    UTF16_LE_BOM,
    create_sample_translation_dat,
    parse_translation_dat,
    create_sample_cegui_layout,
    parse_cegui_layout_texts,
    PROJECT_ROOT
)


class TestF02StringCompilationTooling(unittest.TestCase):

    def test_01_bom_and_utf16le_encoding(self):
        """Compiled translation.dat must start with UTF-16LE BOM (\xFF\xFE)."""
        entries = [("Quit Game", "Sair do Jogo"), ("Options", "Opções")]
        raw_dat = create_sample_translation_dat(entries)
        
        self.assertTrue(raw_dat.startswith(UTF16_LE_BOM), "Must start with \\xFF\\xFE BOM")
        # Ensure it can be decoded strictly as UTF-16LE after BOM
        decoded = raw_dat[2:].decode("utf-16le")
        self.assertIn("Sair do Jogo", decoded)
        self.assertIn("Opções", decoded)

    def test_02_block_structure_syntax(self):
        """translation.dat must strictly adhere to [TRANSLATION] tags and <STRING> prefixes."""
        entries = [("Single Word", "Palavra Única")]
        raw_dat = create_sample_translation_dat(entries)
        text = raw_dat[2:].decode("utf-16le")
        
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        self.assertEqual(lines[0], "[TRANSLATION]")
        self.assertEqual(lines[1], "<STRING>ORIGINAL:Single Word")
        self.assertEqual(lines[2], "<STRING>TRANSLATION:Palavra Única")
        self.assertEqual(lines[3], "[/TRANSLATION]")

    def test_03_multiline_translation_preservation(self):
        """Multiline descriptions (e.g. quest dialogues) must preserve newlines inside blocks."""
        quest_orig = "Line one.\nLine two.\nLine three."
        quest_trans = "Linha um.\nLinha dois.\nLinha três."
        raw_dat = create_sample_translation_dat([(quest_orig, quest_trans)])
        
        parsed = parse_translation_dat(raw_dat)
        self.assertIn(quest_orig, parsed)
        self.assertEqual(parsed[quest_orig], quest_trans)

    def test_04_cegui_layout_replacement(self):
        """Compilation into CEGUI .layout XML must replace Text values while keeping XML valid."""
        original_xml = create_sample_cegui_layout({
            "ResumeGameBtn": "Resume Game",
            "ExitBtn": "Exit"
        })
        root = ET.fromstring(original_xml)
        
        translations = {
            "Resume Game": "Continuar Jogo",
            "Exit": "Sair"
        }
        
        for prop in root.iter("Property"):
            if prop.attrib.get("Name") == "Text":
                val = prop.attrib.get("Value", "")
                if val in translations:
                    prop.set("Value", translations[val])
                    
        new_xml = ET.tostring(root, encoding="utf-8")
        parsed_texts = parse_cegui_layout_texts(new_xml)
        self.assertEqual(parsed_texts["ResumeGameBtn"], "Continuar Jogo")
        self.assertEqual(parsed_texts["ExitBtn"], "Sair")

    def test_05_catalog_to_dat_roundtrip(self):
        """A full set of catalog entries must round-trip through compilation and parsing losslessly."""
        catalog_sample = [
            ("New Character", "Novo Personagem"),
            ("Delete Character", "Excluir Personagem"),
            ("Select Hero Class", "Selecionar Classe"),
            ("Play", "Jogar"),
            ("Cancel", "Cancelar")
        ]
        raw_dat = create_sample_translation_dat(catalog_sample)
        parsed = parse_translation_dat(raw_dat)
        
        for orig, trans in catalog_sample:
            self.assertIn(orig, parsed)
            self.assertEqual(parsed[orig], trans)

    def test_06_unbalanced_tags_detection(self):
        """Parser must detect and reject malformed translation blocks with missing tags."""
        corrupt_dat = UTF16_LE_BOM + (
            "[TRANSLATION]\r\n"
            "<STRING>ORIGINAL:Test\r\n"
            "<STRING>TRANSLATION:Teste\r\n"
            # Missing [/TRANSLATION]
        ).encode("utf-16le")
        
        with self.assertRaises(ValueError):
            parse_translation_dat(corrupt_dat)


if __name__ == "__main__":
    unittest.main()
