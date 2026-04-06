# "Google Drive Sync" Documentation

Welcome to the gdsync wiki. gdsync exports your Google Workspace files (Docs, Sheets, Slides, Drawings)
into multiple local formats, preserving your Drive folder structure.

## Pages

- **[Google Cloud Setup](Google-Cloud-Setup)** — Create a Google Cloud project and OAuth credentials
- **[Configuration](Configuration)** — Config files, output structure, and backup settings
- **[CLI Reference](CLI-Reference)** — All command-line flags and usage examples
- **[Troubleshooting](Troubleshooting)** — Common errors and how to fix them
- **[Development](Development)** — Building from source, testing, linting, and contributing

## How it works

1. Authenticates with Google Drive using OAuth 2.0 (read-only access)
1. Discovers all Workspace files and resolves their folder paths
1. Exports each file into every applicable format (Markdown, PDF, DOCX, CSV, XLSX, PPTX)
1. Tracks what was synced in a manifest for incremental updates
1. Archives the export as a timestamped zip snapshot

Subsequent runs only export files that have changed since the last sync.
