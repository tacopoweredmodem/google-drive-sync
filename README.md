<!-- cSpell:words gdsync venv pptx docx xlsx -->

# gdsync

Sync all Google Workspace files (Docs, Sheets, Slides, Drawings) from your Drive into multiple formats, preserving folder structure.

## Output Structure

```text
~/Documents/gdsync/
├── markdown/        # Docs → .md
├── csv/             # Sheets → .csv
├── pdf/             # All types → .pdf
├── docx/            # Docs → Word
├── xlsx/            # Sheets → Excel
├── pptx/            # Slides → PowerPoint
├── manifest.json    # Sync log
└── .archives/       # Timestamped zip snapshots
```

---

## Installation

### Homebrew (macOS)

```bash
brew tap adamabernathy/gdsync
brew install gdsync
```

### pipx (recommended for CLI tools)

```bash
pipx install gdsync
```

### pip (from PyPI)

```bash
pip install gdsync
```

### pip (from GitHub)

```bash
pip install git+https://github.com/adamabernathy/gdsync.git
```

### From source

```bash
git clone https://github.com/adamabernathy/gdsync.git
cd gdsync
pip install .
```

All methods install the `gdsync` command into your PATH.

---

## Local Development

```bash
# 1. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install in editable mode with dev tools
pip install -e ".[dev]"

# 3. Verify
gdsync --version
```

> **Note:** Editable installs (`pip install -e .`) require the project path to have no spaces.
> If your path has spaces, use `pip install .` and re-run it after each code change.

### Project layout

```text
gdsync/
├── pyproject.toml        # Package metadata + dependencies
├── README.md
├── gdsync/
│   ├── __init__.py       # Version string
│   ├── cli.py            # Entry point, argument parsing, progress UI
│   └── core.py           # Auth, Drive API, export logic
└── tests/
    ├── test_core.py      # Config, safe_filename, HTML→Markdown
    └── test_cli.py       # Archive pruning, exceptions, manifest
```

### Testing & linting

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check gdsync/ tests/

# Auto-format
ruff format gdsync/ tests/
```

### Making changes

All application logic lives in two files:

- **`gdsync/core.py`** — authentication, file discovery, folder resolution, export, and conversion functions.
- **`gdsync/cli.py`** — `main()` entry point, argument parsing, progress bar, summary output, archiving.

After editing, run `gdsync` directly (editable install) or reinstall:

```bash
# If using editable install:
gdsync --dry-run

# If using standard install, reinstall after changes:
pip install . && gdsync --dry-run
```

### Bumping the version

Update the version in two places:

1. `gdsync/__init__.py` — `__version__ = "X.Y.Z"`
2. `pyproject.toml` — `version = "X.Y.Z"`

---

## Setup (Step by Step)

### Step 1: Create a Google Cloud Project

1. Open <https://console.cloud.google.com> and sign in with your Google account.
2. In the top-left dropdown (next to "Google Cloud"), click **Select a project** then **New Project**.
3. Give it any name (e.g. "gdsync") and click **Create**.
4. Make sure the new project is selected in the top-left dropdown.

### Step 2: Enable the Google Drive API

1. In the left sidebar, go to **APIs & Services > Library**.
2. Search for **Google Drive API**.
3. Click on it, then click the blue **Enable** button.

### Step 3: Configure the OAuth Consent Screen

You must do this before creating credentials.

1. In the left sidebar, go to **APIs & Services > OAuth consent screen**.
2. Click **Get Started** (or **Configure Consent Screen**).
3. Fill in:
   - **App name**: anything (e.g. "gdsync")
   - **User support email**: your email
   - **Developer contact email**: your email
4. Click **Save and Continue** through each section (Scopes, Test Users, Summary) — defaults are fine.
5. On the **Test Users** step, click **Add Users** and add your own Gmail/Workspace email address, then continue.
6. You should see a summary page. Click **Back to Dashboard**.

> **Important:** While the app is in "Testing" status, only the test users you added can authorize it. This is fine for personal use.

### Step 4: Create OAuth Credentials

1. In the left sidebar, go to **APIs & Services > Credentials**.
2. Click **+ Create Credentials** at the top, then select **OAuth client ID**.
3. For **Application type**, choose **Desktop app**.
4. Name it anything (e.g. "gdsync Desktop").
5. Click **Create**.
6. A dialog appears with your client ID. Click **Download JSON**.
7. **Rename** the downloaded file to `credentials.json`.
8. **Move** it to `~/.gdsync/credentials.json`:

```bash
mv ~/Downloads/client_secret_*.json ~/.gdsync/credentials.json
```

### Step 5: Run

```bash
# First run — preview what would be exported (no downloads):
gdsync --dry-run
```

**On the first run:**

1. A browser window will open asking you to sign in to Google.
2. You may see a warning: **"Google hasn't verified this app"** — this is expected for personal projects.
   - Click **Advanced** (bottom-left).
   - Click **Go to gdsync (unsafe)**.
3. Grant the requested permission (read-only access to Drive).
4. The browser will say "The authentication flow has completed." You can close it.

Your token is saved to `~/.gdsync/token.json` so you won't need to do this again.

```bash
# Sync (first run exports everything, subsequent runs only fetch changes):
gdsync

