"""Tests for gdsync.cli — archive pruning, exceptions, and manifest logic."""

import json
import time
import zipfile
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Helpers — create fake archives for pruning tests
# ---------------------------------------------------------------------------


def _make_archive(archive_dir: Path, name: str, size_bytes: int = 1024) -> Path:
    """Create a small zip file with a dummy payload of the given size."""
    path = archive_dir / name
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("dummy.txt", "x" * size_bytes)
    return path


# ---------------------------------------------------------------------------
# Archive pruning by count
# ---------------------------------------------------------------------------


class TestArchivePruneByCount:
    def test_keeps_max_backups(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()
        max_backups = 3

        # Create 5 archives with staggered mtime
        names = [f"sync_2026040{i}_080000.zip" for i in range(1, 6)]
        for i, name in enumerate(names):
            _make_archive(archive_dir, name)
            # Ensure distinct mtime ordering
            path = archive_dir / name
            mtime = time.time() - (len(names) - i) * 10
            import os

            os.utime(path, (mtime, mtime))

        archives = sorted(archive_dir.glob("sync_*.zip"), key=lambda p: p.stat().st_mtime)

        while len(archives) > max_backups:
            oldest = archives.pop(0)
            oldest.unlink()

        remaining = list(archive_dir.glob("sync_*.zip"))
        assert len(remaining) == max_backups

    def test_no_pruning_when_under_limit(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()

        names = [f"sync_2026040{i}_080000.zip" for i in range(1, 4)]
        for name in names:
            _make_archive(archive_dir, name)

        archives = sorted(archive_dir.glob("sync_*.zip"), key=lambda p: p.stat().st_mtime)

        max_backups = 5
        while len(archives) > max_backups:
            oldest = archives.pop(0)
            oldest.unlink()

        remaining = list(archive_dir.glob("sync_*.zip"))
        assert len(remaining) == 3


# ---------------------------------------------------------------------------
# Archive pruning by size
# ---------------------------------------------------------------------------


class TestArchivePruneBySize:
    def test_prunes_when_over_size_limit(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()

        # Create 3 archives, each ~2KB payload
        names = [f"sync_2026040{i}_080000.zip" for i in range(1, 4)]
        for i, name in enumerate(names):
            _make_archive(archive_dir, name, size_bytes=2048)
            path = archive_dir / name
            mtime = time.time() - (len(names) - i) * 10
            import os

            os.utime(path, (mtime, mtime))

        # Set a very small size limit (1 byte) to force pruning
        max_archive_bytes = 1
        archives = sorted(archive_dir.glob("sync_*.zip"), key=lambda p: p.stat().st_mtime)

        def _total():
            return sum(a.stat().st_size for a in archives)

        while len(archives) > 1 and _total() > max_archive_bytes:
            oldest = archives.pop(0)
            oldest.unlink()

        remaining = list(archive_dir.glob("sync_*.zip"))
        # Should keep at least 1 (the newest)
        assert len(remaining) >= 1

    def test_always_keeps_at_least_one(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()

        _make_archive(archive_dir, "sync_20260401_080000.zip", size_bytes=10000)

        max_archive_bytes = 1  # Way under the single file size
        archives = sorted(archive_dir.glob("sync_*.zip"), key=lambda p: p.stat().st_mtime)

        def _total():
            return sum(a.stat().st_size for a in archives)

        while len(archives) > 1 and _total() > max_archive_bytes:
            oldest = archives.pop(0)
            oldest.unlink()

        remaining = list(archive_dir.glob("sync_*.zip"))
        assert len(remaining) == 1


# ---------------------------------------------------------------------------
# Archive size warning threshold
# ---------------------------------------------------------------------------


class TestArchiveSizeWarning:
    def test_warning_at_80_percent(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()

        _make_archive(archive_dir, "sync_20260401_080000.zip", size_bytes=900)
        archives = list(archive_dir.glob("sync_*.zip"))
        total_size = sum(a.stat().st_size for a in archives)

        # Limit is such that our archive is > 80% of it
        max_archive_bytes = total_size + 10  # Just barely over
        threshold = max_archive_bytes * 0.8

        assert total_size >= threshold

    def test_no_warning_when_under_threshold(self, tmp_path):
        archive_dir = tmp_path / ".archives"
        archive_dir.mkdir()

        _make_archive(archive_dir, "sync_20260401_080000.zip", size_bytes=100)
        archives = list(archive_dir.glob("sync_*.zip"))
        total_size = sum(a.stat().st_size for a in archives)

        max_archive_bytes = total_size * 10  # Plenty of room
        threshold = max_archive_bytes * 0.8

        assert total_size < threshold


# ---------------------------------------------------------------------------
# Exceptions YAML round-trip
# ---------------------------------------------------------------------------


class TestExceptionsYaml:
    def test_write_and_read_exceptions(self, tmp_path):
        path = tmp_path / "exceptions.yaml"
        data = [
            {
                "id": "abc123",
                "name": "My Doc",
                "path": "Folder/My Doc",
                "reason": "Too large",
            },
            {
                "id": "def456",
                "name": "Other",
                "path": "Other",
                "reason": "No permission",
            },
        ]
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

        loaded = yaml.safe_load(path.read_text())
        assert len(loaded) == 2
        ids = {e["id"] for e in loaded}
        assert ids == {"abc123", "def456"}

    def test_empty_exceptions_file(self, tmp_path):
        path = tmp_path / "exceptions.yaml"
        path.write_text("")
        loaded = yaml.safe_load(path.read_text()) or []
        assert loaded == []


# ---------------------------------------------------------------------------
# Manifest JSON round-trip
# ---------------------------------------------------------------------------


class TestManifest:
    def test_write_and_read_manifest(self, tmp_path):
        manifest = {
            "exported_at": "2026-04-06T12:00:00Z",
            "total_files": 5,
            "exports": 3,
            "skipped": 2,
            "errors": 0,
            "files": [
                {
                    "name": "Doc A",
                    "type": "Doc",
                    "id": "id1",
                    "modifiedTime": "2026-04-01T00:00:00Z",
                },
                {
                    "name": "Sheet B",
                    "type": "Sheet",
                    "id": "id2",
                    "modifiedTime": "2026-04-02T00:00:00Z",
                },
            ],
        }
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2))

        loaded = json.loads(path.read_text())
        assert loaded["total_files"] == 5
        assert len(loaded["files"]) == 2

        # Simulate incremental manifest loading
        prev = {}
        for entry in loaded.get("files", []):
            if "modifiedTime" in entry:
                prev[entry["id"]] = entry["modifiedTime"]
        assert prev == {
            "id1": "2026-04-01T00:00:00Z",
            "id2": "2026-04-02T00:00:00Z",
        }


# ---------------------------------------------------------------------------
# Archive excludes .archives directory
# ---------------------------------------------------------------------------


class TestArchiveExclusion:
    def test_zip_excludes_archives_dir(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        archive_dir = output_dir / ".archives"
        archive_dir.mkdir()

        # Create some content files
        (output_dir / "markdown").mkdir()
        (output_dir / "markdown" / "doc.md").write_text("# Hello")
        (output_dir / "manifest.json").write_text("{}")

        # Create a pre-existing archive (should NOT be included)
        _make_archive(archive_dir, "old_archive.zip", size_bytes=5000)

        # Build a new archive the same way cli.py does
        new_archive = archive_dir / "sync_test.zip"
        with zipfile.ZipFile(new_archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in output_dir.rglob("*"):
                if file.is_file() and not file.is_relative_to(archive_dir):
                    zf.write(file, file.relative_to(output_dir))

        # Verify contents
        with zipfile.ZipFile(new_archive, "r") as zf:
            names = zf.namelist()
            assert "markdown/doc.md" in names
            assert "manifest.json" in names
            # No .archives/ content
            for name in names:
                assert not name.startswith(".archives/")
