# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Maintenance note for markdown lint:

- In numbered release sections, keep level-3 subsection headings unique (for example: `### Added in 0.2.4`, `### Changed in 0.2.4`, `### Fixed in 0.2.4`).

## [Unreleased]

### Added

- Added planned feature spec `docs/specs/v0.2.20-split-audit.md` for a new `split-audit` command to verify suspicious removals between split raw and working TXT outputs.

### Changed

- Synced roadmap/capabilities/technical/readme docs to track split-output integrity audit as roadmap item `R17` (planned, not yet shipped).
- Added a temporary troubleshooting workflow in `TECHNICAL.md` for fast manual split-output triage (`raw.txt` vs `__working.txt`) until `R17 split-audit` is implemented.

## [0.2.19] - 2026-02-19

### Added in 0.2.19

- Added root `AGENTS.md` with non-negotiable agent guardrails for PR-first delivery and canonical Ruff invocation.
- Added `.githooks/pre-push` to block direct pushes to protected `main` when local hooks are enabled.
- Added `scripts/release_via_pr.sh` to automate PR-based release preparation without direct `main` pushes.

### Changed in 0.2.19

- Updated release workflow docs to enforce branch -> PR -> merge -> tag flow and removed direct `main` push instructions.
- Updated contributor and agent references to standardize Python lint usage on `make lint-py` (with `.venv` fallback), avoiding unreliable bare `python3 -m ruff` assumptions.
- Hardened docs-guard CI checks to enforce canonical Ruff command guidance and forbid direct-push-to-main release instructions.
- `scripts/release_check.sh` now runs Python lint (`make lint-py`) as part of release preflight.

## [0.2.18] - 2026-02-19

### Added in 0.2.18

- Added regression coverage ensuring `quick --root <path>` and `recent --root <path>` do not mutate latest-pointer state (`extracted/latest`, `extracted/LATEST.txt`).

### Changed in 0.2.18

- `quick`/`recent` now skip latest-pointer refresh and extraction side effects when `--root` is explicitly provided.
- Synced architecture/security references across `TECHNICAL.md`, `SECURITY.md`, and `docs/runbooks/ai-agent-reference.md` with the modular runtime and current hardening env vars.
- Split oversized dossier command/cleaning modules into focused helper modules while preserving existing CLI behavior and command flags.

## [0.2.17] - 2026-02-19

### Added in 0.2.17

- Added regression coverage ensuring `search --root <path>` ignores cached index rows built from a different export root.

### Changed in 0.2.17

- Search now uses SQLite FTS only when index metadata confirms the index was built for the same requested root; mismatched scope falls back to root-local JSON scanning.
- Index metadata now stores the indexed export root and clears stale rows when rebuilding against a different root (or when migrating legacy metadata-free indexes).
- Refactored parser command wiring for `build-dossier`/`quick`/`recent` aliases into shared helper configuration to reduce duplication risk.
- Refactored shared dossier command setup (`build-dossier`, `quick`, `recent`) into reusable option and conversation-loading helpers.
- Refactored split working-TXT transformation into a dedicated pipeline helper with explicit fail-fast behavior for pipeline errors.
- Updated technical/capability/roadmap/quality-ledger docs to reflect shipped index-scope integrity behavior.

### Fixed in 0.2.17

- Fixed cross-export search mismatches caused by stale global index data being reused for a different `--root`.
- Fixed unnecessary message-blob construction during title-only quick/search paths.

## [0.2.16] - 2026-02-19

### Added in 0.2.16

- Added CLI critical-path regression tests covering `find`, `search`, `index`, `latest-zip`, default no-subcommand extract behavior, and default mode/split environment handling.
- Added edge-case coverage confirming `recent` treats `@file` tokens from stdin as raw IDs (matching existing non-include semantics).

### Changed in 0.2.16

