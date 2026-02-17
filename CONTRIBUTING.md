# Contributing

Thanks for contributing to `cgpt`.

## Development Prerequisites

- Python `3.8` through `3.11` (CI-tested baseline)
- `pip`
- Node.js `20+` (for markdown lint tooling)

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install ruff==0.9.10
npm install --global markdownlint-cli2@0.16.0
```

## Required Local Checks

Run these from the repository root before opening or updating a PR:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
ruff check .
markdownlint-cli2 "**/*.md" "#node_modules"
./scripts/release_check.sh
```

## Documentation Policy

This repo keeps a strict docs contract:

- Core behavior docs are `README.md`, `TECHNICAL.md`, `SECURITY.md`, `CHANGELOG.md`, and `RELEASING.md`.
- Governance docs are `CONTRIBUTING.md` and `LICENSE`.
- Supplemental docs are scoped to `docs/specs/`, `docs/adr/`, `docs/runbooks/`, and `docs/roadmap/`.
- Every scoped markdown file must be linked from `docs/INDEX.md`.

When behavior changes, update docs in the same PR.

## Security and Privacy Guardrails

- Chat export data can contain sensitive personal information.
- Never commit private local files (`config.personal.json`, `*.private.json`) or raw user export artifacts.
- Keep generated/local export data in ignored folders (`zips/`, `extracted/`, `dossiers/`) unless explicitly asked otherwise.
- Follow `SECURITY.md` for data handling practices.

## Pull Request Expectations

- Keep scope explicit and reviewable.
- Include or update tests for behavior changes.
- Keep lint checks green (`ruff`, markdown lint, CI workflows).
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible or maintainer-relevant changes.
- Sync roadmap/spec/runbook docs when priorities or maintenance practices change.
