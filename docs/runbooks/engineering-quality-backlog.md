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

- CI test matrix aligned to supported Python versions (`3.8`, `3.9`, `3.10`, `3.11`).
- Required-status `unit` summary gate added to enforce full matrix success for branch protection compatibility.
- Lint CI gate added (`markdownlint-cli2` and `ruff check .`).
- Governance essentials added (`LICENSE`, `CONTRIBUTING.md`, `CODEOWNERS`).
- Dependency automation baseline added (`.github/dependabot.yml`).
- Temporary Ruff import-order exceptions are scoped to two legacy test files pending cleanup.

Pending / next-phase quality work remains below.

## Prioritized Backlog

| Priority | Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| P0 | Python matrix CI completion | `implemented` | `tests` workflow runs unit tests on Python `3.8-3.11` for `pull_request` and `push` to `main`. |
| P0 | Lint CI completion | `implemented` | `lint` workflow runs markdown lint and Ruff on every PR and push to `main`. |
| P0 | License + contribution governance | `implemented` | `LICENSE`, `CONTRIBUTING.md`, and `CODEOWNERS` exist and are linked from canonical docs. |
| P0 | Dependabot + dependency hygiene baseline | `implemented` | Dependabot config is valid and weekly grouped updates are enabled for `pip` and `github-actions`. |
| P1 | Remove temporary Ruff per-file ignores | `planned` | Eliminate `.ruff.toml` `I001` per-file ignores by bringing affected legacy tests into import-order compliance. |
| P1 | Security scanning baseline | `planned` | Add lightweight security scan workflow (for example dependency and secret scanning) with documented triage policy. |
| P1 | Release automation hardening | `planned` | Add release/tag validation automation and document failure handling in `RELEASING.md`. |
| P2 | Stricter typing baseline | `planned` | Define incremental typing plan (scope, excludes, gate level) and enable first non-blocking type check pass. |

## Continue Optimization Checklist

1. Confirm current CI checks and governance files still match `TECHNICAL.md`, `README.md`, and `RELEASING.md`.
1. Pick highest-priority `planned` backlog item and define a bounded acceptance criterion.
1. Implement changes with tests/lint/docs updates in the same PR.
1. Update this backlog status and `CHANGELOG.md` `[Unreleased]` entry.
1. Sync `docs/roadmap/shared-roadmap.md` when the quality initiative scope or commitment changes.
