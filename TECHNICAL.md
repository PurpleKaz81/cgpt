# cgpt Technical Reference

This file is the canonical source of truth for:

- command behavior
- flags and defaults
- environment variable behavior
- operational and troubleshooting details

If you want the beginner walkthrough, use [README.md](README.md).

## Documentation Topology

Canonical docs:

- `README.md`: beginner-first usage and quick workflows
- `TECHNICAL.md`: canonical command/flag/behavior reference
- `SECURITY.md`: security and privacy handling
- `CHANGELOG.md`: release history and unreleased changes
- `RELEASING.md`: maintainer release workflow

Scoped supplemental docs are allowed only in:

- `docs/specs/`
- `docs/adr/`
- `docs/runbooks/`
- `docs/roadmap/`

Index requirement:

- every markdown file under the scoped `docs/` folders must be linked from `docs/INDEX.md`

## CLI Surface (Current)

Global command:

```bash
cgpt.py [global options] <subcommand> [subcommand options]
```

Subcommands (with aliases):

- `init`
- `latest-zip`
- `extract`
- `x` (alias for `extract`)
- `index`
- `ids`
- `i` (alias for `ids`)
- `find`
- `f` (alias for `find`)
- `search`
- `make-dossiers`
- `build-dossier`
- `d` (alias for `build-dossier`)
- `quick`
- `q` (alias for `quick`)
- `recent`
- `r` (alias for `recent`)

## Expected Folder Model

`cgpt` expects this home layout:

