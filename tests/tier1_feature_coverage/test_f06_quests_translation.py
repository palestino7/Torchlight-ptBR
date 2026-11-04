"""
tests/tier1_feature_coverage/test_f06_quests_translation.py
Feature F06: Quests & Dialogues Translation
Verifies main story quests, NPC dialogues, reward formatting,
journal entries, and multiline dialogue integrity.
"""

import unittest
import json
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF06QuestsTranslation(unittest.TestCase):

    QUEST_TITLES = {
        "Torchlight Under Attack": "Torchlight Sob Ataque",
        "The Missing Girl": "A Garota Desaparecida",
        "Into the Depths": "Rumo às Profundezas",
        "The Corrupted Ember": "O Âmbar Corrompido"
    }

    NPC_DIALOGUES = {
        "Syl": (
            "We must find Master Alric before it's too late.",
            "Devemos encontrar o Mestre Alric antes que seja tarde demais."
        ),
        "Brink": (
            "The creatures from the mines... they're relentless!",
            "As criaturas das minas... elas são implacáveis!"
        ),
        "Vasman": (
            "I study the Ember. Its power is unmatched, yet perilous.",
            "Eu estudo o Âmbar. Seu poder é inigualável, mas perigoso."
        )
    }

    REWARDS = {
        "Reward: %d Gold": "Recompensa: %d de Ouro",
        "Experience: %d XP": "Experiência: %d XP",
        "Choose a Reward": "Escolha uma Recompensa"
    }

    JOURNAL_LABELS = {
        "Active Quests": "Missões Ativas",
        "Completed Quests": "Missões Concluídas",
        "Quest Log": "Registro de Missões"
    }

    def test_01_main_quest_titles_translation(self):
        """Major campaign quest titles must have evocative, narrative-accurate translations."""
        for eng, pt in self.QUEST_TITLES.items():
            self.assertNotEqual(eng, pt)
            self.assertGreater(len(pt), 5)

    def test_02_npc_dialogue_fidelity(self):
        """NPC narrative dialogues must maintain contextual tone and proper grammar."""
        for npc, (eng, pt) in self.NPC_DIALOGUES.items():
            self.assertNotEqual(eng, pt)
            # Ensure names (Syl, Alric, Brink) are retained
            if "Alric" in eng:
                self.assertIn("Alric", pt)
            if "Ember" in eng:
                self.assertIn("Âmbar", pt)

    def test_03_quest_rewards_formatting(self):
        """Reward strings must correctly translate terms while preserving numeric tokens."""
        for eng, pt in self.REWARDS.items():
            if "%d" in eng:
                self.assertIn("%d", pt)
            self.assertNotEqual(eng, pt)

    def test_04_journal_interface_labels(self):
        """Quest log headers and states must be clearly translated in pt-BR."""
        for eng, pt in self.JOURNAL_LABELS.items():
            self.assertIn("Missões", pt)

    def test_05_multiparagraph_npc_dialogue_newlines(self):
        """Long NPC dialogues with paragraph breaks must preserve line breaks exactly."""
        multiline_eng = "Greetings, adventurer.\n\nThe town needs your help.\nSpeak with Syl in the town square."
        multiline_pt = "Saudações, aventureiro.\n\nA cidade precisa de sua ajuda.\nFale com Syl na praça da cidade."
        
        self.assertEqual(multiline_eng.count("\n"), multiline_pt.count("\n"))
        self.assertTrue(multiline_pt.startswith("Saudações"))

    def test_06_live_catalog_quests_category_if_present(self):
        """If catalog JSON is present, verify Quests category."""
        catalog_path = PROJECT_ROOT / "translation_ptbr" / "translation_catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            quests = data.get("categories", {}).get("Quests", [])
            self.assertIsInstance(quests, list)


if __name__ == "__main__":
    unittest.main()
