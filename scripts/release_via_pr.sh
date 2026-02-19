#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/release_via_pr.sh X.Y.Z

Expected current branch:
  release/vX.Y.Z

What this script does:
  - runs release checks (`./scripts/release_check.sh`, `make lint-py`, `make lint-md`)
  - pushes the release branch
  - creates a PR to main if needed
  - enables auto-merge for the PR

Notes:
  - This script never pushes to main directly.
  - Tagging and GitHub release creation happen after PR merge.
USAGE
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

version="${1:-}"
if [ -z "${version}" ]; then
  usage >&2
  exit 2
fi

if ! [[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: version must match X.Y.Z" >&2
  exit 2
fi

branch="release/v${version}"
current_branch="$(git branch --show-current)"
if [ "${current_branch}" != "${branch}" ]; then
  echo "ERROR: current branch is '${current_branch}', expected '${branch}'" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: working tree is not clean" >&2
  exit 1
fi

./scripts/release_check.sh
make lint-py
make lint-md

git push -u origin "${branch}"

pr_url="$(gh pr view --json url --jq .url 2>/dev/null || true)"
if [ -z "${pr_url}" ]; then
  pr_url="$(gh pr create --base main --head "${branch}" --title "Release v${version}" --body "Release v${version}")"
fi

echo "PR: ${pr_url}"
gh pr merge --merge --auto --delete-branch

echo "Release PR prepared with auto-merge."
