# Documentation Index

This file is the canonical index for scoped markdown documentation under `docs/`.

Rule:

- Every markdown file under `docs/specs/`, `docs/adr/`, `docs/runbooks/`, and `docs/roadmap/` must be linked in this file.

Core canonical docs remain:

- `README.md` (beginner-first usage)
- `TECHNICAL.md` (canonical command/reference behavior)
- `SECURITY.md`
- `CHANGELOG.md`
- `RELEASING.md`

## Specs

- [`docs/specs/product-vision.md`](specs/product-vision.md): neutral mission, scope, principles, local-first posture, and non-goals.
- [`docs/specs/current-capabilities.md`](specs/current-capabilities.md): current feature set, constraints, and known limitations.
- [`docs/specs/v0.2.1-edge-hardening.md`](specs/v0.2.1-edge-hardening.md): planned security/correctness hardening scope, behavior contracts, and test matrix for patch v0.2.1.
- [`docs/specs/v0.2.2-remainder-hardening.md`](specs/v0.2.2-remainder-hardening.md): follow-up hardening scope for remaining edge cases, including extraction freshness and input validation.

## ADRs

No entries yet.

## Runbooks

- [`docs/runbooks/ai-agent-reference.md`](runbooks/ai-agent-reference.md): deterministic repository and workflow reference for AI agents and automation.

## Roadmap Notes

- [`docs/roadmap/shared-roadmap.md`](roadmap/shared-roadmap.md): canonical trimester roadmap with status and commitment tags.

## New Doc Checklist

1. Place the new markdown file in one of:
   - `docs/specs/`
   - `docs/adr/`
   - `docs/runbooks/`
   - `docs/roadmap/`
2. Add a link to the file in the appropriate section of `docs/INDEX.md`.
3. If behavior/reference implications exist, also cross-link relevant sections in `TECHNICAL.md`.
