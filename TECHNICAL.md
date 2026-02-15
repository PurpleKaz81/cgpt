# cgpt Technical Reference

This is the single source of truth for CLI behavior, command details, flags, and operational edge cases.

If you are looking for a quick, non-technical walkthrough, start with `README.md`.

## System Model

`cgpt.py` converts ChatGPT export ZIP files into searchable data and dossier files.

Expected home layout:

```text
<home>/
|- cgpt.py
|- zips/       # ChatGPT export ZIP files
|- extracted/  # extracted exports + cgpt_index.db
`- dossiers/   # generated output files
```

Important behavior:

- `zips/`, `extracted/`, and `dossiers/` must exist.
- `cgpt` creates subfolders inside `extracted/` and `dossiers/` as needed.
- In this repo, those folders are tracked with `.gitkeep`; real contents are git-ignored.

## Architecture and Data Flow

High-level pipeline:

```text
latest ZIP discovery -> extraction -> optional indexing -> selection -> dossier build
```

Operational notes:

- `extract` unpacks ZIP data under `extracted/<zip_stem>/`.
- Commands that browse/search conversations default to `extracted/latest` unless `--root` is provided.
- `quick` combines discovery and dossier generation in one flow.
- `recent` is recency-first browsing and selection.
- `build-dossier` is ID-first generation.

## Requirements

- Python 3.8+
- Optional: `python-docx` (required only for `--format docx`)

## Setup

### Option A: Use this repository directly

```bash
cd /path/to/cgpt
python3 cgpt.py --help
```

### Option B: Install as a single script elsewhere

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

Without alias, run commands as `python3 cgpt.py ...`.

## Private + Public Workflow (One Repository)

Use tracked `config.json` for public defaults and untracked `config.personal.json` for personal rules.

One-time setup per clone:

```bash
cp config.json config.personal.json
git config --local core.hooksPath .githooks
```

Private protection layers:

- `.gitignore` ignores `config.personal.json` and `*.private.json`
- `.git/info/exclude` can add clone-local ignore rules
- `.githooks/pre-commit` blocks commits of private config file patterns

Day-to-day private usage examples:

```bash
cgpt quick --config config.personal.json "topic"
cgpt recent 30 --config config.personal.json --split
cgpt build-dossier --ids <id1> <id2> --config config.personal.json --split
```

Safe pull/merge/push routine:

```bash
git status --short
git pull origin main
git add cgpt.py README.md TECHNICAL.md CHANGELOG.md SECURITY.md RELEASING.md config.json .gitignore .githooks/pre-commit
git diff --cached
git commit -m "your message"
git push origin <branch>
```

Avoid `git add .` for this repo.

## Command Overview

### Extract and Index

```bash
cgpt extract [path/to/export.zip]
cgpt x [path/to/export.zip]         # alias
cgpt index                          # rebuild/update search index
cgpt latest-zip                     # print newest ZIP in zips/
```

Notes:

- `extract` without a path uses newest ZIP in `zips/`.
- Running just `cgpt` (no subcommand) behaves like `extract` with newest ZIP.

### Recency-Based Combined Dossier

```bash
cgpt recent 30 --split --name "thesis"
cgpt r 30 --split --name "thesis"  # alias
```

Useful flags:

- `--all`: include all shown conversations without prompt.
- `--mode excerpts --context 2`: only matched segments plus nearby context.
- `--format txt md docx`: request one or many output formats.

### Keyword-Based Combined Dossier

```bash
cgpt quick "topic"
cgpt q "topic"                     # alias
cgpt q --recent 25 "exception"      # only most-recent 25 conversations
cgpt q --days 7 "exception"         # only conversations from last 7 days
cgpt q --where all --split "policy" "brief"
cgpt q --and --split "term1" "term2"
```

Useful flags:

- `--where title|messages|all`: controls matching scope.
- `--recent N`: apply keyword matching only to the N most recent conversations.
- `--days N`: apply keyword matching only to conversations created in last N days.
- `--ids-file <file>`: non-interactive selection source.
- `--split`: create raw plus working TXT output.

Important behavior:

- `recent` remains recency browsing and does not take keyword positional terms.
- For keyword + recency in one command, use `quick --recent N "term"` or `quick --days N "term"`.

### Build Combined Dossier from Explicit IDs

```bash
cgpt build-dossier \
  --ids 123abc 456def \
  --topic "project-topic" \
  --split \
  --name "project"

cgpt d --ids 123abc 456def --mode full --split --name "project"  # alias
```

Rules:

- You must provide `--ids` and/or `--ids-file`.
- IDs are space-separated (not comma-separated).
- In `--mode excerpts`, you must provide `--topic` and/or `--topics`.
- In `--mode full`, topic flags are optional.

### Generate One File per ID

```bash
cgpt make-dossiers --ids 123abc 456def
cgpt make-dossiers --ids-file selected_ids.txt --format txt md
```

This produces separate files per conversation ID, not one combined dossier.

### Discovery and Search Helpers

```bash
cgpt ids
cgpt i                               # alias
cgpt find "keyword"
cgpt f "keyword"                    # alias
cgpt search "keyword"
cgpt search --where messages "keyword"
cgpt search --terms alpha beta --and --where all
```

## Interactive Selection Input

For `recent` and `quick`, supported selection input includes:

- Single numbers: `3`
- Multiple numbers: `1 4 9`
- Ranges: `2-6`
- Mixed: `1-3 7 10-12`
- `all`
- Raw conversation IDs (if listed in the prompt set)

## Output Layout and Naming

Without `--name`:

```text
dossiers/
|- dossier__topic__YYYYMMDD_HHMMSS.txt
`- dossier__topic__YYYYMMDD_HHMMSS__working.txt   # only with --split
```