# Force a full re-export, ignoring previous sync state:
gdsync --full

# Export only Docs and Sheets:
gdsync --types docs sheets

# Custom output directory:
gdsync -o ~/Desktop/my_drive_backup

# Verbose logging (shows skipped files too):
gdsync -v
```

---

## Configuration

gdsync stores its config and credentials in `~/.gdsync/`:

```text
~/.gdsync/
├── config.yaml       # Settings (edit this)
├── credentials.json  # OAuth client secret (you provide this)
├── token.json        # OAuth token (auto-generated)
└── exceptions.yaml   # Files that failed to export (auto-generated)
```

### config.yaml

```yaml
output_dir: ~/Documents/gdsync
rate_limit_delay: 0.2
max_retries: 3
max_backups: 5
max_archive_mb: 500
```

| Key                | Description                                    | Default               |
| ------------------ | ---------------------------------------------- | --------------------- |
| `output_dir`       | Where exported files are saved                 | `~/Documents/gdsync`  |
| `rate_limit_delay` | Seconds to wait between API calls              | `0.2`                 |
| `max_retries`      | Number of retries on transient API errors      | `3`                   |
| `max_backups`      | Maximum number of archive snapshots to keep    | `5`                   |
| `max_archive_mb`   | Maximum total size of all archives (MB). Supersedes `max_backups` — if archives exceed this limit, the oldest are pruned even if the count is under `max_backups`. | `500` |

CLI flags (e.g. `-o`) always override config file values.

---

## CLI Options

| Flag                  | Description                                        |
| --------------------- | -------------------------------------------------- |
| `-o`, `--output`      | Output directory (overrides config)                |
| `-c`, `--credentials` | Path to OAuth credentials JSON                     |
| `-t`, `--token`       | Path to saved token file                           |
| `--types`             | Filter: `docs`, `sheets`, `slides`, `drawings`    |
| `--dry-run`           | List files without downloading                     |
| `--full`              | Force full re-export, ignore previous manifest     |
| `-v`, `--verbose`     | Show detailed step-by-step output                  |
| `--version`           | Show version and exit                              |

---

## Troubleshooting

| Problem                                      | Fix                                                                                                  |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **"This app is blocked"** in browser         | You skipped Step 3. Go back and configure the OAuth consent screen, and add yourself as a test user. |
| **"Google hasn't verified this app"** warning | Expected. Click **Advanced > Go to \[app name\] (unsafe)**.                                          |
| **"Credentials file not found"** error        | Make sure `credentials.json` is in `~/.gdsync/`.                                                     |
| **"Token has been expired or revoked"**       | Delete `~/.gdsync/token.json` and run `gdsync` again to re-authorize.                                |
| **403 / rate limit errors**                   | The tool retries automatically. If persistent, wait a few minutes and try again.                     |

---

## Notes

- gdsync uses `drive.readonly` scope. It **cannot** modify or delete your files.
- Google imposes rate limits on export requests. gdsync includes automatic retry with exponential backoff.
- Large Sheets with multiple tabs export as a single CSV (first sheet only). This is a Google API limitation.
- Files that fail to export are logged to `~/.gdsync/exceptions.yaml` and skipped on future runs. Remove an entry to retry.
