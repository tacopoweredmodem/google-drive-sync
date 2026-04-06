#!/usr/bin/env python3
"""Format markdown files: mdformat + GFM thematic break fix in one pass."""

import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    files = [f for f in sys.argv[1:] if Path(f).is_file()]
    if not files:
        return 0

    # Run mdformat
    result = subprocess.run(["mdformat", *files])
    if result.returncode != 0:
        return result.returncode

    # Fix thematic breaks (mdformat uses ___, GFM convention is ---)
    for f in files:
        path = Path(f)
        text = path.read_text(encoding="utf-8")
        fixed = re.sub(r"^_{3,}$", "---", text, flags=re.MULTILINE)
        if fixed != text:
            path.write_text(fixed, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