```text
<home>/
|- cgpt.py
|- zips/
|- extracted/
`- dossiers/
```

Behavior:

- `zips/`, `extracted/`, and `dossiers/` must exist.
- `cgpt init` can create and verify these required folders.
- Command logic may create subfolders under `extracted/` and `dossiers/`.
- In this repository, `.gitkeep` placeholder files are tracked; real content under these folders is ignored.

## Processing Model

High-level pipeline:

```text
ZIP discovery -> extraction -> optional indexing -> selection -> dossier generation
```

Operational notes:

- `extract` unpacks exports into `extracted/<zip_stem>/`.
- Selection/search commands default to `extracted/latest` unless `--root` is provided.
- `quick` performs topic discovery + selection + dossier generation in one flow.
- `recent` is recency-first selection.
- `build-dossier` is explicit-ID-first generation.

## Requirements

- Python 3.8+
- Optional dependency for DOCX output: `python-docx`

Install optional DOCX dependency:

```bash
pip install python-docx
```

## Setup

### Option A: Run directly in this repository

```bash
cd /path/to/cgpt
python3 cgpt.py --help
```

### Option B: Script-only install elsewhere

```bash
mkdir -p ~/Documents/chatgpt_exports
cp cgpt.py ~/Documents/chatgpt_exports/
cd ~/Documents/chatgpt_exports
mkdir -p zips extracted dossiers
```

Optional alias:

```bash
echo 'alias cgpt="python3 ~/Documents/chatgpt_exports/cgpt.py"' >> ~/.zshrc
source ~/.zshrc
```

## Global Options

These options are valid before subcommands:

- `--version`: print version and exit
- `--color`: force-enable ANSI color output
- `--no-color`: force-disable ANSI color output
- `--home <path>`: set home folder containing `zips/`, `extracted/`, `dossiers/`
- `--quiet`: suppress non-error output
- `--default-mode {full,excerpts}`: set preferred dossier mode default for this invocation

## Command Reference

### `init`

Purpose: create/verify required home folders (`zips/`, `extracted/`, `dossiers/`).

```bash
cgpt init
```

Flags:

- `-h`, `--help`

### `latest-zip`

Purpose: print newest ZIP found in `zips/`.

```bash
cgpt latest-zip
```

Flags:

- `-h`, `--help`

### `extract` / `x`

Purpose: extract a ChatGPT export ZIP.

```bash
cgpt extract [path/to/export.zip]
cgpt x [path/to/export.zip]
```

Arguments:

- `zip` (optional positional): explicit path to ZIP

Flags:

- `--no-index`: skip index update after extraction
- `--reindex`: force full index rebuild after extraction

Notes:

- Without `zip`, newest ZIP in `zips/` is used.
- Running `cgpt` with no subcommand behaves like extraction of newest ZIP.

### `index`

Purpose: build or rebuild search index.

```bash
cgpt index
```

Flags:

- `--root <path>`: extracted data location to scan (default: `extracted/latest`)
- `--reindex`: force rebuild
- `--db <path>`: override index DB path (default: `extracted/cgpt_index.db`)

### `ids` / `i`

Purpose: print `id<TAB>title` for conversations.

```bash
cgpt ids
cgpt i
```

Flags:

- `--root <path>`

### `find` / `f`

Purpose: case-insensitive title match helper.

```bash
cgpt find "keyword"
cgpt f "keyword"
```

Arguments:

- `query` (required positional)

Flags:

- `--root <path>`

### `search`

Purpose: search title and/or message text.

```bash
cgpt search "keyword"
cgpt search "keyword" all
cgpt search --terms alpha beta --and --where messages
```

Arguments:

- `query` (optional positional)
- optional positional location selector: `title|messages|all`

Flags:

- `--terms <term1> [term2 ...]`: explicit term list
- `--and`: require all terms (default logic is OR)
- `--where {title,messages,all}`: explicit search scope
- `--root <path>`

### `make-dossiers`

Purpose: generate one or more files per selected conversation ID.

```bash
cgpt make-dossiers --ids <id1> <id2>
cgpt make-dossiers --ids-file selected_ids.txt --format txt md docx
```

Flags:

- `--root <path>`
- `--ids-file <file>`
- `--ids <id1> <id2> ...`
- `--format txt|md|docx [txt|md|docx ...]` (default: `txt`)

Rules:

- requires `--ids` and/or `--ids-file`
- outputs are per-conversation, not one combined dossier
- output formats are strict: only explicitly requested formats are written

### `build-dossier` / `d`

Purpose: generate one combined dossier from explicit IDs.

```bash
cgpt build-dossier --ids 123abc 456def --mode full --split
cgpt d --ids 123abc 456def --mode excerpts --topic "policy" --context 2
```

Flags:

- `--topic <term>`
- `--topics <term1> [term2 ...]`
- `--mode {full,excerpts}`
- `--context <N>`
- `--root <path>`
- `--ids-file <file>`
- `--ids <id1> <id2> ...`
- `--format txt|md|docx [txt|md|docx ...]`
- `--split` / `--no-split`
- `--dedup` / `--no-dedup`
- `--patterns-file <file>`
- `--used-links-file <file>`
- `--config <file>`
- `--name <project_name>`

Rules:

- requires `--ids` and/or `--ids-file`
- in `full` mode, topic flags are optional
- in `excerpts` mode, at least one topic flag is required
- exits with an error when none of the requested output formats can be created (for example `--format docx` without `python-docx`)

### `quick` / `q`

Purpose: keyword-based selection + combined dossier generation.

```bash
cgpt q "topic"
cgpt q --recent 25 "topic"
cgpt q --days 7 "topic"
cgpt q --where all --and "policy" "brief"
```

Arguments:

- `topics [topics ...]` positional terms

Flags:

- `--and`
- `--mode {full,excerpts}`
- `--context <N>`
- `--all`
- `--where {title,messages,all}`
- `--recent <N>`
- `--days <N>`
- `--root <path>`
- `--ids-file <file>`
- `--format txt|md|docx [txt|md|docx ...]`
- `--split` / `--no-split`
- `--dedup` / `--no-dedup`
- `--patterns-file <file>`
- `--used-links-file <file>`
- `--config <file>`
- `--name <project_name>`

Rules:

- `--recent` and `--days` are mutually exclusive
- if neither is set, quick uses the full available conversation set

### `recent` / `r`

Purpose: recency-first selection + combined dossier generation.

```bash
cgpt recent 30 --split
cgpt r 50 --all --name "thesis"
```

Arguments:

- `count` (optional positional, default `30`)

Flags:

- `--all`
- `--root <path>`
- `--format txt|md|docx [txt|md|docx ...]`
- `--split` / `--no-split`
- `--dedup` / `--no-dedup`
- `--patterns-file <file>`
- `--used-links-file <file>`
- `--config <file>`
- `--name <project_name>`
- `--mode {full,excerpts}`
- `--context <N>`

Rules:

- `recent` does not accept keyword positional terms
- for keyword + recency in one command, use `quick --recent N "term"` or `quick --days N "term"`

## Selection Input Grammar (Interactive)

Used by `recent` and `quick` interactive selection:

- single numbers: `3`
- multiple numbers: `1 4 9`
- ranges: `2-6`
- mixed: `1-3 7 10-12`
- `all`
- raw conversation IDs (if present in shown list)

## Output Behavior

### Combined dossier commands (`build-dossier`, `quick`, `recent`)

Without `--name`:

```text
dossiers/
|- dossier__topic__YYYYMMDD_HHMMSS.txt
`- dossier__topic__YYYYMMDD_HHMMSS__working.txt   # only when split+txt apply
```

