# TEST_INFRA — E2E Test Infrastructure & Specification

**Project**: Torchlight pt-BR Translation & Installer  
**Owner**: Test Writer E2E Track (`test_writer_e2e`)  
**Status**: ACTIVE  
**Last Updated**: 2026-11-03T20:36:00Z  

---

## 1. Executive Summary & Test Strategy

This document defines the architecture, test tiers, verification methodologies, and traceability matrices for the **Torchlight pt-BR Translation Project**. The test suite employs a strict, requirement-driven, opaque-box methodology designed to validate 100% of all inventoried features (F01–F16), edge conditions, cross-feature pipelines, and realistic game deployment workloads.

### Core Testing Principles
1. **Opaque-Box Verification**: Tests validate behavior against external interface contracts, binary format specifications, data schemas, and actual game engine expectations without coupling to internal implementation ephemera.
2. **Progressive Testability**: During milestone execution, tests provide self-contained contract verification with synthetic fixtures while automatically discovering and validating live milestone artifacts as they become available on disk.
3. **No Facades / Anti-Cheat Integrity**: Every test case performs genuine parsing, decoding, validation, or filesystem assertions. Facade tests that trivially return `True` are strictly prohibited.
4. **Authoritative Expected Output Derivation**: Every test derives expected outputs from ground truth: the original Torchlight engine binaries (`Torchlight.exe`, `Pak.zip`), CEGUI XML schemas, Inno Setup compiler specifications, and the project interface contracts in `PROJECT.md`.

---

## 2. Test Architecture & Tier Taxonomy

The test framework is organized into 4 distinct tiers under `tests/`:

```
tests/
├── run_all_tests.py                    # Master test runner (exit 0 on 100% pass)
├── test_helpers.py                     # Shared assertions, mock generators, binary helpers
├── tier1_feature_coverage/             # >=5 test cases per feature (F01–F16)
│   ├── test_f01_extraction.py
│   ├── test_f02_compilation.py
│   ├── test_f03_ui_translation.py
│   ├── test_f04_items_translation.py
│   ├── test_f05_skills_translation.py
│   ├── test_f06_quests_translation.py
│   ├── test_f07_monsters_translation.py
│   ├── test_f08_transmutation_translation.py
│   ├── test_f09_formatting_accents.py
│   ├── test_f10_installer_detection.py
│   ├── test_f11_backup_rollback.py
│   ├── test_f12_clean_pe_metadata.py
│   ├── test_f13_build_pipeline.py
│   ├── test_f14_github_repo.py
│   ├── test_f15_documentation_readme.py
│   └── test_f16_visual_assets.py
├── tier2_boundary_corner/              # Stress, encoding, and adversarial boundaries
│   ├── test_bom_validation.py
│   ├── test_utf16le_edge_cases.py
│   ├── test_empty_translations.py
│   ├── test_formatting_tags.py
│   ├── test_long_quest_strings.py
│   ├── test_unicode_accents.py
│   └── test_layout_xml_escaping.py
├── tier3_cross_feature/                # Multi-stage integration pipelines
│   ├── test_pipeline_e2e.py
│   ├── test_catalog_dat_bijection.py
│   ├── test_installer_payload_sync.py
│   └── test_distribution_integrity.py
└── tier4_real_world/                   # Realistic deployment workloads & game directory
    ├── test_steam_dummy_install.py
    ├── test_translation_applied_hierarchy.py
    ├── test_clean_backup_rollback.py
    ├── test_sha256_checksum_verification.py
    └── test_live_torchlight_directory.py
```

### Tier Definitions
- **Tier 1 — Feature Coverage**: Comprehensive verification of each inventoried feature in `PROJECT.md` (minimum 5 test cases per feature, covering all 16 features F01–F16 = 80+ test cases).
- **Tier 2 — Boundary & Corner Cases**: Deep stress testing of encodings (UTF-16LE, BOM), formatting codes (`|c...|u`), extreme text lengths, null/empty strings, special XML entities, and full pt-BR accented character sets.
- **Tier 3 — Cross-Feature Integration**: End-to-end pipeline flows connecting extraction -> catalog -> compiler -> `translation.dat` -> Inno Setup script payload -> installer distribution bundle.
- **Tier 4 — Realistic Game Workloads**: End-to-end deployment into simulated Steam installation hierarchies, live game path detection, backup creation, clean uninstallation/rollback, and SHA-256 distribution verification.

