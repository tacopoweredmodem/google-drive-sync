# CLI Reference

## Usage

```bash
gdsync [OPTIONS]
```

## Options

| Flag                  | Description                                                            |
| --------------------- | ---------------------------------------------------------------------- |
| `-o`, `--output`      | Output directory (overrides `output_dir` in config)                    |
| `-c`, `--credentials` | Path to OAuth credentials JSON (default: `~/.gdsync/credentials.json`) |
| `-t`, `--token`       | Path to saved token file (default: `~/.gdsync/token.json`)             |
| `--types`             | Filter by type: `docs`, `sheets`, `slides`, `drawings`                 |
| `--dry-run`           | List files that would be exported without downloading                  |
| `--full`              | Force full re-export, ignoring the previous manifest                   |
| `-v`, `--verbose`     | Show detailed step-by-step logging output                              |
| `--version`           | Show version and exit                                                  |

## Examples

### Basic sync

```bash
# Sync everything (incremental — only changed files):
gdsync

# First time? Preview what would be exported:
gdsync --dry-run
```

### Filter by type

```bash
# Only Docs and Sheets:
gdsync --types docs sheets

# Only Slides:
gdsync --types slides
```

### Custom output

```bash
# Export to a different directory:
gdsync -o ~/Desktop/my_drive_backup
```

### Full re-export

```bash
# Ignore the manifest and re-export everything:
gdsync --full
```

### Verbose mode

```bash
# See every file being processed, including skipped ones:
gdsync -v
```

This changes the output from the emoji-based progress bar to timestamped log lines at DEBUG level.

## Exit codes

| Code | Meaning                      |
| ---- | ---------------------------- |
| `0`  | Success (or nothing to sync) |
| `1`  | Missing credentials file     |

Files that fail to export are logged to `exceptions.yaml` but do not cause a non-zero exit.
