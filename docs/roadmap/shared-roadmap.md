# Shared Roadmap

Last updated: 2026-02-18

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

## Necessity Ranking Model

Necessity tags:

- `critical`: required for safe sharing, privacy, or core workflow trust.
- `high`: materially improves repeatability, automation, or output usability.
- `medium`: meaningful improvement, but practical workarounds exist.
- `exploratory`: discovery or expansion work; no immediate core-user requirement.

## Strategy Baseline

- Product posture is local-first, single-user in `v0.x`.
- Current hard ingestion constraint: ChatGPT export ZIP support.
- First expansion lane beyond ChatGPT: Google (Gemini), then Perplexity.

## Shipped Baseline (Implemented)

| ID | Initiative | Status | Commitment | Horizon | Notes |
| --- | --- | --- | --- | --- | --- |
| R0 | Documented, reproducible CLI workflow | `implemented` | `committed` | `2026-T1` | Foundation complete via docs topology, release preflight, and critical-path tests. |
| R0.1 | Edge-case hardening patch (`v0.2.1`) | `implemented` | `committed` | `2026-T1` | Completed ZIP extraction safety, quick AND-scope correctness, timestamp coercion, config hard-fail, and input-file decode policy. |
| R0.2 | Remaining edge-case hardening patch (`v0.2.2`) | `implemented` | `committed` | `2026-T1` | Completed stale re-extraction remediation, strict conversations JSON discovery, message timestamp coercion, and validation for `--context`/`--name`. |
| R0.3 | Additional hardening follow-up patch (`v0.2.3`) | `implemented` | `committed` | `2026-T1` | Added ZIP special-member and archive-limit validation, strict optional-file/config schema validation, duplicate ID detection, and bounded JSON discovery candidate parsing. |
| R4 | `cgpt doctor` health check command | `implemented` | `committed` | `2026-T1` | Runtime/developer diagnostics with `--fix`, `--dev`, and `--strict` are shipped. |
| R16 | Engineering Quality Baseline Hardening | `implemented` | `committed` | `2026-T1` | CI Python matrix/cross-platform smoke, lint gates, governance baseline, and maintenance ledger contracts are in place. |
| R2 | `--redact` mode on dossier-producing commands | `implemented` | `committed` | `2026-T1` | Safe-by-default redaction with incremental private memory and optional interactive review is shipped. |

## Active Queue (Ranked by Necessity)

| Rank | ID | Initiative | Necessity | Status | Commitment | Horizon | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | R3 | Discovery `--json` (`ids`, `find`, `search`) | `high` | `planned` | `committed` | `2026-T1` | Machine-readable discovery pipeline for automation. |
| 2 | R5 | Token-aware chunking (`--max-tokens`) | `high` | `planned` | `committed` | `2026-T2` | Upload-safe context segmentation with ordering guarantees. |
| 3 | R15 | Context Quality Gates (Reliability Layer) | `high` | `planned` | `committed` | `2026-T2` | Pass/fail dossier readiness checks with staged rollout. |
| 4 | R7 | Date range filters (`--since`, `--until`) | `medium` | `planned` | `target` | `2026-T2` | Deterministic time-window filtering beyond relative recency. |
| 5 | R6 | `--dry-run` for write commands | `medium` | `planned` | `target` | `2026-T2` | Safe preview before file writes. |
| 6 | R8 | Output control flags (`--out-dir`, `--output-prefix`) | `medium` | `planned` | `target` | `2026-T3` | Better automation with deterministic paths and names. |
| 7 | R1 | Optional dependency CI matrix (`python-docx` present/missing) | `medium` | `planned` | `target` | `2026-T3` | Prevent regressions in optional DOCX paths. |
| 8 | R9 | Config profiles (`--profile`) | `medium` | `planned` | `target` | `2026-T3` | Reusable profile-based command defaults. |
| 9 | R10 | Write-command `--json` output + `--strict` mode | `medium` | `experimental` | `exploratory` | `2026-T3` | Structured automation semantics and hard-fail workflows. |
| 10 | R11 | Google (Gemini) provider ingestion path | `exploratory` | `experimental` | `exploratory` | `2026-T4` | First non-ChatGPT expansion milestone. |
| 11 | R12 | Perplexity provider ingestion path | `exploratory` | `experimental` | `exploratory` | `2026-T4` | Second provider expansion milestone. |
| 12 | R13 | Provider abstraction layer across AI ecosystems | `exploratory` | `experimental` | `exploratory` | `backlog` | Normalize provider-specific exports into one internal model. |
| 13 | R14 | Cloud-assisted sync/workflows | `exploratory` | `experimental` | `exploratory` | `backlog` | Evaluate only after local-first baseline remains stable. |

## Trimester Plan (Derived from Necessity Ranking)

- `2026-T1`: deliver rank `1` (`R3`) and keep scope tightly bounded to automation baseline.
- `2026-T2`: deliver ranks `2-5` (`R5`, `R15`, `R7`, `R6`) in that order.
- `2026-T3`: deliver ranks `6-9` (`R8`, `R1`, `R9`, `R10`) only after `2026-T2` committed items are complete.
- `2026-T4` and later: evaluate ranks `10-13` (`R11`, `R12`, `R13`, `R14`) based on local-first stability and user pull.

## R15 Initiative Breakdown

Quality gates are planned as one coherent reliability feature family with phased rollout:

1. Phase A (`2026-T2` target): token budget, coverage, and noise checks.
1. Phase B (`2026-T3` target): freshness and provenance checks.
1. Phase C (`2026-T3` to `2026-T4` target): strict-gate mode plus a stable machine-readable gate report contract.

Interface note:

- Candidate flag family (`--quality-gates`, `--max-context-tokens`, `--min-coverage`, `--freshness-days`, `--max-noise-ratio`, `--require-provenance`, `--gate-report`) is reserved for the R15 implementation spec; final names are not yet committed.

## Non-Goals in Current Roadmap Window

- Multi-user collaboration platform scope.
- Mandatory cloud account requirement.
- GUI parity commitments within current trimester unless explicitly added above.

## Review Cadence

- Review and update this roadmap at every release.
- If status or priority changes, also update:
  - `docs/specs/current-capabilities.md`
  - `README.md` (high-level positioning only)