---

## 3. Feature Inventory & Coverage Mapping (F01–F16)

| Feature ID | Feature Name | Test Suite Module | Min Tests | Key Verifications |
|------------|--------------|-------------------|:---------:|-------------------|
| **F01** | Text Extraction Tooling | `tier1_feature_coverage/test_f01_extraction.py` | 5 | ADM binary string table parsing, token filtering, XML layout parsing, category classification, live `Pak.zip` extraction |
| **F02** | String Compilation Tooling | `tier1_feature_coverage/test_f02_compilation.py` | 5 | UTF-16LE with BOM generation, `[TRANSLATION]` block syntax, XML layout serialization, newline preservation, roundtrip consistency |
| **F03** | UI & Menus Translation | `tier1_feature_coverage/test_f03_ui_translation.py` | 5 | Main menu strings, difficulty levels, character creation, HUD/inventory labels, button length/overflow safety |
| **F04** | Items & Equipment Translation | `tier1_feature_coverage/test_f04_items_translation.py` | 5 | Weapons, armor, rarities, affixes (prefixes/suffixes), consumables, gems & sockets |
| **F05** | Skills & Spells Translation | `tier1_feature_coverage/test_f05_skills_translation.py` | 5 | Alchemist skills, Destroyer skills, Vanquisher skills, spell scrolls, cooldown/mana templates |
| **F06** | Quests & Dialogues Translation | `tier1_feature_coverage/test_f06_quests_translation.py` | 5 | Main story quest titles, NPC greeting dialogues, rewards formatting, quest log entries, multi-paragraph text |
| **F07** | Monsters, Bosses & Lore Translation | `tier1_feature_coverage/test_f07_monsters_translation.py` | 5 | Bosses & champions, monster modifiers, standard creatures, dungeon level names, lore notes |
| **F08** | Transmutation & Globals Translation | `tier1_feature_coverage/test_f08_transmutation_translation.py` | 5 | Transmutation recipes, combat log notifications, system error messages, floating text (`FloatyText`), global parameters |
| **F09** | Formatting & Accent Preservations | `tier1_feature_coverage/test_f09_formatting_accents.py` | 5 | CEGUI color tags `|c...|u`, newline preservation, pt-BR accented characters, no Mojibake, format specifiers (`%d`, `%s`) |
| **F10** | Inno Setup Script & Steam Auto-Detect | `tier1_feature_coverage/test_f10_installer_detection.py` | 5 | Inno Setup script structure, Steam App 41500 registry lookup, WOW6432Node fallback, `libraryfolders.vdf` parsing, install path validation |
| **F11** | Safety Backup & Rollback Uninstaller | `tier1_feature_coverage/test_f11_backup_rollback.py` | 5 | Pre-install backup creation, existing file preservation, uninstaller rollback, directory restoration, user save safety |
| **F12** | Clean PE Metadata & Zero False-Positive AV | `tier1_feature_coverage/test_f12_clean_pe_metadata.py` | 5 | PE VersionInfo metadata, `PrivilegesRequired` declaration, absence of UPX packing, standalone offline payload, Palestino7 branding |
| **F13** | Automated Build & Distribution Pipeline | `tier1_feature_coverage/test_f13_build_pipeline.py` | 5 | `build_installer.ps1` structure, `dist/` artifacts (`.exe`, `.zip`), SHA256 checksum generation, zip content validation, checksum verification |
| **F14** | GitHub Repository Setup via MCP | `tier1_feature_coverage/test_f14_github_repo.py` | 5 | Repo naming `palestino7/Torchlight-ptBR`, `.gitignore` binary rules, MIT `LICENSE`, author metadata, topic tags |
| **F15** | Illustrated Documentation & README | `tier1_feature_coverage/test_f15_documentation_readme.py` | 5 | Hero banner link, shields badges, 3-step tutorial, VirusTotal guidance, explicit Palestino7 attribution |
| **F16** | Visual Graphic Assets | `tier1_feature_coverage/test_f16_visual_assets.py` | 5 | `banner_hero.png` PNG signature & dimensions, wizard headers, icon `.ico` format, asset file existence, setup.iss asset references |

