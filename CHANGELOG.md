# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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

### Fixed

- Fixed `quick --ids-file` crash caused by selection parser scope (`UnboundLocalError`)

## [0.1.0] - 2026-02-10

### Added

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

[0.1.0]: https://github.com/PurpleKaz81/cgpt/releases/tag/v0.1.0
[Unreleased]: https://github.com/PurpleKaz81/cgpt/compare/v0.1.0...HEAD
