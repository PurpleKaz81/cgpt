# AI Agent Reference

Last updated: 2026-02-16

## Purpose

Provide deterministic repository guidance so AI agents and automation can operate without inferring undocumented behavior.

## Canonical Source Order

When sources conflict, use this precedence:

1. `TECHNICAL.md` for CLI/runtime behavior and command contracts.
1. `docs/specs/current-capabilities.md` for what is currently shipped.
1. `docs/roadmap/shared-roadmap.md` for future direction and commitment levels.
1. `README.md` for user-facing workflows and onboarding framing.
1. `RELEASING.md` for release process and required checks.

## Current Product Invariants

- Current supported ingestion format is ChatGPT export ZIP data.
- Product is local-first and single-user for `v0.x`.
- Private local configuration should use `config.personal.json` (untracked).
- Output artifacts are context aids, not guaranteed final prompts.

## Repository Landmarks

- `cgpt.py`: CLI entrypoint and command implementation.
- `config.json`: public baseline defaults.
- `tests/`: unit tests and critical-path coverage.
- `scripts/release_check.sh`: release preflight gate.
- `docs/INDEX.md`: required index for scoped docs under `docs/`.

## Operational Commands

Core checks:

```bash
python3 cgpt.py --help
python3 -m unittest discover -s tests -p "test_*.py"
./scripts/release_check.sh
```

Safe git staging pattern (public files only):

```bash
git add cgpt.py README.md TECHNICAL.md CHANGELOG.md SECURITY.md RELEASING.md config.json .gitignore .githooks/pre-commit
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
- Behavior changes in `cgpt.py`, `config.json`, or `requirements.txt` must update at least one core canonical doc.
- Release cadence requires docs review and roadmap status refresh.
- For `CHANGELOG.md` numbered releases, use unique level-3 subsection headings to satisfy markdown lint (for example: `### Added in 0.2.4`, `### Changed in 0.2.4`, `### Fixed in 0.2.4`).

## Agent Guardrails

- Do not present roadmap items as already implemented.
- Do not claim support for non-ChatGPT providers unless capability is moved to `implemented`.
- Prefer updating canonical docs over creating parallel redundant descriptions.
- Do not introduce duplicate sibling headings in `CHANGELOG.md`; preserve the version-qualified heading pattern for release sections.