- Refactored shared `quick`/`recent` setup and selection flows in `cgpt/commands/dossier.py` to reduce duplication while preserving CLI behavior.
- Centralized markdown-to-plain-text conversion in `cgpt/domain/dossier_builder.py` and reused it in dossier generation paths.
- Updated staging/release documentation commands to stage modular package files (`cgpt/`) explicitly alongside `cgpt.py`.
- Synced capability/roadmap/quality-backlog documentation language with the current CI quality-gate baseline and planned context-quality initiative scope.
- Clarified maintainer docs policy text to treat behavior changes under `cgpt/**/*.py` (including `cgpt.py`) as docs-impacting changes.

### Fixed in 0.2.16

- Fixed docs-guard workflow behavior-change matching to include `cgpt/**/*.py` runtime files instead of only `cgpt.py`.
- Fixed release-process version-source guidance to use `cgpt/core/constants.py` (`__version__`) with `pyproject.toml` dynamic mapping.
- Fixed explicit transaction ordering in `index --reindex` so table clears run inside one opened transaction.
- Fixed cross-platform test robustness by normalizing extracted-path assertions on Windows and keeping new test annotations compatible with Python 3.8.

## [0.2.15] - 2026-02-18

### Added in 0.2.15

- Added `scripts/gh_retry.sh` to retry transient `gh`/GitHub API failures with bounded exponential backoff.

### Changed in 0.2.15

- Hardened lint consistency by removing temporary test-file import-order ignores and aligning CI lint tooling install with `.[dev]`.
- Applied behavior-preserving quality cleanups across modular package code (exception/context handling, minor typing/loop simplifications, and import/export normalization) while keeping CLI behavior unchanged.
- Documented resilient `gh` command usage in maintainer/contributor docs (`RELEASING.md`, `CONTRIBUTING.md`).

### Fixed in 0.2.15

- Fixed Dependabot schema validation by switching schedule timezone values from `UTC` to valid IANA `Etc/UTC`.
- Fixed overlapping `.env` glob patterns in `.githooks/pre-commit` that triggered ShellCheck warnings (`SC2221`, `SC2222`) without changing block behavior.

## [0.2.14] - 2026-02-18

### Changed in 0.2.14

- Cleaned up modular package imports and symbol wiring so Ruff lint passes across `cgpt/` modules with no CLI behavior change.
- Tightened package export surface in `cgpt/__init__.py` with explicit re-exports and `__all__`.

### Fixed in 0.2.14

- Fixed modular cross-module references that caused undefined-name lint failures in indexing and dossier builders.
- Fixed packaging dynamic-version resolution to read from `cgpt.core.constants.__version__`, avoiding build backend import collisions between `cgpt.py` and the `cgpt` package.

## [0.2.13] - 2026-02-18

### Changed in 0.2.13

- Modularized the runtime into package layers (`cgpt/core`, `cgpt/domain`, `cgpt/commands`, `cgpt/cli`) while preserving existing CLI behavior.
- Switched installed console entrypoint to `cgpt.cli:main` and kept `cgpt.py` as a compatibility shim for `python3 cgpt.py ...` workflows.
- Updated technical/capability/roadmap/quality-ledger docs to reflect the shipped modular baseline and to clear roadmap notes that previously treated modularization as pending.

## [0.2.12] - 2026-02-18

### Changed in 0.2.12

- Rolled dossier-generation behavior back to the pre-redaction baseline from `0.2.9` (removed `--redact`/`--no-redact`/`--redact-review` and redaction-stage processing from write commands).
- Updated product documentation to reflect that privacy redaction is not currently shipped and is tracked again as planned critical roadmap scope (`R2`) for post-modular implementation.

### Fixed in 0.2.12

- Eliminated redaction-review false-positive prompt path by removing the shipped redaction pipeline pending modular redesign.

## [0.2.11] - 2026-02-18

### Fixed in 0.2.11

- Reduced false-positive `person_name` redaction matches by filtering title-cased UI/product noun phrases (for example `Privacy Portal`) from ambiguous-name detection.
- Added regression coverage in `tests/test_redaction_incremental.py` to ensure non-person UI phrases are not queued as `person_name` candidates.

## [0.2.10] - 2026-02-18

### Added in 0.2.10

