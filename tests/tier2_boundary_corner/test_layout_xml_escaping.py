"""
tests/tier2_boundary_corner/test_layout_xml_escaping.py
Tier 2 Boundary & Corner Tests: XML Special Characters in CEGUI Layouts
Tests escaping of &, <, >, \", ' in CEGUI layout XML files, UTF-8 attribute encoding,
and XML parser rejection of invalid entities.
"""

import unittest
import xml.etree.ElementTree as ET
from tests.test_helpers import create_sample_cegui_layout, parse_cegui_layout_texts


class TestLayoutXMLEscaping(unittest.TestCase):

    def test_01_ampersand_escaping_in_button_text(self):
        """Ampersands in UI labels (e.g. 'Armas & Armaduras') must be properly escaped as &amp;."""
        layout_dict = {"ArmoryBtn": "Armas & Armaduras"}
        xml_bytes = create_sample_cegui_layout(layout_dict)
        
        # Verify XML raw bytes contains &amp;
        self.assertIn(b"Armas &amp; Armaduras", xml_bytes)
        
        # Verify parser roundtrips unescaped '&'
        parsed = parse_cegui_layout_texts(xml_bytes)
        self.assertEqual(parsed.get("ArmoryBtn"), "Armas & Armaduras")

    def test_02_angle_brackets_escaping(self):
        """Angle brackets (< and >) in text attributes must be escaped as &lt; and &gt;."""
        layout_dict = {"NavNext": "< Anterior", "NavPrev": "Próximo >"}
        xml_bytes = create_sample_cegui_layout(layout_dict)
        
        self.assertIn(b"&lt; Anterior", xml_bytes)
        self.assertIn(b"Pr&oacute;ximo &gt;" if b"&oacute;" in xml_bytes else b"&gt;", xml_bytes)
        
        parsed = parse_cegui_layout_texts(xml_bytes)
        self.assertEqual(parsed.get("NavNext"), "< Anterior")
        self.assertEqual(parsed.get("NavPrev"), "Próximo >")

    def test_03_quotes_in_layout_text(self):
        """Single and double quotes inside layout property values must not break XML attribute delimiters."""
        layout_dict = {"QuoteBtn": 'Diga "Olá" ao ferreiro!'}
        xml_bytes = create_sample_cegui_layout(layout_dict)
        
        parsed = parse_cegui_layout_texts(xml_bytes)
        self.assertEqual(parsed.get("QuoteBtn"), 'Diga "Olá" ao ferreiro!')

    def test_04_accented_characters_in_utf8_xml(self):
        """Accented pt-BR strings in CEGUI layout files must encode cleanly in UTF-8."""
        layout_dict = {
            "ConfigBtn": "Configurações",
            "HeroClassBtn": "Destruição e Âmbar",
            "DiffBtn": "Fácil / Difícil"
        }
        xml_bytes = create_sample_cegui_layout(layout_dict)
        parsed = parse_cegui_layout_texts(xml_bytes)
        
        self.assertEqual(parsed.get("ConfigBtn"), "Configurações")
        self.assertEqual(parsed.get("HeroClassBtn"), "Destruição e Âmbar")
        self.assertEqual(parsed.get("DiffBtn"), "Fácil / Difícil")

    def test_05_unescaped_xml_rejection(self):
        """Raw unescaped XML entities must cause ParseError when parsed."""
        raw_broken_xml = b"""<GUILayout><Window Type="DefaultWindow" Name="Root">
            <Property Name="Text" Value="Broken & Unescaped" />
        </Window></GUILayout>"""
        with self.assertRaises(ET.ParseError):
            ET.fromstring(raw_broken_xml)


if __name__ == "__main__":
    unittest.main()
