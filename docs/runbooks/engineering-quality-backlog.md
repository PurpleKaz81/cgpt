# Engineering Quality Backlog

Last updated: 2026-02-17

## Purpose

Provide a durable, public optimization ledger for repository quality work so baseline hardening continues across release cycles and AI/maintainer context resets.

## Operating Model

- Treat this file as the canonical quality-improvement backlog.
- Update status when CI/governance changes merge to `main`.
- Review backlog state during every release review.
- Keep entries implementation-focused with explicit acceptance criteria.

## Current Baseline Status

Implemented in this baseline hardening pass:

- CI unit matrix runs on Python `3.8` through `3.13`, plus cross-platform smoke/unit runs on macOS and Windows.
- Required-status `unit` summary gate enforces full matrix and cross-platform success for branch protection compatibility.
- Lint CI gate is active (`markdownlint-cli2` and `ruff check .`).
- Docs policy gate is active (`docs-guard`) for markdown scope/indexing and code-doc sync enforcement.
- Governance essentials are in place (`LICENSE`, `CONTRIBUTING.md`, `CODEOWNERS`).
- Dependency automation baseline is active (`.github/dependabot.yml`).
- `doctor --dev` preflight checks runtime/developer toolchain health and minimum Node.js major expectations.
- Temporary Ruff import-order exceptions remain scoped to two legacy test files pending cleanup.

Pending / next-phase quality work remains below.

## Prioritized Backlog

| Priority | Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| P0 | Remove temporary Ruff per-file ignores | `planned` | Eliminate `.ruff.toml` `I001` per-file ignores by bringing affected legacy tests into import-order compliance. |
| P0 | Security scanning baseline | `planned` | Add lightweight security scan workflow (dependency and secret scanning) with documented triage policy. |
| P1 | Optional dependency CI split for DOCX paths | `planned` | CI has explicit legs that validate behavior with and without `python-docx`, and docx-only command expectations are covered. |
| P1 | Release automation hardening | `planned` | Add release/tag validation automation and document failure handling in `RELEASING.md`. |
| P2 | Stricter typing baseline | `planned` | Define incremental typing plan (scope, excludes, gate level) and enable first non-blocking type check pass. |

## Continue Optimization Checklist

1. Confirm current CI checks and governance files still match `TECHNICAL.md`, `README.md`, and `RELEASING.md`.
1. Pick highest-priority `planned` backlog item and define a bounded acceptance criterion.
1. Implement changes with tests/lint/docs updates in the same PR.
1. Update this backlog status and `CHANGELOG.md` `[Unreleased]` entry.
1. Sync `docs/roadmap/shared-roadmap.md` when the quality initiative scope or commitment changes.