- Added safe-by-default redaction for dossier-producing commands with new flags: `--redact`, `--no-redact`, `--redact-review`, `--redact-profile`, and `--redact-store`.
- Added incremental private redaction memory at `dossiers/.redaction/state.v1.json` with strict schema validation and fingerprint-only persistence.
- Added machine-readable redaction report emission as `<base>__redaction_report.json`.
- Added `CGPT_DEFAULT_REDACT` environment default support.
- Added `tests/test_redaction_incremental.py` for incremental-memory, non-interactive review guard, and cross-conversation placeholder consistency coverage.

### Changed in 0.2.10

- Refactored `make-dossiers` into build -> shared-redaction-session -> write flow so repeated sensitive values across selected conversations map to consistent placeholders in one run.
- Updated docs (`README.md`, `TECHNICAL.md`, `SECURITY.md`, `docs/specs/current-capabilities.md`, `docs/roadmap/shared-roadmap.md`) to reflect shipped redaction behavior and roadmap status.

## [0.2.9] - 2026-02-18

### Changed in 0.2.9

- Strengthened `README.md` opening to a concise three-line public-facing pitch that frames `cgpt` as a local build system for reusable AI context artifacts.
- Elevated "context continuity over transcript cleanup" language in `README.md` to make product differentiation explicit.
- Rewrote the problem statement in `docs/specs/product-vision.md` to explicitly describe the long-term memory gap in current AI chat products.

## [0.2.8] - 2026-02-17

### Changed in 0.2.8

- Tightened roadmap structure in `docs/roadmap/shared-roadmap.md` by separating shipped baseline initiatives from not-yet-shipped work.
- Corrected roadmap status drift by marking shipped initiatives `R4` (`doctor`) and `R16` (engineering quality baseline) as `implemented`.
- Added necessity-ranked roadmap ordering for active initiatives and derived trimester execution plan by rank.
- Updated `R15` phase timing from past version placeholders to active trimester targets.
- Synced `docs/specs/current-capabilities.md` with shipped `doctor` workflow coverage and current CI validation baseline.
- Synced `docs/runbooks/engineering-quality-backlog.md` baseline details with current CI/docs-guard/lint/governance state and reprioritized remaining quality tasks.
- Updated `README.md` near-term roadmap note to reflect ranked delivery priorities (`R2`, `R3`, `R5`).

## [0.2.7] - 2026-02-17

### Changed in 0.2.7

- `doctor --dev` now validates Node.js major version and warns when it is below `20`.
- Added explicit AI-assisted contributor guidance: run `make check` after each meaningful change set and use `./scripts/release_check.sh` before PR updates.
- Updated contributor/agent references to explain what `pyproject` extras, `make check`, `ruff`, `npx markdownlint`, `tox`, and `doctor --dev` are for.

## [0.2.6] - 2026-02-17

### Added in 0.2.6

- Added `doctor` command to validate runtime setup (`python`, home layout, optional DOCX dependency) with optional `--fix`, `--dev`, and `--strict` modes.
- Added Python packaging metadata (`pyproject.toml`) with console entry point `cgpt` and optional extras: `docx`, `dev`.
- Added contributor automation files: `Makefile` (`make check`) and `tox.ini` (`tox run -e py,lint`).
- Added new CLI tests for `doctor` command behavior.

### Changed in 0.2.6

- Updated CI test matrix to include Python `3.12` and `3.13`, plus macOS/Windows smoke+unit runs.
- Updated lint workflow to run pinned markdown lint via `npx` (no global install) and Python lint via `python -m ruff`.
- Updated markdown lint commands to exclude `#.venv` and `#.tox` so local contributor checks do not fail on tool-managed markdown files.
- Updated docs (`README.md`, `TECHNICAL.md`, `CONTRIBUTING.md`, `RELEASING.md`) to separate end-user runtime needs from contributor tooling requirements.
- Clarified `requirements.txt` to reflect zero mandatory third-party runtime dependencies for base TXT/MD flows.

## [0.2.5] - 2026-02-17

### Changed in 0.2.5

