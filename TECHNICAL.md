# cgpt Technical Reference

This file is the canonical source of truth for:

- command behavior
- flags and defaults
- environment variable behavior
- operational and troubleshooting details

If you want the beginner walkthrough, use [README.md](README.md).

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

Purpose: generate one file per selected conversation ID.

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

Format behavior:

- `--format txt` (default) generates TXT output
- `--format md` and/or `--format docx` generate additional formats
- `__working.txt` exists only when TXT output is generated with split enabled

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

## Feature Roadmap Status

Status labels:

- `Implemented`: available now
- `Planned`: documented intent, not implemented yet

| Feature | Status | Notes |
| --- | --- | --- |
| Automated CLI critical-path tests | `Implemented` | Available via `python -m unittest discover -s tests -p "test_*.py" -v`; covers core selection parsing and output generation paths. |
| Opt-in split default (`CGPT_DEFAULT_SPLIT`) | `Implemented` | Enables split-by-default for split-capable dossier commands; `--split` and `--no-split` provide per-command override. |
| Quick recency window by count (`quick --recent N`) | `Implemented` | Limits quick keyword matching to N most recent conversations before filtering by topic terms. |
| Quick recency window by time (`quick --days N`) | `Implemented` | Limits quick keyword matching to conversations created in the last N days before filtering by topic terms. |
| `cgpt init` command | `Implemented` | Creates and verifies required folders (`zips/`, `extracted/`, `dossiers/`) under the resolved home path. |
| `--redact` mode | `Planned` | Would scrub sensitive patterns (for example emails/phones/tokens) before sharing dossiers. |
| `--json` output for discovery/search commands | `Planned` | Would add machine-readable output mode for `ids`, `find`, and `search`. |
| Token-aware chunking (`--max-tokens`) | `Planned` | Would split large `__working` outputs into upload-safe chunk files. |

Remaining planned items:

1. `--redact`
2. `--json` for `ids` / `find` / `search`
3. `--max-tokens`

## Security Notes

- `cgpt` processes local files and does not require remote APIs.
- Chat exports may contain sensitive data.
- Review outputs before sharing.
- For full policy details, see [SECURITY.md](SECURITY.md).
