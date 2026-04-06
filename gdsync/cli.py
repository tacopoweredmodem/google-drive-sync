"""
CLI entry point for gdsync.
"""

import argparse
import json
import logging
import time
import zipfile
from pathlib import Path

import yaml

from . import __version__
from .core import (
    TYPE_LABELS,
    authenticate,
    build_service,
    export_workspace_file,
    finish_progress,
    get_config_dir,
    list_workspace_files,
    load_config,
    print_progress,
    resolve_folder_path,
    safe_filename,
    save_default_config,
)

logger = logging.getLogger("gdsync")


def main():
    config_dir = get_config_dir()
    config = load_config()

    # First-run welcome
    config_path = config_dir / "config.yaml"
    if not config_path.exists():
        save_default_config()
        print(
            f"\n  \U0001f44b Welcome to gdsync v{__version__}!\n"
            f"\n"
            f"  Config created at: {config_path}\n"
            f"  Edit it to change your sync output directory.\n"
        )

    default_output = str(Path(config.get("output_dir", "~/Documents/gdsync")).expanduser())

    parser = argparse.ArgumentParser(
        prog="gdsync",
        description="Sync Google Workspace files from Drive into multiple formats.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=default_output,
        help=f"Output directory (default: {config.get('output_dir', '~/Documents/gdsync')})",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        default=str(config_dir / "credentials.json"),
        help="Path to OAuth credentials JSON",
    )
    parser.add_argument(
        "-t",
        "--token",
        default=str(config_dir / "token.json"),
        help="Path to saved token file",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["docs", "sheets", "slides", "drawings"],
        default=None,
        help="Limit to specific file types (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without downloading",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force a full re-export, ignoring the previous manifest",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed step-by-step output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"gdsync {__version__}",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)

    verbose = args.verbose

    # --- Auth ---
    if not verbose:
        print("\n  \U0001f510 Authenticating...", end="", flush=True)
    creds = authenticate(args.credentials, args.token)
    service = build_service(creds)
    logger.info("Authenticated successfully.")
    if not verbose:
        print(" done.")

    # --- Discover files ---
    if not verbose:
        print("  \U0001f50d Scanning Drive...", end="", flush=True)
    logger.info("Scanning Google Drive for Workspace files...")
    all_files = list_workspace_files(service)
    if not verbose:
        print(f" found {len(all_files)} files.")

    # Filter by type if requested
    type_filter_map = {
        "docs": "application/vnd.google-apps.document",
        "sheets": "application/vnd.google-apps.spreadsheet",
        "slides": "application/vnd.google-apps.presentation",
        "drawings": "application/vnd.google-apps.drawing",
    }
    if args.types:
        allowed = {type_filter_map[t] for t in args.types}
        all_files = [f for f in all_files if f["mimeType"] in allowed]

    logger.info(f"Total files to export: {len(all_files)}")

    if not all_files:
        print("  \U0001f4ed No Workspace files found. Nothing to do.")
        return

    # --- Resolve folder paths ---
    if not verbose:
        print("  \U0001f4c2 Resolving folders...", end="", flush=True)
    logger.info("Resolving Drive folder structure...")
    folder_cache = {}
    file_paths = []
    for file_info in all_files:
        drive_path = resolve_folder_path(service, file_info, folder_cache)
        file_paths.append(drive_path)
    if not verbose:
        print(" done.")

    # --- Dry run ---
    if args.dry_run:
        print(f"\n  \U0001f4cb Dry run — {len(all_files)} files would be exported:\n")
        for f, dp in zip(all_files, file_paths):
            label = TYPE_LABELS.get(f["mimeType"], "?")
            print(f"     {label:8s}  {dp / f['name']}")
        print()
        return

    # --- Export ---
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    exceptions_path = config_dir / "exceptions.yaml"

    # Load exception list
    excepted_ids = set()
    exceptions_data = []
    if exceptions_path.exists():
        try:
            exceptions_data = yaml.safe_load(exceptions_path.read_text()) or []
            for entry in exceptions_data:
                fid = entry.get("id", "")
                if fid:
                    excepted_ids.add(fid)
        except (yaml.YAMLError, OSError) as e:
            logger.warning(f"Could not read exceptions: {e}")
        if excepted_ids and not verbose:
            print(f"  \u23ed\ufe0f  Skipping {len(excepted_ids)} excepted file(s)")
        logger.info(f"Loaded {len(excepted_ids)} file IDs from exceptions.yaml")

    # Load previous manifest for incremental sync
    prev_manifest = {}
    if not args.full and manifest_path.exists():
        try:
            old = json.loads(manifest_path.read_text())
            for entry in old.get("files", []):
                if "modifiedTime" in entry:
                    prev_manifest[entry["id"]] = entry["modifiedTime"]
            logger.info(f"Loaded previous manifest with {len(prev_manifest)} entries.")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load previous manifest: {e}. Doing full export.")

    stats = {"exported": 0, "skipped": 0, "excepted": 0, "errors": 0}
    failures = []
    total = len(all_files)

    # Pre-count what needs to be exported
    to_export = 0
    for file_info in all_files:
        fid = file_info["id"]
        if fid in excepted_ids:
            continue
        if fid in prev_manifest and prev_manifest[fid] == file_info.get("modifiedTime"):
            continue
        to_export += 1

    if prev_manifest and to_export == 0:
        print("\n  \u2705 Everything is up to date.\n")
        return

    if not verbose:
        if prev_manifest:
            print(f"\n  \U0001f4e6 {to_export} file(s) new or modified since last sync.\n")
        else:
            print(f"\n  \U0001f4e6 {to_export} file(s) to export.\n")
        print("  \u2934\ufe0f  Syncing files:")

    for i, (file_info, drive_path) in enumerate(zip(all_files, file_paths), 1):
        file_id = file_info["id"]
        modified = file_info.get("modifiedTime")

        if file_id in excepted_ids:
            logger.debug(f"  Skipping (excepted): {file_info['name']}")
            stats["excepted"] += 1
            if not verbose:
                print_progress(i, total, file_info["name"][:40])
            continue

        if file_id in prev_manifest and prev_manifest[file_id] == modified:
            logger.debug(f"  Skipping (unchanged): {file_info['name']}")
            stats["skipped"] += 1
            if not verbose:
                print_progress(i, total, file_info["name"][:40])
            continue

        logger.info(f"--- File {i}/{len(all_files)} ---")
        if not verbose:
            print_progress(i, total, file_info["name"][:40])
        export_workspace_file(service, file_info, output_dir, drive_path, stats, failures, config)

    if not verbose:
        finish_progress()

    # Print errors below the progress bar and update exceptions.yaml
    if failures:
        new_exceptions = {}
        for f in failures:
            fid = f.get("id", "")
            if fid and fid not in excepted_ids and fid not in new_exceptions:
                new_exceptions[fid] = f

        if not verbose:
            print()
            seen_paths = {}
            for f in failures:
                if f["path"] not in seen_paths:
                    seen_paths[f["path"]] = f["reason"]
            for path, reason in seen_paths.items():
                print(f"  \u274c  {path}")
                print(f"      {reason}")
            print()

        if new_exceptions:
            for fid, info in new_exceptions.items():
                exceptions_data.append(
                    {
                        "id": fid,
                        "name": info["name"],
                        "path": info["path"],
                        "reason": info["reason"],
                    }
                )
                excepted_ids.add(fid)
            exceptions_path.write_text(
                yaml.dump(exceptions_data, default_flow_style=False, sort_keys=False)
            )
            logger.info(f"Added {len(new_exceptions)} new entries to exceptions.yaml")

    # --- Clean up deleted files ---
    current_ids = {f["id"] for f in all_files}
    deleted_ids = set(prev_manifest.keys()) - current_ids
    deleted_count = 0

    if deleted_ids:
        try:
            old = json.loads(manifest_path.read_text())
            old_file_map = {e["id"]: e for e in old.get("files", [])}
        except (json.JSONDecodeError, KeyError):
            old_file_map = {}

        for did in deleted_ids:
            entry = old_file_map.get(did, {})
            old_name = safe_filename(entry.get("name", ""))
            if not old_name:
                continue
            for fmt_dir in output_dir.iterdir():
                if not fmt_dir.is_dir():
                    continue
                for match in fmt_dir.rglob(f"{old_name}.*"):
                    logger.info(f"  Removing deleted: {match.relative_to(output_dir)}")
                    match.unlink()
                    deleted_count += 1

    # --- Summary ---
    ruler = "  " + "\u2500" * 42
    print()
    print(ruler)
    print("  \u2728 Sync complete!")
    print()
    print(f"     \U0001f4c1 Files on Drive      {len(all_files)}")
    print(f"     \u2b07\ufe0f  Exported (new/mod)  {stats['exported']}")
    print(f"     \u23e9 Skipped (no change) {stats['skipped']}")
    print(f"     \u23ed\ufe0f  Excepted (skipped)  {stats['excepted']}")
    print(f"     \U0001f5d1\ufe0f  Deleted             {deleted_count}")
    if stats["errors"]:
        print(f"     \u26a0\ufe0f  Errors              {stats['errors']}")
    else:
        print(f"     \u2705 Errors              {stats['errors']}")
    print()
    print(f"     \U0001f4be {output_dir.resolve()}")
    if excepted_ids:
        n = len(excepted_ids)
        fname = exceptions_path.name
        print()
        print(f"     \U0001f4dd {n} file(s) excepted \u2014 edit {fname} to retry")
    print(ruler)

    # Write updated manifest
    manifest = {
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_files": len(all_files),
        "exports": stats["exported"],
        "skipped": stats["skipped"],
        "errors": stats["errors"],
        "files": [
            {
                "name": f["name"],
                "type": TYPE_LABELS.get(f["mimeType"], "?"),
                "id": f["id"],
                "modifiedTime": f.get("modifiedTime"),
            }
            for f in all_files
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Manifest written to {manifest_path}")

    if not verbose:
        print("\n  \U0001f4e6 Archiving...", end="", flush=True)

    # --- Write failure report ---
    report_path = output_dir / "files-that-cant-be-synced.md"
    if failures:
        seen = {}
        for f in failures:
            key = f["path"]
            if key not in seen:
                seen[key] = {"type": f["type"], "formats": [], "reason": f["reason"]}
            seen[key]["formats"].append(f["format"])

        headers = ["File", "Type", "Failed Formats", "Reason"]
        rows = []
        for path, info in seen.items():
            formats = ", ".join(info["formats"])
            reason = info["reason"].replace("|", "\\|")
            rows.append([str(path), info["type"], formats, reason])

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        def fmt_row(cells):
            padded = [cells[i].ljust(col_widths[i]) for i in range(len(cells))]
            return "| " + " | ".join(padded) + " |"

        separator = "| " + " | ".join("-" * w for w in col_widths) + " |"

        lines = [
            "# Files That Can't Be Synced",
            "",
            f"*Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"{len(seen)} file(s) could not be exported during the most recent sync.",
            "",
            fmt_row(headers),
            separator,
        ]
        for row in rows:
            lines.append(fmt_row(row))

        lines.append("")
        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Failure report written to {report_path}")
    elif report_path.exists():
        report_path.unlink()
        logger.info("All files synced successfully, removed old failure report.")

    # --- Archive ---
    archive_dir = output_dir / ".archives"
    archive_dir.mkdir(parents=True, exist_ok=True)

    max_backups = config.get("max_backups", 5)
    max_archive_bytes = config.get("max_archive_mb", 500) * 1024 * 1024

    # Create the new archive
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    archive_path = archive_dir / f"sync_{timestamp}.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_dir.rglob("*"):
            if file.is_file() and not file.is_relative_to(archive_dir):
                zf.write(file, file.relative_to(output_dir))
    logger.info(f"Archive saved to {archive_path}")

    # Prune old archives — max_archive_mb supersedes max_backups
    archives = sorted(archive_dir.glob("sync_*.zip"), key=lambda p: p.stat().st_mtime)

    def _total_archive_size():
        return sum(a.stat().st_size for a in archives)

    # Remove by count first (keep at most max_backups)
    while len(archives) > max_backups:
        oldest = archives.pop(0)
        print(f"\n  \U0001f5d1\ufe0f  Pruning {oldest.name}")
        print(f"     Backup limit ({max_backups}) reached.")
        print(
            f"     \u2022 To keep more:  increase 'max_backups' in {config_dir.name}/config.yaml"
        )
        print(f'     \u2022 To save first: cp "{oldest}" /path/to/safe/location/')
        oldest.unlink()

    # Remove by size (max_archive_mb supersedes count)
    while len(archives) > 1 and _total_archive_size() > max_archive_bytes:
        oldest = archives.pop(0)
        total_mb = _total_archive_size() / (1024 * 1024)
        limit_mb = max_archive_bytes / (1024 * 1024)
        print(f"\n  \U0001f5d1\ufe0f  Pruning {oldest.name} ({total_mb:.0f}/{limit_mb:.0f} MB)")
        print("     Size limit exceeded.")
        cfg = f"{config_dir.name}/config.yaml"
        print(f"     \u2022 To expand:     increase 'max_archive_mb' in {cfg}")
        print(f'     \u2022 To save first: cp "{oldest}" /path/to/safe/location/')
        oldest.unlink()

    # Warn if within 20% of the size limit
    total_size = _total_archive_size()
    if total_size >= max_archive_bytes * 0.8:
        used_mb = total_size / (1024 * 1024)
        limit_mb = max_archive_bytes / (1024 * 1024)
        pct = total_size / max_archive_bytes * 100
        print(
            f"\n  \u26a0\ufe0f  Archive storage {pct:.0f}% full"
            f" ({used_mb:.0f} MB / {limit_mb:.0f} MB)"
        )
        print("     Oldest archives will be pruned on the next run.")
        cfg = f"{config_dir.name}/config.yaml"
        print(f"     \u2022 To expand:     increase 'max_archive_mb' in {cfg}")
        print(f"     \u2022 To free space: move old archives out of {archive_dir}/")

    if not verbose:
        print(" done.\n")
