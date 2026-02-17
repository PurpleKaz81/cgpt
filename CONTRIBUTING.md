# Contributing

Thanks for contributing to `cgpt`.

## Runtime vs Contributor Requirements

- End-user runtime: Python `3.8+`, no required third-party runtime deps for TXT/MD flows.
- Optional runtime feature: DOCX export requires `python-docx`.
- Contributor tooling (only for development/PR checks): `ruff`, `tox`, Node.js `20+` for markdown lint.

## Local Setup (Contributors)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
git config --local core.hooksPath .githooks
```

Optional DOCX dependency for local feature testing:

```bash
python -m pip install -e ".[docx]"
```

## Required Local Checks

Run these from repository root before opening/updating a PR:

```bash
make check
./scripts/release_check.sh
```

Equivalent commands:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 -m ruff check .
npx --yes markdownlint-cli2@0.16.0 "**/*.md" "#node_modules" "#.venv" "#.tox"
```

Matrix/dev convenience:

```bash
tox run -e py,lint
python3 cgpt.py doctor --dev
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
- Keep the pre-commit hook enabled to block accidental staging of private configs, secrets, and export artifacts.
- Follow `SECURITY.md` for data handling practices.

## Pull Request Expectations

- Keep scope explicit and reviewable.
- Include or update tests for behavior changes.
- Keep lint checks green (`ruff`, markdown lint, CI workflows).
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible or maintainer-relevant changes.
- Sync roadmap/spec/runbook docs when priorities or maintenance practices change.
