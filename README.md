# cgpt: ChatGPT Export to Dossier

`cgpt.py` converts ChatGPT export ZIP files into searchable data and clean dossier files.

It works locally on your machine with this folder layout:

```text
<home>/
├── cgpt.py
├── zips/       # put ChatGPT export ZIPs here
├── extracted/  # extracted exports + cgpt_index.db
└── dossiers/   # generated output files
```

Important:

- `cgpt` requires `zips/`, `extracted/`, and `dossiers/` to already exist.
- `cgpt` creates subfolders inside `extracted/` and `dossiers/` as needed.
- In this repo, those folders are tracked with `.gitkeep`; real contents are git-ignored.

## Requirements

- Python 3.8+
- Optional: `python-docx` (only if you use `--format docx`)

## Setup (First Time)

### Option A: Use this repository directly

```bash
cd /path/to/cgpt
python3 cgpt.py --help
```

The required folders are already present in this repo.

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

If you do not create an alias, use `python3 cgpt.py ...` in every example below.

## Private + Public Workflow (One Repository)

You can safely use one repo for both:

- public/shared code and docs
- your private writing constraints and personal config

The rule is simple:

- keep public defaults in tracked `config.json`
- keep personal rules in untracked `config.personal.json`

### One-time setup (do this once per clone)

```bash
cp config.json config.personal.json
git config --local core.hooksPath .githooks
```

Edit `config.personal.json` with your personal rules.

Private config files are ignored by git via:

- `.gitignore` (shared repo protection)
- `.git/info/exclude` (local-only protection)

Safety hook (enabled in this clone):

- `.githooks/pre-commit` blocks commits of files like `config.personal.json` and `*.private.json`.
- Local git config is set to use it: `core.hooksPath=.githooks`.

### 1. Your day-to-day work with `cgpt` (private use)

Always pass your private config file:

```bash
cgpt quick --config config.personal.json "topic"
cgpt recent 30 --config config.personal.json --split
cgpt build-dossier --ids <id1> <id2> --config config.personal.json --split
```

If you forget `--config`, `cgpt` uses public `config.json`.

### 2. Safe `pull` / `merge` / `push` without leaking private data

Use this exact routine:

1. Check what changed:

```bash
git status --short
```

2. If you have local public changes, commit them first (or stash them).

3. Update from remote:

```bash
git pull origin main
```

4. Stage only public files explicitly (never `git add .`):

```bash
git add cgpt.py README.md CHANGELOG.md SECURITY.md RELEASING.md config.json .gitignore .githooks/pre-commit
```

5. Verify staged content:

```bash
git diff --cached
```

6. Commit and push:

```bash
git commit -m "your message"
git push origin <branch>
```

If a private file is accidentally staged, the pre-commit hook blocks the commit.

## Quick Start (Recommended Workflow)

### 1. Put your export ZIP into `zips/`

Example:

```bash
cp ~/Downloads/chatgpt_export.zip zips/
```

### 2. Generate a dossier from recent conversations

```bash
cgpt recent 30 --split --name "project-name"
```

What happens:

- If `extracted/` is empty, `cgpt` auto-extracts the newest ZIP from `zips/`.
- You get an interactive selection list.
- Output is written under `dossiers/project-name/`.

### 3. Upload the working file to ChatGPT

With `--split`, two TXT files are created:

- `<name>.txt` (raw)
- `<name>__working.txt` (cleaned)

Use the `__working.txt` file for ChatGPT.

## Command Overview

### Extract / Index

```bash
cgpt extract [path/to/export.zip]
cgpt x [path/to/export.zip]         # alias
cgpt index                          # rebuild or update search index
cgpt latest-zip                     # print newest ZIP in zips/
```

Notes:

- `extract` without a path uses the newest ZIP in `zips/`.
- Running just `cgpt` (no subcommand) is equivalent to `extract` with newest ZIP.

### Build a combined dossier by recency

```bash
cgpt recent 30 --split --name "thesis"
cgpt r 30 --split --name "thesis"  # alias
```

Useful flags:

- `--all`: skip prompt and include every shown conversation.
- `--mode excerpts --context 2`: include only matching segments with context.
- `--format txt md docx`: request multiple output formats.

### Build a combined dossier by search terms

```bash
cgpt quick "topic"
cgpt q "topic"                     # alias
cgpt q --where all --split "policy" "brief"
cgpt q --and --split "term1" "term2"
```

Useful flags:

- `--where title|messages|all` controls where matching happens.
- `--ids-file <file>` allows non-interactive selection input.
- `--split` creates raw + working TXT (cleaned) variants.

### Build a combined dossier from explicit IDs

```bash
cgpt build-dossier \
  --ids 123abc 456def \
  --topic "project-topic" \
  --split \
  --name "project"

cgpt d --ids 123abc 456def --mode full --split --name "project"  # alias
```

Important for `build-dossier`:

- You must provide `--ids` and/or `--ids-file`.
- IDs are space-separated, not comma-separated.
- In `--mode excerpts`, you must provide `--topic` and/or `--topics`.
- In `--mode full`, topic flags are optional.

