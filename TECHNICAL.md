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

Shared strategy docs (canonical for product framing beyond raw CLI reference):

- `docs/specs/product-vision.md`
- `docs/specs/current-capabilities.md`
- `docs/roadmap/shared-roadmap.md`
- `docs/runbooks/ai-agent-reference.md`

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
- ZIP members are security-validated before extraction; unsafe member paths fail fast with no extraction writes.
- ZIP extraction rejects symlink/special entries and enforces limits for member count and total uncompressed bytes.
- Re-extracting the same ZIP stem replaces prior extraction contents (no stale-file carryover).

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
- duplicate conversation IDs in export input fail fast (ambiguous map protection)

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
- `--context` must be within `0..200`
- explicit `--patterns-file`/`--used-links-file` paths must exist
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
- `--and --where messages` requires every term in message text scope.
- `--and --where all` requires every term across title+message union scope.
- `--context` must be within `0..200`
- explicit `--patterns-file`/`--used-links-file` paths must exist

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
- `--context` must be within `0..200`
- explicit `--patterns-file`/`--used-links-file` paths must exist

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

`--name` is normalized for filesystem safety; if normalization would produce an empty/unsafe slug (`""`, `"."`, `".."`), command fails explicitly.

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
- file encoding for these inputs is UTF-8 (UTF-8 BOM accepted)
- missing `--patterns-file`/`--used-links-file` paths are hard errors
- `--config` schema is strict (unknown keys and wrong-typed fields fail fast)

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
- `CGPT_MAX_ZIP_MEMBERS`: override extraction ZIP member-count limit
- `CGPT_MAX_ZIP_UNCOMPRESSED_BYTES`: override extraction ZIP total-uncompressed-size limit
- `CGPT_JSON_DISCOVERY_BUCKET_LIMIT`: override per-priority JSON discovery shortlist cap

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

### `ERROR: No conversations JSON found under ...`

Fix:

```bash
cgpt extract
```

Cause: extracted root does not contain a valid conversations JSON payload.

### `ERROR: Provide --topic and/or --topics`

Cause: `excerpts` mode without topic terms.

### `ERROR: Provide --ids and/or --ids-file`

Cause: ID-required command called without IDs.

### `ERROR: Unsafe ZIP member path detected: ...`

Cause: ZIP contains unsafe extraction paths (for example parent traversal or absolute paths).

### `ERROR: Special ZIP member type is not allowed: ...`

Cause: ZIP contains symlink/special entries.

### ZIP member/uncompressed size limit errors

Cause: ZIP exceeds hardening limits for member count or aggregate uncompressed bytes.

### `ERROR: Failed to read ... file as UTF-8 text: ...`

Cause: input file for IDs/patterns/used-links is not UTF-8/UTF-8-BOM decodable.

### `ERROR: patterns file not found: ...` / `ERROR: used-links file not found: ...`

Cause: explicit optional file path flag points to a missing path.

### `ERROR: Config file not found: ...` / `ERROR: Error loading config: ...` / `ERROR: Invalid config schema ...`

Cause: explicit `--config` file is missing, invalid JSON, or violates schema constraints.

### `ERROR: argument --context: --context must be between 0 and 200`

Cause: `--context` is outside allowed bounds.

### `ERROR: --name must contain at least one safe alphanumeric character after normalization.`

Cause: `--name` normalizes to an empty/unsafe path segment.

### `ERROR: Duplicate conversation ID(s) found in export: ...`

Cause: source export contains repeated IDs, so map resolution would be ambiguous.

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
- edge-case hardening suite covering:
  - ZIP path safety validation
  - ZIP symlink/special-member and archive-limit validation
  - extraction freshness on repeated same-stem extraction
  - `quick --and` behavior by scope
  - invalid timestamp coercion in recency/day filtering
  - invalid message timestamp coercion during message extraction
  - strict config load/parse/schema failures
  - strict missing-file errors for `--patterns-file` and `--used-links-file`
  - duplicate conversation ID detection in map-building paths
  - UTF-8-family input file decoding guarantees
  - conversations JSON discovery robustness and bounded candidate parsing
  - `--context`/`--name` input validation

## Feature Roadmap Status

Roadmap source of truth:

- [`docs/roadmap/shared-roadmap.md`](docs/roadmap/shared-roadmap.md)

Current capabilities source of truth:

- [`docs/specs/current-capabilities.md`](docs/specs/current-capabilities.md)

This technical reference intentionally does not maintain a second roadmap status model. Use this file for command contracts and implementation detail only.

### Technical Planning Notes (Current)

- Discovery `--json` should land before write-command `--json` to keep schemas aligned.
- Optional dependency CI matrix should land before broad feature rollout to catch dependency-state regressions continuously.
- `--strict` should be introduced only after warning surfaces and structured outputs are standardized.
- `--dry-run` should precede output-path customization to validate no-write semantics independently.
- `cgpt doctor` is high-leverage early because it reduces setup/debug support load.

## Security Notes

- `cgpt` processes local files and does not require remote APIs.
- Chat exports may contain sensitive data.
- Review outputs before sharing.
- For full policy details, see [SECURITY.md](SECURITY.md).
