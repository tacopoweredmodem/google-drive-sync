# Configuration

## Config directory

gdsync stores all configuration and credentials in `~/.gdsync/`:

```text
~/.gdsync/
├── config.yaml       # Settings (edit this)
├── credentials.json  # OAuth client secret (you provide this)
├── token.json        # OAuth token (auto-generated)
└── exceptions.yaml   # Files that failed to export (auto-generated)
```

The directory is created automatically on first run with restricted permissions (`0700`).

## config.yaml

Created automatically with defaults on first run. Edit to customize:

```yaml
output_dir: ~/Documents/gdsync
rate_limit_delay: 0.2
max_retries: 3
max_backups: 5
max_archive_mb: 500
```

| Key                | Description                                 | Default              |
| ------------------ | ------------------------------------------- | -------------------- |
| `output_dir`       | Where exported files are saved              | `~/Documents/gdsync` |
| `rate_limit_delay` | Seconds to wait between API calls           | `0.2`                |
| `max_retries`      | Number of retries on transient API errors   | `3`                  |
| `max_backups`      | Maximum number of archive snapshots to keep | `5`                  |
| `max_archive_mb`   | Maximum total size of all archives in MB    | `500`                |

CLI flags (e.g. `-o`) always override config file values.

### Backup settings

Archives are stored in `{output_dir}/.archives/` as timestamped zip files. Pruning works in two passes:

1. **Count-based** — if there are more than `max_backups` archives, the oldest are deleted first.
1. **Size-based** (supersedes count) — if total archive size exceeds `max_archive_mb`, the oldest archives are deleted until it fits. At least one archive is always kept.
1. **Warning** — if archives are 80% or more of `max_archive_mb`, a warning is printed with instructions to expand the limit or move archives out.

Before pruning, gdsync prints a `cp` command you can use to save the archive elsewhere.

## Output structure

```text
~/Documents/gdsync/
├── markdown/        # Docs → .md
├── csv/             # Sheets → .csv
├── pdf/             # All types → .pdf
├── docx/            # Docs → Word
├── xlsx/            # Sheets → Excel
├── pptx/            # Slides → PowerPoint
├── manifest.json    # Sync state for incremental updates
└── .archives/       # Timestamped zip snapshots
```

Each format directory mirrors your Google Drive folder hierarchy. For example, a Doc at `Work/Reports/Q4 Review` becomes:

```
markdown/Work/Reports/Q4 Review.md
pdf/Work/Reports/Q4 Review.pdf
docx/Work/Reports/Q4 Review.docx
```

## Export formats

| Google type | Exported formats    |
| ----------- | ------------------- |
| Docs        | Markdown, PDF, DOCX |
| Sheets      | CSV, PDF, XLSX      |
| Slides      | PDF, PPTX           |
| Drawings    | PDF                 |

## exceptions.yaml

Files that fail to export are automatically added to `~/.gdsync/exceptions.yaml` and skipped on future runs. The file looks like:

```yaml
- id: "1kvG-wQgm..."
  name: The Annual Report
  path: Reports/The Annual Report
  reason: This file is too large for Google to export.
```

To retry a file, remove its entry and run `gdsync` again.

## manifest.json

Located in the output directory, this file tracks what was synced and when. It enables incremental syncs — only files with a newer `modifiedTime` than the manifest entry are re-exported.

Use `gdsync --full` to ignore the manifest and force a complete re-export.