### Generate one file per conversation ID

```bash
cgpt make-dossiers --ids 123abc 456def
cgpt make-dossiers --ids-file selected_ids.txt --format txt md
```

This command writes separate files per conversation, not one combined dossier.

### Discovery and search helpers

```bash
cgpt ids
cgpt i                               # alias for ids
cgpt find "keyword"
cgpt f "keyword"                    # alias for find
cgpt search "keyword"
cgpt search --where messages "keyword"
cgpt search --terms alpha beta --and --where all
```

## Interactive Selection Input

For `recent` and `quick`, you can select with:

- Single numbers: `3`
- Multiple numbers: `1 4 9`
- Ranges: `2-6`
- Mixed: `1-3 7 10-12`
- `all`
- Raw conversation IDs (if they are in the shown list)

## Output Layout and Naming

Without `--name`:

```text
dossiers/
├── dossier__topic__YYYYMMDD_HHMMSS.txt
└── dossier__topic__YYYYMMDD_HHMMSS__working.txt   # only with --split
```

With `--name "thesis"`:

```text
dossiers/
└── thesis/
    ├── YYYY-MM-DD_HHMMSS.txt
    └── YYYY-MM-DD_HHMMSS__working.txt             # only with --split
```

## Flags That Matter Most

- `--split`: create both raw and cleaned working TXT files.
- `--name "X"`: group output under `dossiers/X/`.
- `--where all`: search titles and messages.
- `--mode excerpts --context N`: narrower dossier focused on matched segments.
- `--format txt md docx`: choose output types.
- `--no-dedup`: disable deduplication in working output.
- `--home /path/to/home`: override auto home detection.
- `--quiet`: suppress non-error output.

Important `--split` behavior:

- `--split` only produces a working file when TXT output is being generated.
- If you use only `--format md` or only `--format docx`, no `__working.txt` is created.

## Advanced Filter Inputs

These options are supported on `recent`/`r`, `quick`/`q`, and `build-dossier`/`d`:

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

CLI quirk to know:

- `--topic`/`--topics` are only required when `--mode excerpts` is used.

## Home Resolution and Environment Variables

Home folder resolution order:

1. `--home`
2. `CGPT_HOME`
3. Auto-discovery from current directory and parents

Supported environment variables:

- `CGPT_HOME`: explicit home path.
- `CGPT_DEFAULT_MODE`: `full` or `excerpts`.
- `CGPT_FORCE_COLOR`: `1/true/yes/on` or `0/false/no/off`.

## Troubleshooting

### `ERROR: Missing folder: ... Expected: zips/, extracted/, dossiers/`

Create required top-level folders:

```bash
mkdir -p zips extracted dossiers
```

### `ERROR: No ZIPs found in .../zips`

Put at least one ChatGPT export ZIP into `zips/`.

### `ERROR: No JSON found under ...`

Your export is not extracted yet, or `--root` points to the wrong place.

Fix:

```bash
cgpt extract
```

Then retry your command.

### `ERROR: Provide --topic and/or --topics`

This only applies when using excerpts mode (`--mode excerpts`).

### `ERROR: Provide --ids and/or --ids-file`

`build-dossier` and `make-dossiers` require explicit conversation IDs.

### `ModuleNotFoundError: No module named 'docx'`

Install optional DOCX dependency:

```bash
pip install python-docx
```

## Automated Tests

Run the CLI critical-path suite:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

This suite currently covers selection parsing and output generation for:

- `quick`
- `recent`
- `make-dossiers`

## Suggested Features (Roadmap)

The items below track suggested improvements discussed for this project.

Status labels:

- `Implemented`: available in the current CLI.
- `Planned`: documented intent only; not available yet.

| Feature | Status | Notes |
| --- | --- | --- |
| Automated CLI critical-path tests | `Implemented` | Available via `python -m unittest discover -s tests -p "test_*.py" -v`; covers core selection parsing and output generation paths. |
| `cgpt init` command | `Planned` | Would create/verify `zips/`, `extracted/`, and `dossiers/`, and optionally scaffold defaults. |
| `--redact` mode | `Planned` | Would scrub sensitive patterns (for example emails/phones/tokens) from generated dossiers before sharing. |
| `--json` output for discovery/search commands | `Planned` | Would add machine-readable output mode for `ids`, `find`, and `search` to improve scripting/automation workflows. |
| Token-aware chunking (`--max-tokens`) | `Planned` | Would split large `__working` outputs into chunked files sized for upload constraints. |

Important:

- Planned items are not implemented yet and should not be relied on in production workflows.

## Safety Notes

- This tool processes local files; it does not send your exports to external services.
- Your ChatGPT exports may include personal/sensitive data.
- Review files before sharing.
- See `SECURITY.md` for contributor and data-handling guidance.

## Maintainer Note

Documentation maintenance rules are defined in `RELEASING.md`.
The markdown set is intentionally limited to:

- `README.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `RELEASING.md`
