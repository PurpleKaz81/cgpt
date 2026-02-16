# Current Capabilities

Last updated: 2026-02-16

## Scope Snapshot

This file describes what `cgpt` does today. Anything not listed as implemented here should be treated as not available yet.

## Supported Input

- ChatGPT export ZIP files placed in `zips/`.
- Extracted JSON conversation trees under `extracted/`.

## Core Implemented Workflows

- Extraction and indexing:
  - `cgpt extract`, `cgpt index`, `cgpt latest-zip`
- Discovery and search:
  - `cgpt ids`, `cgpt find`, `cgpt search`
- Selection and dossier generation:
  - `cgpt build-dossier`, `cgpt quick`, `cgpt recent`, `cgpt make-dossiers`
- Workspace bootstrap:
  - `cgpt init` creates/verifies required folders.

## Selection Features Implemented

- Interactive selection by index, range, and mixed ranges (`1-3 7 10-12`).
- Selection by explicit conversation IDs.
- Recency-based filtering (`recent N`, `quick --recent N`).
- Day-window filtering (`quick --days N`).
- Keyword/topic-driven conversation discovery.

## Output Features Implemented

- Output formats: `txt`, `md`, and `docx` (DOCX requires optional `python-docx` dependency).
- Combined dossier workflows support split output (`--split`) and dedup controls.
- Strict format behavior for `make-dossiers --format` (only requested formats are emitted).

## Configuration Features Implemented

- Tracked public defaults via `config.json`.
- Local private overrides via untracked `config.personal.json`.
- Environment defaults including `CGPT_DEFAULT_MODE` and `CGPT_DEFAULT_SPLIT`.

## Operating Model

- Single-user, local CLI workflow.
- Local files are the system of record; no required hosted service integration.

## Known Constraints

- Supported export ingestion is currently ChatGPT export ZIP only.
- CLI-first interface only; no native GUI app yet.
- The generated dossier is a strong starting context artifact, not a guaranteed final optimized prompt package.

## Reliability and Validation

- Critical-path unit tests are in `tests/`.
- One-command release preflight is available at `scripts/release_check.sh`.

## Canonical Future Source

Future work and priority sequencing are tracked in:

- [`docs/roadmap/shared-roadmap.md`](../roadmap/shared-roadmap.md)
