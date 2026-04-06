#!/usr/bin/env python3
"""
Run all linting, formatting, and tests for the gdsync project.

Usage:
    python scripts/lint.py          # check everything (no changes)
    python scripts/lint.py --fix    # auto-fix and format, then test
"""

import glob
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIX_MD_BREAKS = "scripts/fix_md_breaks.py"
MD_FILES = ["README.md"] + sorted(glob.glob("wiki/*.md"))
PY_DIRS = ["gdsync/", "tests/"]


def run(label: str, cmd: list[str], ok_codes: tuple[int, ...] = (0,)) -> bool:
    print(f"\n{'─' * 50}")
    print(f"  {label}")
    print(f"{'─' * 50}")
    result = subprocess.run(cmd)
    ok = result.returncode in ok_codes
    print(f"  {'✅ passed' if ok else '❌ failed'}")
    return ok


def check_markdown() -> bool:
    """Check markdown by formatting temp copies and comparing to originals."""
    print(f"\n{'─' * 50}")
    print("  markdown (mdformat + thematic breaks)")
    print(f"{'─' * 50}")

    dirty = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for md in MD_FILES:
            src = Path(md)
            dst = tmp / src.name
            shutil.copy2(src, dst)

            # Format the copy
            subprocess.run(["mdformat", str(dst)], capture_output=True)
            text = dst.read_text(encoding="utf-8")
            fixed = re.sub(r"^_{3,}$", "---", text, flags=re.MULTILINE)
            dst.write_text(fixed, encoding="utf-8")

            if src.read_text(encoding="utf-8") != dst.read_text(encoding="utf-8"):
                dirty.append(md)

    if dirty:
        for f in dirty:
            print(f"  would reformat: {f}")
        print("  ❌ failed")
        return False

    print("  ✅ passed")
    return True


def fix_markdown() -> bool:
    """Format all markdown files in place."""
    ok = run("mdformat", ["mdformat", *MD_FILES])
    run(
        "fix thematic breaks",
        [sys.executable, FIX_MD_BREAKS, *MD_FILES],
        ok_codes=(0, 1),
    )
    return ok


def main() -> int:
    fix = "--fix" in sys.argv
    results = []

    if fix:
        results.append(run("ruff lint --fix", ["ruff", "check", "--fix", *PY_DIRS]))
        results.append(run("ruff format", ["ruff", "format", *PY_DIRS]))
        results.append(fix_markdown())
    else:
        results.append(run("ruff lint", ["ruff", "check", *PY_DIRS]))
        results.append(run("ruff format --check", ["ruff", "format", "--check", *PY_DIRS]))
        results.append(check_markdown())

    results.append(run("pytest", ["pytest", "--tb=short", "-q"]))

    print(f"\n{'═' * 50}")
    passed = sum(results)
    total = len(results)
    if all(results):
        print(f"  ✅ All {total} checks passed.")
    else:
        print(f"  ❌ {total - passed}/{total} checks failed.")
    print(f"{'═' * 50}\n")

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
