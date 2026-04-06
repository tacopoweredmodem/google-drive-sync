<!-- cSpell:words gdsync venv pptx docx xlsx pipx -->

# gdsync

<div align="center">

**Sync your Google Drive to local files. Automatically.**

[![Tests](https://github.com/tacopoweredmodem/google-drive-sync/actions/workflows/test.yml/badge.svg)](https://github.com/tacopoweredmodem/google-drive-sync/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Export Google Docs, Sheets, Slides, and Drawings into Markdown, PDF, CSV, DOCX, XLSX, and PPTX — preserving your Drive folder structure. Incremental syncs only fetch what changed.

</div>

---

## Quick Start

### 1. Install

```bash
pipx install git+https://github.com/tacopoweredmodem/google-drive-sync.git
```

<details>
<summary>Other install methods</summary>

```bash
# pip
pip install git+https://github.com/tacopoweredmodem/google-drive-sync.git

# From source
git clone https://github.com/tacopoweredmodem/google-drive-sync.git
cd google-drive-sync && pip install .
```

</details>

### 2. Set up Google credentials

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
1. Enable the **Google Drive API**
1. Configure the **OAuth consent screen** (add yourself as a test user)
1. Create an **OAuth client ID** (Desktop app) and download the JSON
1. Save it:

```bash
mkdir -p ~/.gdsync
mv ~/Downloads/client_secret_*.json ~/.gdsync/credentials.json
```

> See the [full setup guide](https://github.com/tacopoweredmodem/google-drive-sync/wiki/Google-Cloud-Setup) for detailed screenshots and instructions.

### 3. Run

```bash
gdsync --dry-run   # Preview what will sync
gdsync             # Sync everything
```

On first run, a browser window opens for Google sign-in. After that, it's automatic.

---

## What it does

```text
Google Drive      Local files
─────────────     ───────────
  My Doc      --> markdown/My Doc.md
                  pdf/My Doc.pdf
                  docx/My Doc.docx

  Budget      --> csv/Budget.csv
                  pdf/Budget.pdf
                  xlsx/Budget.xlsx

  Deck        --> pdf/Deck.pdf
                  pptx/Deck.pptx
```

- Exports each file into **every applicable format**
- Preserves your **Drive folder hierarchy**
- **Incremental** — only re-exports files that changed since last sync
- **Archives** — keeps timestamped zip snapshots with automatic pruning
- **Skips failures gracefully** — logs them and moves on

---

## Common commands

```bash
gdsync                       # Sync all files
gdsync --types docs sheets   # Only Docs and Sheets
gdsync --full                # Force full re-export
gdsync -o ~/Backup/drive     # Custom output directory
gdsync -v                    # Verbose logging
```

---

## Documentation

For detailed docs, see the **[Wiki](https://github.com/tacopoweredmodem/google-drive-sync/wiki)**:

- [Google Cloud Setup](https://github.com/tacopoweredmodem/google-drive-sync/wiki/Google-Cloud-Setup) — step-by-step credentials walkthrough
- [Configuration](https://github.com/tacopoweredmodem/google-drive-sync/wiki/Configuration) — config file, CLI options, and backup settings
- [CLI Reference](https://github.com/tacopoweredmodem/google-drive-sync/wiki/CLI-Reference) — all flags and usage examples
- [Troubleshooting](https://github.com/tacopoweredmodem/google-drive-sync/wiki/Troubleshooting) — common errors and fixes
- [Development](https://github.com/tacopoweredmodem/google-drive-sync/wiki/Development) — building from source, testing, and contributing

---

## License

[GNU Affero General Public License v3.0](LICENSE)
