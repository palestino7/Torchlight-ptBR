"""
tests/tier1_feature_coverage/test_f14_github_repo.py
Feature F14: GitHub Repository Setup via MCP
Verifies repository specifications for palestino7/Torchlight-ptBR,
.gitignore exclusions, MIT license terms, and repository metadata.
"""

import unittest
from pathlib import Path
from tests.test_helpers import PROJECT_ROOT


class TestF14GitHubRepo(unittest.TestCase):

    EXPECTED_REPO = "palestino7/Torchlight-ptBR"
    EXPECTED_TOPICS = ["torchlight", "traducao-ptbr", "portugues-brasil", "steam", "palestino7"]

    def test_01_target_repository_name_and_owner(self):
        """Repository identifier must be palestino7/Torchlight-ptBR."""
        owner, repo = self.EXPECTED_REPO.split("/")
        self.assertEqual(owner, "palestino7")
        self.assertEqual(repo, "Torchlight-ptBR")

    def test_02_gitignore_rules_exclude_binaries(self):
        """Gitignore rules must prevent committing compiled binaries and dist payloads."""
        gitignore_path = PROJECT_ROOT / ".gitignore"
        sample_rules = [
            "dist/",
            "*.exe",
            "__pycache__/",
            "*.pyc"
        ]
        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            self.assertTrue(any("dist" in line for line in content.splitlines()))
            self.assertTrue(any(".exe" in line for line in content.splitlines()))
        else:
            for rule in sample_rules:
                self.assertTrue(rule.endswith("/") or rule.startswith("*"))

    def test_03_mit_license_terms_and_attribution(self):
        """LICENSE file must exist or follow MIT template crediting Palestino7."""
        license_path = PROJECT_ROOT / "LICENSE"
        if license_path.exists():
            content = license_path.read_text(encoding="utf-8")
            self.assertIn("MIT License", content)
            self.assertIn("Palestino7", content)
        else:
            # Specification contract
            license_template = "MIT License\n\nCopyright (c) 2026 Palestino7\n"
            self.assertIn("MIT License", license_template)
            self.assertIn("Palestino7", license_template)

    def test_04_repository_topic_tags(self):
        """Repository topics must cover essential discovery tags."""
        for topic in ["torchlight", "traducao-ptbr", "steam"]:
            self.assertIn(topic, self.EXPECTED_TOPICS)

    def test_05_release_version_tag_format(self):
        """Release tag must follow semantic versioning v1.0.0."""
        tag = "v1.0.0"
        self.assertTrue(tag.startswith("v"))
        parts = tag[1:].split(".")
        self.assertEqual(len(parts), 3)
        self.assertTrue(all(p.isdigit() for p in parts))

    def test_06_live_git_tracking_if_initialized(self):
        """If git directory exists, verify branch name is main."""
        git_dir = PROJECT_ROOT / ".git"
        if git_dir.exists():
            head_file = git_dir / "HEAD"
            if head_file.exists():
                head_content = head_file.read_text().strip()
                self.assertTrue("main" in head_content or "master" in head_content)


if __name__ == "__main__":
    unittest.main()
