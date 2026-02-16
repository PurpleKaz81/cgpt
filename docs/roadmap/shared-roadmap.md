# Shared Roadmap

Last updated: 2026-02-16

## Purpose

This is the canonical roadmap for users, contributors, and AI agents. It defines implementation status, commitment level, and delivery horizon in one place.

## Status and Commitment Model

Status tags:

- `implemented`: shipped in the current product behavior.
- `in-progress`: actively being built.
- `planned`: approved future implementation, not started.
- `experimental`: exploratory work with uncertain scope/timeline.

Commitment tags:

- `committed`: expected delivery unless blocked by critical risk.
- `target`: intended direction, may move if priorities change.
- `exploratory`: research/discovery; no delivery guarantee.

Planning horizon tags:

- `YYYY-T1`: Jan-Mar
- `YYYY-T2`: Apr-Jun
- `YYYY-T3`: Jul-Sep
- `YYYY-T4`: Oct-Dec
- `backlog`: no assigned trimester yet

## Strategy Baseline

- Product posture is local-first, single-user in `v0.x`.
- Current hard ingestion constraint: ChatGPT export ZIP support.
- First expansion lane beyond ChatGPT: Google (Gemini), then Perplexity.

## Roadmap Table

| ID | Initiative | Status | Commitment | Horizon | Notes |
| --- | --- | --- | --- | --- | --- |
| R0 | Documented, reproducible CLI workflow | `implemented` | `committed` | `2026-T1` | Foundation complete via docs topology + release preflight + critical-path tests. |
| R1 | Optional dependency CI matrix (`python-docx` present/missing) | `planned` | `target` | `2026-T1` | Prevent regressions in optional DOCX paths. |
| R2 | `--redact` mode on dossier-producing commands | `planned` | `committed` | `2026-T1` | Privacy protection before sharing generated outputs. |
| R3 | Discovery `--json` (`ids`, `find`, `search`) | `planned` | `committed` | `2026-T1` | Machine-readable discovery pipeline for automation. |
| R4 | `cgpt doctor` health check command | `planned` | `target` | `2026-T2` | Deterministic setup/runtime diagnostics. |
| R5 | Token-aware chunking (`--max-tokens`) | `planned` | `committed` | `2026-T2` | Upload-safe context segmentation with ordering guarantees. |
| R6 | `--dry-run` for write commands | `planned` | `target` | `2026-T2` | Safe preview before file writes. |
| R7 | Date range filters (`--since`, `--until`) | `planned` | `target` | `2026-T2` | Deterministic time-window filtering beyond relative recency. |
| R8 | Output control flags (`--out-dir`, `--output-prefix`) | `planned` | `target` | `2026-T2` | Better automation with deterministic paths and names. |
| R9 | Config profiles (`--profile`) | `planned` | `target` | `2026-T3` | Reusable profile-based command defaults. |
| R10 | Write-command `--json` output + `--strict` mode | `experimental` | `exploratory` | `2026-T3` | Structured automation semantics and hard-fail workflows. |
| R11 | Google (Gemini) provider ingestion path | `experimental` | `exploratory` | `2026-T3` | First non-ChatGPT expansion milestone. |
| R12 | Perplexity provider ingestion path | `experimental` | `exploratory` | `2026-T4` | Second provider expansion milestone. |
| R13 | Provider abstraction layer across AI ecosystems | `experimental` | `exploratory` | `backlog` | Normalize provider-specific exports into one internal model. |
| R14 | Cloud-assisted sync/workflows | `experimental` | `exploratory` | `backlog` | Evaluate only after local-first baseline remains stable. |

## Non-Goals in Current Roadmap Window

- Multi-user collaboration platform scope.
- Mandatory cloud account requirement.
- GUI parity commitments within current trimester unless explicitly added above.

## Review Cadence

- Review and update this roadmap at every release.
- If status or priority changes, also update:
  - `docs/specs/current-capabilities.md`
  - `README.md` (high-level positioning only)
