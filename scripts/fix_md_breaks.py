#!/usr/bin/env python3
"""Replace mdformat's underscore thematic breaks with GFM-style dashes."""

import re
import sys
from pathlib import Path


def fix_file(path: Path) -> bool:
    """Fix thematic breaks in a single file. Returns True if changed."""
    text = path.read_text(encoding="utf-8")
    fixed = re.sub(r"^_{3,}$", "---", text, flags=re.MULTILINE)
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file() and fix_file(path):
            changed.append(path.name)
    if changed:
        print(f"  Fixed thematic breaks in: {', '.join(changed)}")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