With `--name "thesis"`:

```text
dossiers/
`- thesis/
   |- YYYY-MM-DD_HHMMSS.txt
   `- YYYY-MM-DD_HHMMSS__working.txt              # only with --split
```

## Flags That Matter Most

- `--split`: create raw and cleaned working TXT files.
- `--no-split`: force-disable split output (useful when `CGPT_DEFAULT_SPLIT` is enabled).
- `--name "X"`: group output under `dossiers/X/`.
- `--where all`: search both titles and messages.
- `--mode excerpts --context N`: narrower dossier from matched segments.
- `--format txt md docx`: choose output formats.
- `--no-dedup`: disable deduplication in working output.
- `--home /path/to/home`: override auto home detection.
- `--quiet`: suppress non-error output.

`--split` behavior details:

- Split-by-default can be enabled with `CGPT_DEFAULT_SPLIT=1`.
- `--split` and `--no-split` override environment default for a single command.
- `--split` creates working file only when TXT output is generated.
- If output is only `md` and/or `docx`, no `__working.txt` file is created.

## Advanced Filter Inputs

Supported by `recent`/`r`, `quick`/`q`, and `build-dossier`/`d`:

- `--patterns-file <file>`: one deliverable pattern per line.
- `--used-links-file <file>`: one URL per line to prioritize in source output.
- `--config <file>`: JSON config for segment filtering/control-layer behavior.

Example:

```bash
cgpt q --split \
  --patterns-file patterns.txt \
  --used-links-file used-links.txt \
  --config config.personal.json \
  "topic"
```

Mode caveat:

- `--topic` and `--topics` are only required in `--mode excerpts`.

## Home Resolution and Environment Variables

Home resolution order:

1. `--home`
2. `CGPT_HOME`
3. Auto-discovery from current directory and parents

Supported environment variables:

- `CGPT_HOME`: explicit home path.
- `CGPT_DEFAULT_MODE`: `full` or `excerpts`.
- `CGPT_DEFAULT_SPLIT`: `1/true/yes/on` or `0/false/no/off`.
- `CGPT_FORCE_COLOR`: `1/true/yes/on` or `0/false/no/off`.

## Troubleshooting

### `ERROR: Missing folder: ... Expected: zips/, extracted/, dossiers/`

Create required folders:

```bash
mkdir -p zips extracted dossiers
```

### `ERROR: No ZIPs found in .../zips`

Put at least one ChatGPT export ZIP in `zips/`.

### `ERROR: No JSON found under ...`

Export is not extracted yet, or `--root` points to wrong location.

Fix:

```bash
cgpt extract
```

Then rerun your command.

### `ERROR: Provide --topic and/or --topics`

Applies only to excerpts mode (`--mode excerpts`).

### `ERROR: Provide --ids and/or --ids-file`

`build-dossier` and `make-dossiers` require explicit conversation IDs.

### `ModuleNotFoundError: No module named 'docx'`

Install optional DOCX dependency:

```bash
pip install python-docx
```

## Automated Tests

Run CLI critical-path suite:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Current suite coverage includes selection parsing and output generation for:

- `quick`
- `recent`
- `make-dossiers`

## Feature Roadmap Status

Status labels:

- `Implemented`: available in current CLI.
- `Planned`: documented intent only; not implemented.

| Feature | Status | Notes |
| --- | --- | --- |
| Automated CLI critical-path tests | `Implemented` | Available via `python -m unittest discover -s tests -p "test_*.py" -v`; covers core selection parsing and output generation paths. |
| Opt-in split default (`CGPT_DEFAULT_SPLIT`) | `Implemented` | Enables split-by-default for split-capable dossier commands; `--split` and `--no-split` provide per-command override. |
| Quick recency window by count (`quick --recent N`) | `Implemented` | Limits quick keyword matching to the N most recent conversations before filtering by topic terms. |
| Quick recency window by time (`quick --days N`) | `Implemented` | Limits quick keyword matching to conversations created in the last N days before filtering by topic terms. |
| `cgpt init` command | `Planned` | Would create/verify `zips/`, `extracted/`, and `dossiers/`, and optionally scaffold defaults. |
| `--redact` mode | `Planned` | Would scrub sensitive patterns (for example emails/phones/tokens) from generated dossiers before sharing. |
| `--json` output for discovery/search commands | `Planned` | Would add machine-readable output mode for `ids`, `find`, and `search` to improve scripting/automation workflows. |
| Token-aware chunking (`--max-tokens`) | `Planned` | Would split large `__working` outputs into chunked files sized for upload constraints. |

Remaining planned features:

1. `cgpt init` command
2. `--redact` mode
3. `--json` output for `ids` / `find` / `search`
4. Token-aware chunking (`--max-tokens`)

## Safety Notes

- `cgpt` runs locally and does not send exports to external services.
- Chat exports may contain sensitive information.
- Review generated files before sharing.
- Security handling rules are in `SECURITY.md`.
