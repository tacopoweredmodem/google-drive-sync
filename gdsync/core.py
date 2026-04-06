"""
Core logic for gdsync: authentication, file discovery, export, and archiving.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import markdownify
import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

EXPORT_MAP = {
    "application/vnd.google-apps.document": {
        "markdown": ("text/html", ".md"),
        "pdf": ("application/pdf", ".pdf"),
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
    },
    "application/vnd.google-apps.spreadsheet": {
        "csv": ("text/csv", ".csv"),
        "pdf": ("application/pdf", ".pdf"),
        "xlsx": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
    },
    "application/vnd.google-apps.presentation": {
        "pdf": ("application/pdf", ".pdf"),
        "pptx": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
    },
    "application/vnd.google-apps.drawing": {
        "pdf": ("application/pdf", ".pdf"),
    },
}

TYPE_LABELS = {
    "application/vnd.google-apps.document": "Doc",
    "application/vnd.google-apps.spreadsheet": "Sheet",
    "application/vnd.google-apps.presentation": "Slides",
    "application/vnd.google-apps.drawing": "Drawing",
}

FRIENDLY_ERRORS = {
    "cannotExportFile": (
        "You don't have permission to export this file. "
        "It may be owned by someone else or restricted by your organization."
    ),
    "exportSizeLimitExceeded": (
        "This file is too large for Google to export. "
        "Try opening it in Drive and downloading manually."
    ),
    "notFound": "This file no longer exists or you lost access to it.",
    "rateLimitExceeded": "Too many requests. The script will retry automatically.",
    "dailyLimitExceeded": "You've hit Google's daily API quota. Try again tomorrow.",
}

DEFAULT_CONFIG = {
    "output_dir": "~/Documents/gdsync",
    "rate_limit_delay": 0.2,
    "max_retries": 3,
    "max_backups": 5,
    "max_archive_mb": 500,
}

logger = logging.getLogger("gdsync")


# ---------------------------------------------------------------------------
# Config directory (~/.gdsync/)
# ---------------------------------------------------------------------------


def get_config_dir() -> Path:
    """Return ~/.gdsync/, creating it with restricted permissions if needed."""
    config_dir = Path.home() / ".gdsync"
    if not config_dir.exists():
        config_dir.mkdir(mode=0o700)
    return config_dir


def load_config() -> dict:
    """Load ~/.gdsync/config.yaml, returning defaults for missing keys."""
    config_path = get_config_dir() / "config.yaml"
    config = dict(DEFAULT_CONFIG)
    if config_path.exists():
        try:
            user_config = yaml.safe_load(config_path.read_text()) or {}
            config.update(user_config)
        except (yaml.YAMLError, OSError) as e:
            logger.warning(f"Could not read config: {e}. Using defaults.")
    return config


def save_default_config() -> Path:
    """Write a default config.yaml and return its path."""
    config_path = get_config_dir() / "config.yaml"
    config_path.write_text(yaml.dump(DEFAULT_CONFIG, default_flow_style=False, sort_keys=False))
    return config_path


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------


def print_progress(current: int, total: int, label: str = "", width: int = 30):
    """Print an in-place progress bar to stderr."""
    filled = int(width * current / total) if total else width
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    pct = (current / total * 100) if total else 100
    text = f"\r     {bar} {current}/{total} ({pct:.0f}%)"
    if label:
        text += f"  {label}"
    print(text.ljust(85), end="", file=sys.stderr, flush=True)


def finish_progress():
    """End the progress bar line."""
    print("", file=sys.stderr)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def authenticate(credentials_file: str, token_file: str) -> Credentials:
    """
    Run the OAuth 2.0 flow. On first run, opens a browser for consent.
    Subsequent runs reuse the saved token.
    """
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                config_dir = get_config_dir()
                print(
                    f"\nCredentials file not found: {credentials_file}\n\n"
                    f"To set up gdsync:\n"
                    f"  1. Create OAuth credentials at https://console.cloud.google.com\n"
                    f"  2. Download the JSON and save it as:\n"
                    f"     {config_dir / 'credentials.json'}\n"
                )
                sys.exit(1)
            logger.info("Starting OAuth flow (browser will open)...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(creds.to_json())
        logger.info(f"Token saved to {token_file}")

    return creds


def build_service(creds: Credentials):
    """Build and return a Google Drive v3 service object."""
    return build("drive", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def list_workspace_files(service) -> list[dict]:
    """
    Enumerate all Google Workspace files the authenticated user can access.
    Returns a list of dicts with keys: id, name, mimeType, modifiedTime, parents.
    """
    mime_types = list(EXPORT_MAP.keys())
    query = " or ".join(f"mimeType='{mt}'" for mt in mime_types)

    all_files = []
    page_token = None

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                pageSize=100,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files = response.get("files", [])
        all_files.extend(files)
        logger.info(f"  Found {len(files)} files (total: {len(all_files)})")

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return all_files


def resolve_folder_path(service, file_info: dict, cache: dict) -> Path:
    """
    Walk the parent chain to build the full Drive folder path for a file.
    Results are cached to avoid redundant API calls.
    """
    parents = file_info.get("parents")
    if not parents:
        return Path(".")

    parent_id = parents[0]
    parts = []

    while parent_id:
        if parent_id in cache:
            cached = cache[parent_id]
            if cached is None:
                break
            parts.append(cached)
            parent_id = cache.get(f"{parent_id}__parent")
            continue

        try:
            folder = (
                service.files()
                .get(
                    fileId=parent_id,
                    fields="id, name, parents",
                    supportsAllDrives=True,
                )
                .execute()
            )
        except HttpError:
            cache[parent_id] = None
            break

        folder_parents = folder.get("parents", [])
        next_parent = folder_parents[0] if folder_parents else None

        if not next_parent or next_parent == parent_id:
            cache[parent_id] = None
            break

        folder_name = safe_filename(folder["name"])
        cache[parent_id] = folder_name
        cache[f"{parent_id}__parent"] = next_parent
        parts.append(folder_name)
        parent_id = next_parent

    parts.reverse()
    return Path(*parts) if parts else Path(".")


# ---------------------------------------------------------------------------
# Export and conversion
# ---------------------------------------------------------------------------


def safe_filename(name: str) -> str:
    """Strip or replace characters that cause filesystem problems."""
    name = name.replace("..", "_")
    for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "\x00"]:
        name = name.replace(ch, "_")
    name = name.strip(". ")
    if not name:
        name = "_unnamed"
    if len(name) > 200:
        name = name[:200]
    return name


def _friendly_error(e: HttpError) -> str:
    """Extract a human-readable message from a Google API error."""
    try:
        details = e.error_details  # type: ignore[attr-defined]
        if details:
            reason = details[0].get("reason", "")
            if reason in FRIENDLY_ERRORS:
                return FRIENDLY_ERRORS[reason]
    except (AttributeError, IndexError, KeyError, TypeError):
        pass
    return e._get_reason() or str(e)


def export_file(
    service, file_id: str, mime_type: str, config: dict
) -> tuple[Optional[bytes], str]:
    """
    Export a Google Workspace file to the given MIME type, with retries.
    Returns (data, error_reason). On success error_reason is empty.
    """
    max_retries = config.get("max_retries", 3)
    for attempt in range(1, max_retries + 1):
        try:
            data = service.files().export(fileId=file_id, mimeType=mime_type).execute()
            return data, ""
        except HttpError as e:
            if e.resp.status in (429, 500, 503) and attempt < max_retries:
                wait = 2**attempt
                logger.warning(f"  Retrying in {wait}s (HTTP {e.resp.status})...")
                time.sleep(wait)
            else:
                reason = _friendly_error(e)
                logger.error(f"  {reason}")
                return None, reason
    return None, "Unknown error after retries"


def html_to_markdown(html_bytes: bytes) -> str:
    """Convert HTML content to Markdown."""
    html_str = html_bytes.decode("utf-8", errors="replace")
    return markdownify.markdownify(html_str, heading_style="ATX", strip=["img"])


def export_workspace_file(
    service,
    file_info: dict,
    output_dir: Path,
    drive_path: Path,
    stats: dict,
    failures: list,
    config: dict,
):
    """
    Export a single Workspace file into all applicable formats.
    Preserves the Google Drive folder hierarchy under each format directory.
    """
    file_id = file_info["id"]
    file_name = file_info["name"]
    mime_type = file_info["mimeType"]
    type_label = TYPE_LABELS.get(mime_type, "Unknown")

    export_config = EXPORT_MAP.get(mime_type)
    if not export_config:
        return

    safe_name = safe_filename(file_name)
    display_path = str(drive_path / file_name)
    logger.info(f"[{type_label}] {display_path}")

    rate_delay = config.get("rate_limit_delay", 0.2)

    for format_name, (export_mime, ext) in export_config.items():
        format_dir = output_dir / format_name / drive_path
        format_dir.mkdir(parents=True, exist_ok=True)

        raw, error_reason = export_file(service, file_id, export_mime, config)

        if raw is None:
            stats["errors"] += 1
            failures.append(
                {
                    "id": file_id,
                    "name": file_name,
                    "path": display_path,
                    "type": type_label,
                    "format": format_name,
                    "reason": error_reason,
                }
            )
            continue

        if format_name == "markdown":
            md_content = html_to_markdown(raw)
            out_path = format_dir / f"{safe_name}.md"
            out_path.write_text(md_content, encoding="utf-8")
        else:
            out_path = format_dir / f"{safe_name}{ext}"
            if isinstance(raw, str):
                out_path.write_text(raw, encoding="utf-8")
            else:
                out_path.write_bytes(raw)

        logger.info(f"  -> {format_name}: {out_path.relative_to(output_dir)}")
        stats["exported"] += 1
        time.sleep(rate_delay)
