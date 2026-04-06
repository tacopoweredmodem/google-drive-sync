# Development

## Prerequisites

- Python 3.10+
- Git

## Setup

```bash
git clone https://github.com/tacopoweredmodem/google-drive-sync.git
cd google-drive-sync

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify
gdsync --version
```

> **Note:** Editable installs (`pip install -e .`) require the project path to have no spaces.
> If your path has spaces, use `pip install .` and re-run it after each code change.

## Project layout

```text
google-drive-sync/
├── pyproject.toml        # Package metadata + dependencies
├── README.md
├── LICENSE
├── gdsync/
│   ├── __init__.py       # Version string
│   ├── cli.py            # Entry point, argument parsing, progress UI
│   └── core.py           # Auth, Drive API, export logic
├── tests/
│   ├── test_core.py      # Config, safe_filename, HTML→Markdown
│   └── test_cli.py       # Archive pruning, exceptions, manifest
├── wiki/                 # Wiki source (published via GitHub Actions)
└── .github/
    └── workflows/
        ├── test.yml      # CI: lint + test on Python 3.10–3.13
        ├── publish.yml   # Build + attach assets on release
        └── wiki.yml      # Publish wiki/ to GitHub Wiki
```

## Architecture

All application logic lives in two files:

- **`gdsync/core.py`** — Authentication, Google Drive API calls, file discovery, folder path resolution, export with retries, HTML-to-Markdown conversion, config management, and progress bar.
- **`gdsync/cli.py`** — `main()` entry point, argument parsing, sync orchestration, manifest management, exception tracking, failure reporting, archive creation and pruning, and all user-facing output.

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_core.py
```

Tests cover:

- Filename sanitization (`safe_filename`)
- HTML to Markdown conversion
- Config loading, merging, and saving (YAML)
- Archive pruning by count and size
- Archive size warning thresholds
- Exceptions YAML round-trip
- Manifest JSON round-trip
- Archive `.archives/` exclusion

## Linting

```bash
# Check for issues
ruff check gdsync/ tests/

# Auto-fix what can be fixed
ruff check --fix gdsync/ tests/

# Format code
ruff format gdsync/ tests/

# Check formatting without changes
ruff format --check gdsync/ tests/
```

Ruff is configured in `pyproject.toml`:

- Target: Python 3.10
- Line length: 99
- Rules: E (errors), F (pyflakes), W (warnings), I (import sorting)

## Making changes

With an editable install, changes take effect immediately:

```bash
gdsync --dry-run
```

With a standard install, reinstall after changes:

```bash
pip install . && gdsync --dry-run
```

## Bumping the version

Update the version in two places:

1. `gdsync/__init__.py` — `__version__ = "X.Y.Z"`
1. `pyproject.toml` — `version = "X.Y.Z"`

## CI/CD

### Tests (on every push/PR to main)

- Runs on Python 3.10, 3.11, 3.12, 3.13
- Lints with `ruff check`
- Checks formatting with `ruff format --check`
- Runs `pytest`

### Release (on GitHub release publish)

- Builds sdist and wheel with `python -m build`
- Attaches build artifacts to the GitHub release

### Wiki (on push to main)

- Publishes the `wiki/` directory to the repository's GitHub Wiki
