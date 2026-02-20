#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "❌ $1" >&2
  exit 1
}

echo "== cgpt release preflight =="

# 1) Git tree state
if [[ -n "$(git status --porcelain)" ]]; then
  fail "Working tree is not clean. Commit/stash changes before release."
fi
echo "✅ Working tree is clean"

# 2) Basic CLI health
python3 cgpt.py --version >/dev/null || fail "cgpt.py --version failed"
python3 cgpt.py --help >/dev/null || fail "cgpt.py --help failed"
python3 cgpt.py project --help >/dev/null || fail "project --help failed"
python3 cgpt.py extract --help >/dev/null || fail "extract --help failed"
python3 cgpt.py recent --help >/dev/null || fail "recent --help failed"
python3 cgpt.py quick --help >/dev/null || fail "quick --help failed"
python3 cgpt.py build-dossier --help >/dev/null || fail "build-dossier --help failed"
python3 cgpt.py make-dossiers --help >/dev/null || fail "make-dossiers --help failed"
python3 cgpt.py search --help >/dev/null || fail "search --help failed"
python3 cgpt.py doctor --help >/dev/null || fail "doctor --help failed"
python3 cgpt.py doctor >/dev/null || fail "doctor failed"
echo "✅ CLI smoke checks passed"

# 3) Test suite
python3 -m unittest discover -s tests -p 'test_*.py' >/dev/null || fail "Unit tests failed"
echo "✅ Unit tests passed"

# 4) Python lint
if ! make lint-py >/dev/null; then
  fail "Python lint failed (run: make lint-py)"
fi
echo "✅ Python lint passed"

# 5) Changelog has unreleased section
if ! rg -n '^## \[Unreleased\]' CHANGELOG.md >/dev/null; then
  fail "CHANGELOG.md is missing an [Unreleased] section"
fi
echo "✅ CHANGELOG.md has [Unreleased] section"

# 6) Defensive private file check (staged + tracked)
if git ls-files | rg -e '(^|/)config\.personal\.json$' -e '\.private\.json$' >/dev/null; then
  fail "Private config file is tracked in git"
fi
echo "✅ No tracked private config files"

# shellcheck disable=SC2028
echo "\n🎉 Release preflight passed"
