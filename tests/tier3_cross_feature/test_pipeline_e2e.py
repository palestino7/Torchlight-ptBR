"""
tests/tier3_cross_feature/test_pipeline_e2e.py
Tier 3 Cross-Feature Integration: End-to-End Pipeline
Validates complete flow: raw asset extraction -> catalog construction ->
compilation into translation.dat (UTF-16LE BOM) -> in-engine parsing roundtrip.
"""

import unittest
import tempfile
import json
from pathlib import Path
from tests.test_helpers import (
    create_sample_adm_bytes,
    parse_adm_bytes,
    create_sample_cegui_layout,
    parse_cegui_layout_texts,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestPipelineE2E(unittest.TestCase):

    def test_01_full_pipeline_roundtrip(self):
        """Simulate extraction of ADM and layout strings through catalog to compiled DAT."""
        # Step 1: Simulate extraction from binary ADM and XML layout
        raw_adm = create_sample_adm_bytes(["Sword of Valor", "Shield of Ages"])
        _, adm_strings = parse_adm_bytes(raw_adm)
        
        raw_xml = create_sample_cegui_layout({"StartBtn": "Start Game", "QuitBtn": "Quit Game"})
        layout_strings = list(parse_cegui_layout_texts(raw_xml).values())
        
        all_extracted = adm_strings + layout_strings
        self.assertEqual(len(all_extracted), 4)
        
        # Step 2: Build translation catalog
        catalog = {
            "metadata": {"game": "Torchlight", "version": "1.15", "total_strings": len(all_extracted)},
            "categories": {
                "Items": [
                    {"id": "ITEM_01", "original": "Sword of Valor", "translation": "Espada da Bravura"},
                    {"id": "ITEM_02", "original": "Shield of Ages", "translation": "Escudo das Eras"}
                ],
                "UI": [
                    {"id": "UI_01", "original": "Start Game", "translation": "Iniciar Jogo"},
                    {"id": "UI_02", "original": "Quit Game", "translation": "Sair do Jogo"}
                ]
            }
        }
        
        # Step 3: Compile catalog to translation.dat
        flat_translations = []
        for cat_list in catalog["categories"].values():
            for item in cat_list:
                flat_translations.append((item["original"], item["translation"]))
                
        compiled_dat_bytes = create_sample_translation_dat(flat_translations)
        self.assertTrue(compiled_dat_bytes.startswith(b"\xff\xfe"))
        
        # Step 4: Parse compiled translation.dat (simulating CStringTranslate)
        loaded_dictionary = parse_translation_dat(compiled_dat_bytes)
        
        self.assertEqual(loaded_dictionary["Sword of Valor"], "Espada da Bravura")
        self.assertEqual(loaded_dictionary["Shield of Ages"], "Escudo das Eras")
        self.assertEqual(loaded_dictionary["Start Game"], "Iniciar Jogo")
        self.assertEqual(loaded_dictionary["Quit Game"], "Sair do Jogo")

    def test_02_pipeline_handles_accented_ptbr_tokens(self):
        """Pipeline must preserve Brazilian Portuguese accents across all stages."""
        catalog = {
            "Items": [
                ("Potion of Healing", "Poção de Cura"),
                ("Magic Ring", "Anel Mágico")
            ]
        }
        raw_dat = create_sample_translation_dat(catalog["Items"])
        parsed = parse_translation_dat(raw_dat)
        self.assertEqual(parsed["Potion of Healing"], "Poção de Cura")
        self.assertEqual(parsed["Magic Ring"], "Anel Mágico")

    def test_03_pipeline_handles_formatting_tags(self):
        """Pipeline must keep |c...|u color codes intact from catalog to DAT."""
        catalog_item = [("Rare Item", "|cFFFFBA00Item Raro|u")]
        raw_dat = create_sample_translation_dat(catalog_item)
        parsed = parse_translation_dat(raw_dat)
        self.assertEqual(parsed["Rare Item"], "|cFFFFBA00Item Raro|u")


if __name__ == "__main__":
    unittest.main()