- Hardened `.githooks/pre-commit` to block force-staged sensitive export/data artifacts under `zips/`, `extracted/`, and `dossiers/` (except tracked `.gitkeep` placeholders).
- Extended pre-commit checks to block common secret/credential filename patterns (for example `.env*`, `*.key`, `*.pem`) as defense in depth.
- Added local hygiene ignore patterns for common tooling artifacts in `.gitignore` (`.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `coverage.xml`, `htmlcov/`).
- Updated `README.md`, `SECURITY.md`, and `CONTRIBUTING.md` to reflect the stricter commit guardrails and hook activation guidance.
- Added mandatory AI-agent workflow rules in `docs/runbooks/ai-agent-reference.md` so branch usage, PR flow, checks, and post-merge cleanup are always enforced.

## [0.2.4] - 2026-02-17

### Changed in 0.2.4

- Clarified product identity positioning in `README.md` and `docs/specs/product-vision.md` to emphasize continuity, deterministic context builds, and handoff reliability.
- Added roadmap initiative `R15` in `docs/roadmap/shared-roadmap.md` to package Quality Gates as one planned, committed reliability feature family with phased scope.
- Synced GitHub repository About description to the new one-line positioning: local-first context compiler for reusable AI working-memory dossiers.
- Expanded `.github/workflows/tests.yml` to run the `unit` test job across Python `3.8`, `3.9`, `3.10`, and `3.11`.
- Added `.github/workflows/lint.yml` with repository markdown lint (`markdownlint-cli2`) and Python lint (`ruff check .`) gates.
- Added baseline governance and ownership surfaces: `LICENSE` (MIT), `CONTRIBUTING.md`, `.github/CODEOWNERS`, and `.github/dependabot.yml`.
- Added `docs/runbooks/engineering-quality-backlog.md` and synchronized docs (`README.md`, `TECHNICAL.md`, `RELEASING.md`, `docs/INDEX.md`, `docs/runbooks/ai-agent-reference.md`, `docs/roadmap/shared-roadmap.md`) to keep quality-maintenance contracts durable.
- Added a required `unit` summary gate in `.github/workflows/tests.yml` while keeping Python execution in `unit-matrix`, so branch protection can require a stable check name.
- Cleaned up existing markdown lint blockers by making test-matrix headings unique in `docs/specs/v0.2.2-remainder-hardening.md` and `docs/specs/v0.2.3-hardening-followups.md`.
- Applied Ruff follow-up remediation in `cgpt.py` (unused locals and import ordering), and scoped temporary `I001` per-file ignores to two legacy test files in `.ruff.toml`.
- Synced docs terminology around behavior docs vs governance docs and refreshed explicit staging command examples in `README.md` and `RELEASING.md`.

## [0.2.3] - 2026-02-16

### Added in 0.2.3

- Added `v0.2.3` hardening tests in `tests/test_edge_case_hardening.py` covering:
  - ZIP special-member and archive limit validation
  - strict missing-file handling for `--patterns-file` and `--used-links-file`
  - config schema validation for unknown keys and wrong-typed values
  - duplicate conversation ID detection in map-building paths
  - bounded JSON discovery candidate parsing

### Changed in 0.2.3

- ZIP extraction now enforces member-count and total uncompressed-size limits and rejects symlink/special ZIP entries.
- Conversations JSON discovery now uses bounded per-priority candidate shortlists to reduce scaling costs on large trees.
- `build-dossier`/`quick`/`recent` now fail fast when explicit optional file flags reference missing files.
- Updated `README.md`, `TECHNICAL.md`, `docs/specs/current-capabilities.md`, and roadmap status for the `v0.2.3` hardening pass.
- Working-index generation now coerces malformed conversation `create_time` values before sorting/scoring math.
- Config loading now validates schema (unknown keys and wrong-typed fields fail explicitly).
- Duplicate conversation IDs in export input now fail fast instead of silently overwriting map entries.

## [0.2.2] - 2026-02-16

### Added in 0.2.2

- Added remaining-edge hardening tests in `tests/test_edge_case_hardening.py` covering:
  - same-stem re-extraction stale-file cleanup
  - message-level timestamp coercion resilience
  - conversations JSON discovery robustness
  - `--context` bounds validation
  - `--name` normalized-slug validation

### Changed in 0.2.2

- Extraction now uses a temporary target and replace flow so repeated extraction of the same ZIP stem does not keep stale files.
- Conversations JSON discovery now uses conversation-aware candidate selection instead of generic largest-JSON fallback.
- `--context` now enforces a bounded range (`0..200`) across dossier-producing commands.
- Updated `README.md`, `TECHNICAL.md`, `docs/specs/current-capabilities.md`, and roadmap status for `v0.2.2` hardening.

### Fixed in 0.2.2

- Message extraction now coerces malformed message `create_time` values to `0.0` instead of failing silently via exception fallbacks.
- `--name` now fails fast when normalization yields an empty/unsafe slug, avoiding accidental writes to the root dossier directory.

## [0.2.1] - 2026-02-16

### Added in 0.2.1

- Added edge-case hardening test suite at `tests/test_edge_case_hardening.py` covering:
  - ZIP extraction safety checks
  - `quick --and` scope semantics
  - invalid timestamp handling
  - strict config error behavior
  - UTF-8-family input-file decoding

### Changed in 0.2.1

- `extract`/`quick`/`recent` now apply ZIP member safety validation before extraction writes.
- File-based CLI inputs for IDs/patterns/used-links now use UTF-8-family decoding with explicit failure messages.
- Updated `README.md`, `TECHNICAL.md`, `docs/specs/current-capabilities.md`, and roadmap status for the hardening bundle.

### Fixed

- Fixed `quick --and` behavior for `--where messages` and `--where all`.
- Fixed recency/day filtering crashes on malformed `create_time` values by coercing invalid values to `0.0` with warning summaries.
- Removed silent config-extension swallowing in `quick`/`build-dossier`; explicit `--config` failures now fail fast.

## [0.2.0] - 2026-02-16

### Added in 0.2.0

- Added a structured documentation architecture for users and AI agents:
  - `docs/specs/product-vision.md` (mission, posture, non-goals)
  - `docs/specs/current-capabilities.md` (implemented behavior and limits)
  - `docs/roadmap/shared-roadmap.md` (trimester planning with `status`, `commitment`, `horizon` tags)
  - `docs/runbooks/ai-agent-reference.md` (deterministic agent context and guardrails)
- Updated `README.md` and `TECHNICAL.md` to use the new canonical vision/capability/roadmap sources and avoid duplicate roadmap status models.
- Updated `RELEASING.md` checklist to require roadmap and capability documentation review at each release.
- Consolidated release documentation into a single maintainer guide: `RELEASING.md`
- Removed redundant, version-specific release docs (`RELEASE_NOTES.md`, `RELEASE_INSTRUCTIONS.md`)
- Rewrote `README.md` with corrected command examples, folder requirements, and step-by-step usage
- Rewrote `SECURITY.md` to match current `.gitignore` behavior (`.gitkeep` tracked, real contents ignored)
- Added CI docs guard (`.github/workflows/docs-guard.yml`) to enforce:
  - minimal markdown set
  - markdown updates when code/config files change
- `build-dossier` now supports `--config` and `--used-links-file` like alias `d`
- `build-dossier` now honors global default mode resolution (`--default-mode` / `CGPT_DEFAULT_MODE`)
- `build-dossier` no longer requires topics when running in `full` mode
- `make-dossiers` now emits explicit warnings for output-write failures instead of silently swallowing errors
- `make-dossiers --format` now strictly writes only explicitly requested formats (no implicit Markdown sidecar)
- Combined dossier commands now fail clearly when no requested output can be generated (for example docx-only without `python-docx`) instead of printing a non-existent fallback path
- Updated `make-dossiers` CLI help and docs to reflect strict format behavior and current `init`-first workflow guidance
- Unified roadmap documentation across `README.md` and `TECHNICAL.md` with one prioritized implementation queue, status split (`Planned (Committed)` vs `Proposed Enhancement`), and explicit implementation order
- Expanded docs guard policy to allow scoped `docs/` markdown (`specs`, `adr`, `runbooks`, `roadmap`) with required indexing in `docs/INDEX.md` while keeping code-doc sync tied to core docs
- Added a small automated CLI critical-path test suite (`tests/test_cli_critical_paths.py`) and CI workflow (`.github/workflows/tests.yml`)
- Replaced tracked `config.json` content with a neutral public-safe baseline for shared usage
- Added private-config protection patterns to `.gitignore` (`config.personal.json`, `*.private.json`, etc.)
- Added local commit safety hook at `.githooks/pre-commit` to block private config files from being committed
- Documented one-repo public/private workflow and safe pull/merge/push routine in `README.md`
- Updated `SECURITY.md` and `RELEASING.md` with private config and hook guidance
- Added opt-in split default via `CGPT_DEFAULT_SPLIT` with `--no-split` per-command override
- Added `quick --recent N` / `q --recent N` and `quick --days N` / `q --days N` to combine keyword matching with recency windows in one command
- Updated README roadmap to explicitly separate implemented features from remaining planned features
- Split docs by audience: `README.md` is now user-first and `TECHNICAL.md` is now the canonical command and behavior reference
- Updated docs policy and docs guard to include `TECHNICAL.md` in the allowed markdown set
- Expanded docs completeness pass: rewrote `README.md` as an idiot-proof beginner guide with visual flows and copy/paste workflows; expanded `TECHNICAL.md` to cover full command/flag surface
- Added `scripts/release_check.sh` one-command release preflight and documented it in `RELEASING.md`
- Added `init` command to create/verify required home folders (`zips/`, `extracted/`, `dossiers/`)
- Fixed `quick --ids-file` crash caused by selection parser scope (`UnboundLocalError`)

## [0.1.0] - 2026-02-10

### Added in 0.1.0

- Initial release of cgpt - ChatGPT Export → Clean Dossier tool
- Extract ChatGPT conversation exports from ZIP files
- Interactive conversation selection with browse and search capabilities
- Build clean, organized research dossiers from conversations
- Two-file output: full transcript + cleaned working file for ChatGPT
- Support for organizing dossiers into project folders with `--name` flag
- Automatic cleanup of tool noise, citations, and duplicates
- Source organization and categorization
- Navigation index generation for large dossiers
- Multiple search modes: recent conversations, keyword search, content search
- Advanced filtering with custom configuration support
- Export formats: plain text, Markdown, and DOCX (requires python-docx)
- SQLite-based search index with FTS5 support
- Comprehensive CLI with short aliases for common commands
- Interactive selection with ranges and multiple inputs

### Features

- **Extract Command**: Extract ChatGPT ZIP exports
- **Recent Command**: Browse and select from recent conversations
- **Quick Command**: Search by keyword and select conversations
- **Build-Dossier Command**: Create combined dossiers from specific conversation IDs
- **List IDs Command**: View all conversation IDs with filtering
- **Search Command**: Full-text search in titles and content

### Configuration

- Customizable filtering with config.json
- Research-focused default configuration included
- Support for deliverable pattern extraction
- Source URL prioritization

### Documentation

- Comprehensive README with quick start guide
- Command reference and cheat sheet
- FAQ and troubleshooting section
- Common mistakes and fixes guide

[0.2.17]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.17
[0.2.16]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.16
[0.2.15]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.15
[0.2.14]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.14
[0.2.13]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.13
[0.2.12]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.12
[0.2.11]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.11
[0.2.10]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.10
[0.2.9]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.9
[0.2.8]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.8
[0.2.7]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.7
[0.2.6]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.6
[0.2.5]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.5
[0.2.4]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.4
[0.2.3]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.3
[0.2.2]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.2
[0.2.1]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.1
[0.2.0]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.0
[0.1.0]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.1.0
[Unreleased]: https://github.com/PurpleKaz81/cgpt/compare/v0.2.17...HEAD