With `--name "project"`:

```text
dossiers/
`- project/
   |- YYYY-MM-DD_HHMMSS.txt
   `- YYYY-MM-DD_HHMMSS__working.txt
```

Format behavior for combined dossier commands:

- `--format txt` (default) generates TXT output
- `--format md` and/or `--format docx` generate additional formats
- `__working.txt` exists only when TXT output is generated with split enabled
- if all requested outputs fail to generate, the command exits with an error

### Per-conversation command (`make-dossiers`)

Output naming:

```text
dossiers/
|- <conversation_id>__<title_slug>.txt
|- <conversation_id>__<title_slug>.md
`- <conversation_id>__<title_slug>.docx
```

Format behavior for `make-dossiers`:

- only the formats explicitly requested with `--format` are written
- no implicit sidecar format is created

## Split and Dedup Semantics

Relevant controls:

- `--split` forces split output
- `--no-split` disables split output
- `--dedup` / `--no-dedup` control deduplication in working output

Environment interplay:

- `CGPT_DEFAULT_SPLIT=1` enables split-by-default behavior
- per-command flags override environment default

## Advanced Input Files

Supported on `quick`, `recent`, and `build-dossier`:

- `--patterns-file <file>`: one deliverable pattern per line
- `--used-links-file <file>`: one URL per line to prioritize sources
- `--config <file>`: JSON config for segment filtering/control-layer behavior

Example:

```bash
cgpt q --split \
  --patterns-file patterns.txt \
  --used-links-file used-links.txt \
  --config config.personal.json \
  "topic"
