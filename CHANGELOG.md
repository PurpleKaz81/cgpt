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
