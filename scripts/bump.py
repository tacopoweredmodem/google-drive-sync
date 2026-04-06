#!/usr/bin/env python3
"""
Bump the gdsync version in __init__.py and pyproject.toml.

Usage:
    python scripts/bump.py patch    # 0.1.0 → 0.1.1
    python scripts/bump.py minor    # 0.1.0 → 0.2.0
    python scripts/bump.py major    # 0.1.0 → 1.0.0
"""

import re
import sys
from pathlib import Path

INIT_FILE = Path("gdsync/__init__.py")
TOML_FILE = Path("pyproject.toml")

VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def read_version() -> tuple[int, int, int]:
    """Read the current version from __init__.py."""
    text = INIT_FILE.read_text()
    match = VERSION_RE.search(text)
    if not match:
        print(f"❌ Could not find version in {INIT_FILE}")
        sys.exit(1)
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump(major: int, minor: int, patch: int, part: str) -> tuple[int, int, int]:
    """Return the bumped version tuple."""
    if part == "major":
        return major + 1, 0, 0
    elif part == "minor":
        return major, minor + 1, 0
    elif part == "patch":
        return major, minor, patch + 1
    else:
        print(f"❌ Unknown bump type: {part}")
        print("   Use: major, minor, or patch")
        sys.exit(1)


def update_file(path: Path, old_version: str, new_version: str) -> None:
    """Replace the version string in a file."""
    text = path.read_text()
    updated = text.replace(old_version, new_version, 1)
    if text == updated:
        print(f"  ⚠️  No change in {path}")
    else:
        path.write_text(updated)
        print(f"  ✅ {path}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/bump.py [major|minor|patch]")
        return 1

    part = sys.argv[1].lower()
    major, minor, patch = read_version()
    old = f"{major}.{minor}.{patch}"
    new_major, new_minor, new_patch = bump(major, minor, patch, part)
    new = f"{new_major}.{new_minor}.{new_patch}"

    print(f"\n  📦 Bumping version: {old} → {new}\n")

    update_file(INIT_FILE, old, new)
    update_file(TOML_FILE, old, new)

    print("\n  Done. Don't forget to commit and tag:\n")
    print(f"    git add {INIT_FILE} {TOML_FILE}")
    print(f'    git commit -m "bump: v{new}"')
    print(f"    git tag v{new}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
