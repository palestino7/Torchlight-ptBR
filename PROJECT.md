# Project: Torchlight pt-BR Translation & Installer

## Architecture
Torchlight (Steam Build 17685, Engine v1.15) localization system and installer architecture:
- **Game Engine & Text Hook**: The game uses `CStringTranslate::Translate()` at VA `0x52cbd0` (236 active call sites). It natively reads `translations\translation.dat` (UTF-16LE with BOM) relative to the Steam install directory `C:\Program Files (x86)\Steam\steamapps\common\Torchlight`.
- **UI Screens & Layouts**: 35 CEGUI `.layout` XML files inside `Pak.zip` / loose overlay files defining button text, menu titles, and window layouts.
- **Font Rendering**: CEGUI FreeType renderer using `media/UI/Torchlight Regular.ttf`, `BRLNSDB.TTF`, and `CONSOLA.TTF`, all containing 100% native Latin-1 accented glyphs (`á, é, í, ó, ú, â, ê, ô, ã, õ, ç, à, ü, etc.`).
- **Data Flow**:
  1. Extraction Tooling parses `Pak.zip` (`.dat.adm` token trees and `.layout` XMLs) -> `translation_catalog.json`.
  2. Localization Engine translates catalog -> Brazilian Portuguese (`pt-BR`) with contextual narrative fidelity and preserved formatting tags (`|cFFFFBA00...|u`).
  3. Compilation Tooling builds `translations\translation.dat` and localized `.layout` files.
  4. Inno Setup 6.7.3 compiles clean Delphi PE `.exe` installer with Steam App 41500 auto-detection, safety backup, and rollback uninstallation.
  5. Distribution pipeline creates `.exe`, `.zip`, and `SHA256SUMS.txt`.
  6. GitHub MCP initializes `palestino7/Torchlight-ptBR` with illustrated `README.md` and project assets.

## Feature Inventory
Every feature identified during Survey is assigned to a milestone:
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | Text Extraction Tooling | Script to parse all `.dat.adm` files and `.layout` XMLs from `Pak.zip` into structured JSON catalog | M1 | Survey 1 |
| F02 | String Compilation Tooling | Script to build `translations\translation.dat` (UTF-16LE with BOM) and localized `.layout` files from catalog | M1 | Survey 1 |
| F03 | UI & Menus Translation | 100% translation of main menu, options, character creation, inventory, HUD, tooltips | M2 | Survey 1 / R1 |
| F04 | Items & Equipment Translation | 100% translation of weapons, armor, gems, sockets, affixes, consumables, quest items | M2 | Survey 1 / R1 |
| F05 | Skills & Spells Translation | 100% translation of Alchemist, Destroyer, Vanquisher active/passive skills and spell scrolls | M2 | Survey 1 / R1 |
| F06 | Quests & Dialogues Translation | 100% translation of main story quests, random town quests, NPC greetings and dialogue trees | M2 | Survey 1 / R1 |
| F07 | Monsters, Bosses & Lore Translation | 100% translation of monster names, boss titles, champions, dungeon level descriptions, lore notes | M2 | Survey 1 / R1 |
| F08 | Transmutation & Globals Translation | 100% translation of recipes, combat notifications, system messages, difficulty levels | M2 | Survey 1 / R1 |
| F09 | Formatting & Accent Preservations | Preservation of color/style tags (`|c...|u`), line breaks (`\n`), and native pt-BR accents | M2 | Survey 1 / R1 |
| F10 | Inno Setup Script & Steam Auto-Detect | Inno Setup 6 Pascal script detecting `Steam App 41500` InstallLocation from Windows Registry | M3 | Survey 2 / R2 |
| F11 | Safety Backup & Rollback Uninstaller | Automatic backup of existing files and full uninstaller restoring original game files cleanly | M3 | Survey 2 / R2 |
| F12 | Clean PE Metadata & Zero False-Positive AV | Native compilation without UPX/PyInstaller, PE VersionInfo crediting Palestino7, lowest privileges | M3 | Survey 2 / R2 |
| F13 | Automated Build & Distribution Pipeline | PowerShell build script `build_installer.ps1` outputting `.exe`, `.zip` and `SHA256SUMS.txt` into `dist/` | M3 | Survey 2 / R2 |
| F14 | GitHub Repository Setup via MCP | Creation of public repository `palestino7/Torchlight-ptBR` with license, gitignore, and workflows | M4 | Survey 3 / R3 |
| F15 | Illustrated Documentation & README | Modern illustrated `README.md` with hero banner, badges, 3-step tutorial, VirusTotal 0/72 guide, crediting Palestino7 | M4 | Survey 3 / R3 |
| F16 | Visual Graphic Assets | Generation and integration of `banner_hero.png`, wizard header, and installer icon | M4 | Survey 3 / R3 |
| F17 | E2E Testing Suite (Tiers 1-4) | Comprehensive opaque-box test suite verifying string coverage, engine loading, installer, and repo | M5 | E2E Track |
| F18 | Adversarial Coverage Hardening (Tier 5) | White-box stress testing, corner cases, special characters, and edge case resilience | M5 | E2E Track |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Text Extraction & Compilation Pipeline | Build `tools/extract_strings.py`, `tools/compile_translation.py`, and `tools/verify_translation.py`; extract 13,622 clean strings (0 leaked assets) | none | DONE |
| M2 | pt-BR Complete Translation | Translate all extracted strings across all game categories to pt-BR; compile `translation.dat` & `.layout` | M1 | DONE |
| M3 | Executable Installer & Packaging Pipeline | Build Inno Setup installer script `setup.iss`, `build_installer.ps1`, compile `.exe` and `.zip` in `dist/` | M2 | DONE |
| M4 | GitHub Repository & Visual Documentation | Create `palestino7/Torchlight-ptBR`, commit code/translation, generate visual assets, publish illustrated `README.md` | M3 | DONE |
| M5 | Final Milestone: 100% E2E Test Suite & Hardening | Validate 100% of E2E test cases (Tiers 1-4) and complete Tier 5 adversarial hardening | M1, M2, M3, M4, TEST_READY | DONE |