---

## 4. Authoritative Expected Output Derivations

| Test Domain | Input Source | Authoritative Reference / Oracle | Expected Derivation Rule |
|-------------|--------------|-----------------------------------|--------------------------|
| **ADM String Table** | Binary `.dat.adm` files in `Pak.zip` | Reverse engineering discovery (`explorer_survey_1`) | Header: `uint32 ver == 1`, `uint32 num_strings`. Entries: `uint32 id`, `uint32 len`, UTF-16LE characters. |
| **Translation DAT** | `translation.dat` | Torchlight `CStringTranslate::Translate()` (`0x52cbf0`) | Byte 0-1: `\xFF\xFE` (UTF-16LE BOM). Block: `[TRANSLATION]\r?\n<STRING>ORIGINAL:...\r?\n<STRING>TRANSLATION:...\r?\n[/TRANSLATION]`. |
| **CEGUI Layouts** | `media/UI/*.layout` | CEGUI XML v0.6 layout parser | Valid XML. Text properties inside `<Property Name="Text" Value="..." />`. |
| **pt-BR Typography** | Game TrueType fonts | `Torchlight Regular.ttf`, `BRLNSDB.TTF`, `CONSOLA.TTF` | CMAP table contains all 24 Latin-1 accented characters (`á, é, í, ó, ú, â, ê, ô, ã, õ, ç, etc.`). |
| **Steam Path Discovery** | Windows Registry | Valve Steam AppID 41500 specification | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 41500\InstallLocation`. |
| **Distribution Checksum** | Release files (`.exe`, `.zip`) | RFC 6234 (SHA-256 cryptographic standard) | `SHA256SUMS.txt` formatted as `<hash> *<filename>` or `<hash>  <filename>`. |

---

## 5. Execution Guide & Test Runner Semantics

### Command Line Usage
To execute the complete E2E test suite:
```powershell
python tests/run_all_tests.py
```

### Filtering by Tier
```powershell
python tests/run_all_tests.py --tier 1
python tests/run_all_tests.py --tier 2
python tests/run_all_tests.py --tier 3
python tests/run_all_tests.py --tier 4
```

### Detailed Verbosity
```powershell
python tests/run_all_tests.py --verbose
```

### Exit Code Semantics
- **`0`**: 100% of all executed tests passed successfully.
- **`1`**: One or more test assertions failed.
- **`2`**: Unhandled exception, execution interruption, or invalid configuration.

---

## 6. Progressive Testability Architecture

During active development across multiple milestones (M1–M5), some artifacts may still be in the process of implementation. The test suite handles this through **progressive dual-mode verification**:

1. **Synthetic Contract Mode (Always active)**:
   Tests verify the specification contract against self-contained mock inputs, ensuring the parsers, compilers, validators, and installers behave strictly according to requirements under all permutations.
2. **Live Artifact Mode (Activated when artifacts exist)**:
   When files such as `translation_ptbr/translations/translation.dat`, `dist/Torchlight_Traducao_ptBR_Setup.exe`, `README.md`, or `C:\Program Files (x86)\Steam\steamapps\common\Torchlight` exist, tests run full forensic validation on those real files.

---

## 7. Quality Gates & Readiness Criteria

The test infrastructure is deemed **READY** when:
1. `tests/run_all_tests.py` is present and functional.
2. All 4 tiers (`tier1_feature_coverage`, `tier2_boundary_corner`, `tier3_cross_feature`, `tier4_real_world`) contain valid, executable Python test cases.
3. Every inventoried feature F01–F16 has at least 5 distinct test cases in Tier 1.
4. Total test case count exceeds 100 tests.
5. `python tests/run_all_tests.py` runs cleanly and exits with code `0`.
6. `TEST_READY.md` is published at the project root.
