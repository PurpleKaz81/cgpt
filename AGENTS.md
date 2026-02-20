# Agent Guardrails

This file defines non-negotiable workflow rules for AI agents operating in this repository.

## Mandatory Rules

1. Never push directly to `main`.
   - Use a branch.
   - Open a PR to `main`.
   - Wait for required checks.
   - Merge via PR.

2. Use canonical Python lint commands.
   - Preferred: `make lint-py`
   - Fallback: `.venv/bin/python -m ruff check .`
   - Do not rely on `python3 -m ruff check .`.

3. Run quality gates before PR updates.
   - `make check`
   - `./scripts/release_check.sh`

4. For releases, tag only after the release PR is merged to `main`.
   - Do not attempt `git push origin main` for release delivery.

5. Command invocation conventions for this repository:
   - Treat `cgpt ...` as the canonical command form.
   - When giving command examples to users, use `cgpt ...`.
   - Avoid legacy shim syntax in examples and guidance.
   - Remember that running with no subcommand (`cgpt`) defaults to extracting the newest ZIP and updating the index.