## Interface Contracts

### M1 (Extraction Pipeline) ↔ M2 (Translation)
- **Input**: `C:\Program Files (x86)\Steam\steamapps\common\Torchlight\Pak.zip`
- **Output Catalog Format**: `translation_ptbr/translation_catalog.json`
  - Schema:
    ```json
    {
      "metadata": { "game": "Torchlight", "version": "1.15", "total_strings": 13622 },
      "categories": {
        "UI": [{ "id": "UI_001", "original": "Quit Game", "translation": "Sair do Jogo", "context": "mainmenuframe.layout" }],
        "Quests": [...],
        "Items": [...],
        "Skills": [...],
        "Affixes": [...],
        "Monsters": [...],
        "Globals": [...]
      }
    }
    ```
- **Compiler**: `tools/compile_translation.py` takes `translation_catalog.json` and outputs:
  - `translation_ptbr/translations/translation.dat` (UTF-16LE with BOM)
  - `translation_ptbr/media/UI/*.layout` (localized XML layout files)

### M2 (Translation) ↔ M3 (Installer)
- **Payload Directory**: `translation_ptbr/`
  - Contains `translations/translation.dat` and `media/UI/*.layout`.
- **Installer Source**: `src/installer/setup.iss` references `translation_ptbr/` to package all files into `dist/Torchlight_Traducao_ptBR_Setup.exe`.

### M3 (Installer) ↔ M4 (GitHub Repo)
- **Distribution Artifacts**: `dist/` contains:
  - `Torchlight_Traducao_ptBR_Setup.exe`
  - `Torchlight_Traducao_ptBR_v1.0.0.zip`
  - `SHA256SUMS.txt`
- **Repo Inclusions**: Source code, installer script, translation assets, documentation, and `SHA256SUMS.txt` committed to `palestino7/Torchlight-ptBR`. Executables excluded via `.gitignore` and documented in `README.md` with GitHub Releases download links.

### E2E Testing Track ↔ Implementation Track
- **Signal**: `TEST_READY.md` published at project root when test suite is built.
- **Runner**: `python tests/run_all_tests.py` returning exit code 0 if 100% of tests pass.

## Code Layout
```
c:\Users\omate\OneDrive\Desktop\Torchlight Tradução pt-BR\
├── .agents/
│   └── teamwork/
│       ├── ORIGINAL_REQUEST.md
│       ├── orchestrator/
│       ├── e2e_test_orch/
│       └── ...
├── docs/
│   └── images/
│       ├── banner_hero.png
│       ├── installer_welcome.png
│       └── ...
├── src/
│   └── installer/
│       ├── setup.iss
│       ├── setup_resources.rc
│       └── build_installer.ps1
├── tools/
│   ├── extract_strings.py
│   ├── compile_translation.py
│   └── verify_translation.py
├── translation_ptbr/
│   ├── translations/
│   │   └── translation.dat
│   └── media/
│       └── UI/
├── tests/
│   ├── e2e/
│   ├── tier1_feature_coverage/
│   ├── tier2_boundary_corner/
│   ├── tier3_cross_feature/
│   ├── tier4_real_world/
│   └── run_all_tests.py
├── dist/
│   ├── Torchlight_Traducao_ptBR_Setup.exe
│   ├── Torchlight_Traducao_ptBR_v1.0.0.zip
│   └── SHA256SUMS.txt
├── .gitignore
├── LICENSE
├── README.md
├── RELEASE_NOTES_v1.0.0.md
├── PROJECT.md
└── TEST_READY.md (published upon E2E test completion)
```
