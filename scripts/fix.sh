#!/usr/bin/env bash
# Fix all lint/format issues in one shot.
# Usage: bash scripts/fix.sh

set -e
cd "$(git rev-parse --show-toplevel)"

echo ""
echo "  🔧 Fixing Python..."
ruff check --fix gdsync/ tests/ scripts/ 2>/dev/null || true
ruff format gdsync/ tests/ scripts/

echo ""
echo "  🔧 Fixing Markdown..."
python scripts/format_md.py README.md wiki/*.md

echo ""
echo "  ✅ All fixed. Ready to commit."
echo ""
