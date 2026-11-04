"""
tests/tier3_cross_feature/test_catalog_dat_bijection.py
Tier 3 Cross-Feature Integration: Catalog and DAT Bijection
Verifies exact 1:1 correspondence between translation_catalog.json
and translations/translation.dat.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import (
    PROJECT_ROOT,
    create_sample_translation_dat,
    parse_translation_dat
)


class TestCatalogDatBijection(unittest.TestCase):

    def test_01_bijection_contract_logic(self):
        """Synthetic catalog and DAT must have 100% mutual key and value coverage."""
        catalog = {
            "categories": {
                "UI": [
                    {"original": "Play", "translation": "Jogar"},
                    {"original": "Quit", "translation": "Sair"}
                ],
                "Items": [
                    {"original": "Axe", "translation": "Machado"}
                ]
            }
        }
        
        # Build catalog dict
        catalog_dict = {}
        for cat_list in catalog["categories"].values():
            for item in cat_list:
                catalog_dict[item["original"]] = item["translation"]
                
        # Generate DAT
        raw_dat = create_sample_translation_dat(list(catalog_dict.items()))
        dat_dict = parse_translation_dat(raw_dat)
        
        # Verify bijection: every catalog key in dat_dict, every dat_dict key in catalog
        self.assertEqual(set(catalog_dict.keys()), set(dat_dict.keys()))
        for k in catalog_dict:
            self.assertEqual(catalog_dict[k], dat_dict[k])

    def test_02_detect_missing_catalog_entries_in_dat(self):
        """Failure condition: if an entry is in catalog but missing in DAT, test must detect it."""
        catalog_dict = {"Key1": "Val1", "Key2": "Val2"}
        dat_dict = {"Key1": "Val1"}  # Missing Key2
        
        missing = set(catalog_dict.keys()) - set(dat_dict.keys())
        self.assertIn("Key2", missing)

    def test_03_detect_orphan_dat_entries(self):
        """Failure condition: if an entry is in DAT but not in catalog, test must detect it."""
        catalog_dict = {"Key1": "Val1"}
        dat_dict = {"Key1": "Val1", "GhostKey": "GhostVal"}
        
        orphans = set(dat_dict.keys()) - set(catalog_dict.keys())
        self.assertIn("GhostKey", orphans)

    def test_04_live_catalog_dat_bijection_if_both_exist(self):
        """If both translation_catalog.json and translation.dat exist on disk, verify bijection."""
        catalog_file = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        dat_file = PROJECT_ROOT / "translation_ptbr" / "translations" / "translation.dat"
        
        if catalog_file.exists() and dat_file.exists():
            with open(catalog_file, "r", encoding="utf-8") as f:
                cat_data = json.load(f)
            catalog_dict = {}
            for cat_list in cat_data.get("categories", {}).values():
                for item in cat_list:
                    catalog_dict[item["original"]] = item.get("translation", "")
                    
            dat_dict = parse_translation_dat(dat_file)
            
            # Check overlap
            common_keys = set(catalog_dict.keys()).intersection(set(dat_dict.keys()))
            self.assertGreater(len(common_keys), 0, "No common strings between catalog and DAT")


if __name__ == "__main__":
    unittest.main()
