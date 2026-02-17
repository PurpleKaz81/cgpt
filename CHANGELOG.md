# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Maintenance note for markdown lint:

- In numbered release sections, keep level-3 subsection headings unique (for example: `### Added in 0.2.4`, `### Changed in 0.2.4`, `### Fixed in 0.2.4`).

## [Unreleased]

### Changed

- Nothing yet.

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

[0.2.7]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.7
[0.2.6]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.6
[0.2.5]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.5
[0.2.4]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.4
[0.2.3]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.3
[0.2.2]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.2
[0.2.1]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.1
[0.2.0]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.2.0
[0.1.0]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.1.0
[Unreleased]: https://github.com/PurpleKaz81/cgpt/compare/v0.2.7...HEAD
