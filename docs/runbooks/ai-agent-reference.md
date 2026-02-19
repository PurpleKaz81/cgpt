# AI Agent Reference

Last updated: 2026-02-19

## Purpose

Provide deterministic repository guidance so AI agents and automation can operate without inferring undocumented behavior.

## Canonical Source Order

When sources conflict, use this precedence:

1. `TECHNICAL.md` for CLI/runtime behavior and command contracts.
1. `docs/specs/current-capabilities.md` for what is currently shipped.
1. `docs/roadmap/shared-roadmap.md` for future direction and commitment levels.
1. `docs/runbooks/engineering-quality-backlog.md` for quality baseline status and follow-up hardening priorities.
1. `README.md` for user-facing workflows and onboarding framing.
1. `RELEASING.md` for release process and required checks.

## Current Product Invariants

- Current supported ingestion format is ChatGPT export ZIP data.
- Product is local-first and single-user for `v0.x`.
- Private local configuration should use `config.personal.json` (untracked).
- Output artifacts are context aids, not guaranteed final prompts.

## Repository Landmarks

- `cgpt/core/`: runtime helpers for environment, layout, IO, and safety primitives.
- `cgpt/domain/`: conversation normalization, indexing, and dossier processing logic.
- `cgpt/commands/`: CLI command handler implementations.
- `cgpt/cli/`: parser wiring and CLI entrypoint orchestration.
- `cgpt.py`: compatibility shim entrypoint for `python3 cgpt.py ...`.
- `config.json`: public baseline defaults.
- `tests/`: unit tests and critical-path coverage.
- `scripts/release_check.sh`: release preflight gate.
- `docs/INDEX.md`: required index for scoped docs under `docs/`.
- `docs/runbooks/engineering-quality-backlog.md`: canonical quality-improvement ledger.

## Operational Commands

Core checks:

```bash
python3 cgpt.py doctor --dev
make check
tox run -e py,lint
./scripts/release_check.sh
```

## Mandatory Git Workflow (All AI Agents)

These rules are required for every AI-agent change in this repository:

1. Never commit directly to `main`.
1. Create a focused branch per change set (`<type>/<scope>` naming preferred).
1. Keep commits scoped and reviewable; do not mix unrelated concerns.
1. Run `make check` after each meaningful code change.
1. Run local checks before opening or updating a PR: `make check`, `./scripts/release_check.sh`.
1. Open a PR to `main`; do not bypass required checks.
1. Merge only after required checks pass and review conversations are resolved.
1. After merge, sync local `main`, prune remotes, and delete merged local branches.
1. Do not leave stale branches; keep only active PR branches and `main`.

Safe git staging pattern (public files only):

```bash
git add cgpt/ cgpt.py config.json pyproject.toml requirements.txt
git add README.md TECHNICAL.md SECURITY.md CHANGELOG.md RELEASING.md CONTRIBUTING.md LICENSE
git add .github/CODEOWNERS .github/dependabot.yml
git add .github/workflows/tests.yml .github/workflows/docs-guard.yml .github/workflows/lint.yml
git add .ruff.toml .markdownlint.yml .gitignore .githooks/pre-commit
git add docs/INDEX.md docs/specs docs/adr docs/runbooks docs/roadmap
```

## Roadmap Tag Semantics

Status:

- `implemented`: available now.
- `in-progress`: currently being built.
- `planned`: approved next work.
- `experimental`: exploratory.

Commitment:

- `committed`: intended delivery.
- `target`: preferred but movable.
- `exploratory`: no guaranteed delivery.

## Documentation Update Rules

- Any new markdown file under scoped docs must be linked in `docs/INDEX.md`.
- Behavior changes in `cgpt/**/*.py` (including `cgpt.py`), `config.json`, or `requirements.txt` must update at least one core canonical doc.
- Release cadence requires docs review and roadmap status refresh.
- For `CHANGELOG.md` numbered releases, use unique level-3 subsection headings to satisfy markdown lint (for example: `### Added in 0.2.4`, `### Changed in 0.2.4`, `### Fixed in 0.2.4`).

## Agent Guardrails

- Do not present roadmap items as already implemented.
- Do not claim support for non-ChatGPT providers unless capability is moved to `implemented`.
- Prefer updating canonical docs over creating parallel redundant descriptions.
- Do not introduce duplicate sibling headings in `CHANGELOG.md`; preserve the version-qualified heading pattern for release sections.