```

## Home Resolution and Environment Variables

Home resolution order:

1. `--home`
2. `CGPT_HOME`
3. auto-discovery from current directory and parent folders

Environment variables:

- `CGPT_HOME`: set explicit home path
- `CGPT_DEFAULT_MODE`: `full` or `excerpts`
- `CGPT_DEFAULT_SPLIT`: `1/true/yes/on` or `0/false/no/off`
- `CGPT_FORCE_COLOR`: force-enable or force-disable color (`1/true/yes/on` or `0/false/no/off`)

## Private + Public Workflow (One Repository)

Recommended split:

- tracked `config.json` for public defaults
- untracked `config.personal.json` for personal/private preferences

One-time setup:

```bash
cp config.json config.personal.json
git config --local core.hooksPath .githooks
```

Day-to-day private usage:

```bash
cgpt q --config config.personal.json "topic"
cgpt recent 30 --config config.personal.json --split
cgpt build-dossier --ids <id1> <id2> --config config.personal.json --split
```

Safe git routine:

```bash
git status --short
git pull origin main
git add cgpt.py README.md TECHNICAL.md CHANGELOG.md SECURITY.md RELEASING.md config.json .gitignore .githooks/pre-commit
git add docs/INDEX.md docs/specs docs/adr docs/runbooks docs/roadmap
git diff --cached
git commit -m "your message"
git push origin <branch>
```

Avoid `git add .`.

## Troubleshooting

### `ERROR: Missing folder: ... Expected: zips/, extracted/, dossiers/`

Fix:

```bash
mkdir -p zips extracted dossiers
```

### `ERROR: No ZIPs found in .../zips`

Fix: place at least one ChatGPT export ZIP in `zips/`.

### `ERROR: No JSON found under ...`

Fix:

```bash
cgpt extract
```

### `ERROR: Provide --topic and/or --topics`

Cause: `excerpts` mode without topic terms.

### `ERROR: Provide --ids and/or --ids-file`

Cause: ID-required command called without IDs.

### `ModuleNotFoundError: No module named 'docx'`

Fix:

```bash
pip install python-docx
```

## Validation and Tests

Run critical-path tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Current test coverage includes key generation flows around:

- `quick`
- `recent`
- `make-dossiers`
- `init`
- strict `make-dossiers --format` behavior (`txt`-only and `md`-only)
- `build-dossier` docx-only failure behavior when `python-docx` is unavailable

## Feature Roadmap Status

This section is the canonical, implementation-ordered queue for roadmap items that are not yet implemented.

### Roadmap Status Model

- `Implemented`: available now in CLI/runtime behavior.
- `Planned (Committed)`: approved implementation intent; not built yet.
- `Proposed Enhancement`: prioritized recommendation; not yet committed.

### Unified Priority Queue

| Priority | Feature | Status | Why now | Interface changes | Dependencies | Effort | Primary acceptance gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Optional dependency CI matrix (`python-docx` present/missing) | `Proposed Enhancement` | Prevent regressions in optional DOCX paths early | CI matrix jobs for dependency-on and dependency-off runs | none | `M` | CI passes in both environments |
| 2 | `cgpt doctor` command | `Proposed Enhancement` | Reduce setup/support friction with deterministic health checks | New `doctor` subcommand and structured check output | none | `M` | Detects layout/dependency/config failures with correct exit code |
| 3 | `--redact` mode | `Planned (Committed)` | High data-safety value before sharing outputs | `--redact` on dossier-producing commands | none | `L` | Sensitive patterns are scrubbed with predictable rules |
| 4 | `--json` output for `ids` / `find` / `search` | `Planned (Committed)` | Enables script/automation integration for discovery flows | `--json` on discovery/search commands with stable schema | none | `M` | JSON schema is stable and parity-tested against text mode |
| 5 | `--dry-run` mode for write commands | `Proposed Enhancement` | Improves confidence before writes/overwrites | `--dry-run` for `build-dossier`, `make-dossiers`, `quick`, `recent` | none | `M` | Dry-run produces plan output and writes zero files |
| 6 | Token-aware chunking (`--max-tokens`) | `Planned (Committed)` | Prevents oversized working outputs for downstream upload limits | `--max-tokens <N>` for combined dossier working outputs | none | `M` | Chunk files respect token limits and preserve ordering |
| 7 | `--json` output for write commands | `Proposed Enhancement` | Standardizes machine-readable output metadata | `--json` on write commands (paths, warnings, counts, timings) | discovery `--json` (P4) | `M` | Write command results are schema-validated and stable |
| 8 | `--strict` automation mode | `Proposed Enhancement` | Strengthens CI/script reliability by hard-failing warning states | `--strict` mode for write/validation flows | warning surfaces stabilized (P7) | `M` | Warnings become failures with deterministic non-zero exits |
| 9 | Date range filters (`--since`, `--until`) | `Proposed Enhancement` | Adds reproducible time-window control beyond relative filters | `--since` / `--until` on query/selection flows | none | `M` | Filtering is timezone-consistent and boundary-tested |
| 10 | Output control flags (`--out-dir`, `--output-prefix`) | `Proposed Enhancement` | Improves automation and deterministic output naming | `--out-dir` / `--output-prefix` on write commands | none | `M` | Outputs land in requested locations with validated naming |
| 11 | Config profiles (`--profile`) | `Proposed Enhancement` | Simplifies repeatable workflows without long flag strings | `--profile <name>` config-profile selection | none | `L` | Profile resolution is deterministic and overrides are well-defined |

### Feature Specs (Decision-Complete Cards)

#### P1. Optional Dependency CI Matrix (`python-docx` present/missing) [`Proposed Enhancement`]

- Goal: prevent regressions in optional DOCX behavior across dependency states.
- In scope: CI matrix for dependency-present and dependency-missing jobs; existing suite execution in both jobs.
- Out of scope: changing runtime feature behavior beyond test hardening.
- CLI/API contract: no user-facing CLI changes.
- Error/failure behavior: CI must fail on behavior drift in either dependency state.
- Test scenarios: run full unit suite in both matrix lanes; validate docx-failure paths when dependency is missing.
- Exit criteria: CI config merged and green in both lanes on `main`.

#### P2. `cgpt doctor` [`Proposed Enhancement`]

- Goal: provide a one-command health check for environment/workspace readiness.
- In scope: layout checks (`zips/`, `extracted/`, `dossiers/`), optional dependency checks, config parse checks, index presence/basic integrity checks.
- Out of scope: auto-remediation that mutates user data beyond optional explicit flags.
- CLI/API contract: add `cgpt doctor` subcommand; optional `--json` output is allowed if designed in the same effort.
- Error/failure behavior: non-zero exit on hard failures; clear categorized diagnostics.
- Test scenarios: healthy workspace, missing folders, invalid config JSON, missing optional dependency.
- Exit criteria: deterministic output and exit code semantics documented and tested.

#### P3. `--redact` Mode [`Planned (Committed)`]

- Goal: reduce accidental leakage of sensitive data in generated outputs.
- In scope: redact emails, phone-like values, API-key/token patterns in output text.
- Out of scope: irreversible mutation of source export files.
- CLI/API contract: add `--redact` to dossier-producing commands (`build-dossier`, `quick`, `recent`, optional `make-dossiers` coverage decision documented at implementation).
- Error/failure behavior: invalid redact configuration fails fast with descriptive error.
- Test scenarios: redact on/off comparisons; mixed content with multiple sensitive pattern types.
- Exit criteria: default-off behavior, deterministic redaction output, and test coverage for major pattern classes.

#### P4. Discovery `--json` (`ids` / `find` / `search`) [`Planned (Committed)`]

- Goal: provide stable machine-readable discovery outputs for scripts and tooling.
- In scope: JSON schemas for each command including IDs, titles, scopes, and metadata.
- Out of scope: replacing human-readable default output.
- CLI/API contract: `--json` flag on `ids`, `find`, and `search`.
- Error/failure behavior: schema serialization errors return non-zero and descriptive stderr.
- Test scenarios: parity tests between text output rows and JSON item counts/fields.
- Exit criteria: schema documented in TECHNICAL and regression-tested.

#### P5. `--dry-run` for Write Commands [`Proposed Enhancement`]

- Goal: allow safe previews before generating files.
- In scope: `build-dossier`, `make-dossiers`, `quick`, `recent` plan output without writes.
- Out of scope: deep simulation of optional side effects outside normal write paths.
- CLI/API contract: add `--dry-run` on targeted write commands.
- Error/failure behavior: invalid argument combinations fail with current command validation semantics.
- Test scenarios: verify selection/planning output exists and file system remains unchanged.
- Exit criteria: zero-write guarantee validated by tests.

#### P6. Token-Aware Chunking (`--max-tokens`) [`Planned (Committed)`]

- Goal: split working outputs into upload-safe segments.
- In scope: chunking for combined dossier working outputs with ordering and naming guarantees.
- Out of scope: exact model-tokenizer parity for every downstream model family.
- CLI/API contract: add `--max-tokens <N>` to combined dossier generation paths.
- Error/failure behavior: invalid `N` values fail with clear validation message.
- Test scenarios: near-boundary chunk sizes, minimal chunk size, multi-chunk ordering.
- Exit criteria: deterministic chunk boundaries and complete content preservation.

#### P7. Write-Command `--json` Output [`Proposed Enhancement`]

- Goal: provide structured machine-readable metadata for generated artifacts.
- In scope: JSON results for `build-dossier`, `make-dossiers`, `quick`, `recent` including output paths, warnings, counts, timings.
- Out of scope: removal of current human-readable output.
- CLI/API contract: add `--json` to write commands with shared response envelope.
- Error/failure behavior: schema failures return non-zero and emit error diagnostics.
- Test scenarios: single-output, multi-output, warning-producing runs, no-output failures.
- Exit criteria: schema stability and command parity tests across write commands.

#### P8. `--strict` Automation Mode [`Proposed Enhancement`]

- Goal: make automation pipelines fail fast on warning conditions.
- In scope: promote eligible warnings to hard failures in strict mode.
- Out of scope: changing default non-strict behavior.
- CLI/API contract: add `--strict` mode to relevant commands (write/validation flows).
- Error/failure behavior: warning states produce non-zero exit in strict mode with clear reason.
- Test scenarios: known warning-producing paths in strict vs non-strict mode.
- Exit criteria: strict behavior is deterministic and documented.

#### P9. Date Range Filters (`--since`, `--until`) [`Proposed Enhancement`]

- Goal: support deterministic date-bounded query/selection workflows.
- In scope: date-range filtering for query/selection commands.
- Out of scope: replacing existing `--recent` / `--days` shortcuts.
- CLI/API contract: add `--since <date>` and `--until <date>` where selection/query semantics apply.
- Error/failure behavior: invalid date format or impossible range fails with clear diagnostics.
- Test scenarios: open-ended ranges, inclusive boundaries, empty result windows.
- Exit criteria: documented date format and timezone handling with boundary tests.

#### P10. Output Control Flags (`--out-dir`, `--output-prefix`) [`Proposed Enhancement`]

- Goal: provide deterministic output paths and names for automation.
- In scope: path/prefix control for write commands.
- Out of scope: changing existing defaults when flags are omitted.
- CLI/API contract: add `--out-dir <path>` and `--output-prefix <prefix>` to write commands.
- Error/failure behavior: invalid or unwritable directories fail fast before processing.
- Test scenarios: valid custom dirs, non-existent dirs, permission errors, prefix formatting.
- Exit criteria: outputs consistently honor requested location/naming.

#### P11. Config Profiles (`--profile`) [`Proposed Enhancement`]

- Goal: reduce repetitive flag usage with named reusable configuration profiles.
- In scope: profile lookup and merge resolution across config sources.
- Out of scope: dynamic remote profile fetching.
- CLI/API contract: add `--profile <name>` profile selection in config handling.
- Error/failure behavior: missing/invalid profile fails with explicit profile list guidance.
- Test scenarios: default profile fallback, explicit profile selection, override precedence.
- Exit criteria: deterministic precedence rules documented and covered by tests.

### Dependency Graph Notes

- Discovery `--json` (P4) is a prerequisite for write-command `--json` (P7) to keep schemas aligned.
- Optional dependency CI matrix (P1) should land before broad feature rollout to catch dependency-state regressions continuously.
- `--strict` (P8) should be introduced only after warning surfaces and structured outputs are standardized (P7).
- `--dry-run` (P5) should precede output-path customization (P10) to validate no-write semantics independently.
- `cgpt doctor` (P2) is best delivered early to reduce support/debug load during subsequent feature rollouts.

## Security Notes

- `cgpt` processes local files and does not require remote APIs.
- Chat exports may contain sensitive data.
- Review outputs before sharing.
- For full policy details, see [SECURITY.md](SECURITY.md).
