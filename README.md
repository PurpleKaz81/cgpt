# cgpt: Beginner Guide (Idiot-Proof)

If you can copy and paste commands, you can use this tool.

`cgpt` takes your ChatGPT export ZIP and compiles it into reusable context dossiers you can carry across sessions.

If you want full technical details and every flag, go to [TECHNICAL.md](TECHNICAL.md).

## Project Snapshot

- Mission: transform previous AI chats into reusable context dossiers for new conversations.
- Product posture: local-first, single-user CLI in `v0.x`.
- Current hard constraint: supported ingestion is ChatGPT export ZIP data.
- Product strategy and future horizons live in [`docs/roadmap/shared-roadmap.md`](docs/roadmap/shared-roadmap.md).

## What cgpt Is Really For

- Continuity first: keep reasoning continuity across sessions instead of restarting from zero each time.
- Deterministic local build flow: run the same inputs and config to produce consistent context artifacts.
- Reliable handoff: package context so a future you (or another person/model session) can resume work with less ambiguity.

Coming next: roadmap initiative `R15` positions quality gates as a reliability layer for dossier readiness checks. See [`docs/roadmap/shared-roadmap.md`](docs/roadmap/shared-roadmap.md).

## What This Tool Is (In Plain English)

You export your ChatGPT data from ChatGPT.
You place that ZIP file in this project.
`cgpt` reads it and creates organized files you can reuse.

Simple picture:

```text
ChatGPT export ZIP
        |
        v
     zips/
        |
        v
     cgpt
      / \
     v   v
extracted/  dossiers/
(raw data)  (clean outputs you use)
```

Folder picture:

```text
cgpt/
|- cgpt.py
|- zips/       <- put your ChatGPT ZIP here
|- extracted/  <- cgpt unpacks exports here
`- dossiers/   <- cgpt writes final output files here
```

## 5-Minute First Setup

1. Open Terminal (Warp is fine).
2. Go to this project folder.

```bash
cd /path/to/cgpt
```

1. Check the tool works.

```bash
python3 cgpt.py --help
```

1. Optional quality-of-life alias (so you can type `cgpt`):

```bash
echo 'alias cgpt="python3 /path/to/cgpt/cgpt.py"' >> ~/.zshrc
source ~/.zshrc
```

Replace `/path/to/cgpt` with your actual folder path.

1. Test alias:

```bash
cgpt --help
```

## First Real Use (Step by Step)

### Step 1. Put your ChatGPT ZIP in `zips/`

Example:

```bash
cp ~/Downloads/chatgpt_export.zip zips/
```

### Step 2. Build a dossier from recent chats

```bash
cgpt recent 30 --name "my-project" --split
```

What this means:

- `recent 30`: show your 30 most recent conversations.
- `--name "my-project"`: save output in `dossiers/my-project/`.
- `--split`: create both raw and cleaned files.

### Step 3. Choose conversations when prompted

When cgpt asks what to include, you can type:

- `all` for everything shown
- `1 2 5` for specific items
- `1-10` for a range
- `1-3 8 12-15` for mixed selections

### Step 4. Use the cleaned output file

After generation, upload the file ending in `__working.txt` to ChatGPT.

Example path:

```text
dossiers/my-project/YYYY-MM-DD_HHMMSS__working.txt
```

## Which Command Should You Use?

```text
Need most recent chats?
  -> cgpt recent 30 --split

Need chats about a keyword/topic?
  -> cgpt q "topic"

Need keyword + only recent N chats?
  -> cgpt q --recent 25 "topic"

Need keyword + last N days only?
  -> cgpt q --days 7 "topic"

Already know exact conversation IDs?
  -> cgpt build-dossier --ids <id1> <id2> --split
```

## Copy/Paste Command Pack

Most common commands:

```bash
cgpt recent 30 --split
cgpt q "topic"
cgpt q --recent 25 "topic"
cgpt q --days 7 "topic"
cgpt build-dossier --ids <id1> <id2> --split
cgpt make-dossiers --ids <id1> <id2>
```

Useful helpers:

```bash
cgpt init
cgpt latest-zip
cgpt extract
cgpt index
cgpt ids
cgpt find "keyword"
cgpt search "keyword"
```

## Private vs Public (Important)

You can keep one public repo and still have private personal settings.

Rule:

- Public defaults live in tracked `config.json`.
- Personal/private rules live in untracked `config.personal.json`.

Setup once:

```bash
cp config.json config.personal.json
git config --local core.hooksPath .githooks
```

Use your private config in commands:

```bash
cgpt q --config config.personal.json "topic"
```

Why this is safe:

- `config.personal.json` is git-ignored.
- Pre-commit hook blocks accidental commit of private config files, common secret/credential filenames, and sensitive files under `zips/`, `extracted/`, and `dossiers/` (except `.gitkeep` placeholders).

## Pull / Push / Merge Without Leaking Private Data

Use this exact safe routine:

1. Check what changed:

```bash
git status --short
```

1. Pull latest main:

```bash
git pull origin main
```

1. Stage only public files explicitly (never `git add .`):

```bash
git add cgpt.py config.json requirements.txt
git add README.md TECHNICAL.md SECURITY.md CHANGELOG.md RELEASING.md CONTRIBUTING.md LICENSE
git add .github/CODEOWNERS .github/dependabot.yml
git add .github/workflows/tests.yml .github/workflows/docs-guard.yml .github/workflows/lint.yml
git add .ruff.toml .markdownlint.yml .gitignore .githooks/pre-commit
# if scoped docs changed, add them explicitly too:
git add docs/INDEX.md docs/specs docs/adr docs/runbooks docs/roadmap
```

1. Verify staged files:

```bash
git diff --cached
```

1. Commit and push:

```bash
git commit -m "your message"
git push origin <branch>
```

## If Something Fails (No Panic)

`ERROR: Missing folder: ... Expected: zips/, extracted/, dossiers/`

Fix (recommended):

```bash
cgpt init
```

Fallback:

```bash
mkdir -p zips extracted dossiers
```

`ERROR: No ZIPs found in .../zips`

Fix: place at least one export ZIP into `zips/`.

`ERROR: No conversations JSON found under ...`

Fix:

```bash
cgpt extract
```

Cause: extracted folder does not contain a valid conversations JSON payload.

`ERROR: Unsafe ZIP member path detected: ...`

Cause: the ZIP contains unsafe extraction paths.  
Fix: re-export the archive from ChatGPT and retry.

`ERROR: Special ZIP member type is not allowed: ...` or ZIP size/member limit errors

Cause: ZIP includes symlink/special entries or exceeds hardening limits for member count/uncompressed size.  
Fix: re-export and retry with a safe archive.

`ERROR: patterns file not found: ...` or `ERROR: used-links file not found: ...`

Cause: you passed `--patterns-file`/`--used-links-file` with a missing path.  
Fix: verify the file path or remove the flag.

`ERROR: Config file not found: ...`, `ERROR: Error loading config: ...`, or `ERROR: Invalid config schema ...`

Cause: explicit `--config` file is missing, invalid JSON, or has unsupported keys/wrong types.  
Fix: verify path, JSON syntax, and supported schema keys/types.

`ERROR: Failed to read ... file as UTF-8 text: ...`

Cause: IDs/patterns/used-links file is not UTF-8/UTF-8-BOM decodable.  
Fix: re-save the file as UTF-8 (or UTF-8 with BOM).

`ERROR: argument --context: --context must be between 0 and 200`

Cause: `--context` is negative or too large.  
Fix: use a value in range `0..200`.

`ERROR: --name must contain at least one safe alphanumeric character after normalization.`

Cause: `--name` was effectively empty after cleanup (for example `"!!!"`).  
Fix: provide a name with letters or numbers.

`ERROR: Duplicate conversation ID(s) found in export: ...`

Cause: export payload contains repeated conversation IDs and selection would be ambiguous.  
Fix: use a clean export source and retry.

`ModuleNotFoundError: No module named 'docx'`

Fix:

```bash
pip install python-docx
```

Note: if you request only DOCX output before installing this dependency, the command will fail.

## Product Status and Roadmap

Current-state source of truth:

- [`docs/specs/current-capabilities.md`](docs/specs/current-capabilities.md)

Roadmap source of truth (shared by users, contributors, and AI agents):

- [`docs/roadmap/shared-roadmap.md`](docs/roadmap/shared-roadmap.md)

Vision and non-goals:

- [`docs/specs/product-vision.md`](docs/specs/product-vision.md)

Agent reference:

- [`docs/runbooks/ai-agent-reference.md`](docs/runbooks/ai-agent-reference.md)

## Project Governance

- Contribution workflow and local quality checks: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Project license: [`LICENSE`](LICENSE)
- Ongoing engineering quality optimization ledger: [`docs/runbooks/engineering-quality-backlog.md`](docs/runbooks/engineering-quality-backlog.md)

## Where To Go Next

- Complete command and flag reference: [TECHNICAL.md](TECHNICAL.md)
- Scoped docs index (specs, ADRs, runbooks, roadmap notes): [docs/INDEX.md](docs/INDEX.md)
- Security and safe data handling: [SECURITY.md](SECURITY.md)
- Release process (maintainers): [RELEASING.md](RELEASING.md)
- Full change history: [CHANGELOG.md](CHANGELOG.md)

## Safety Reminder

Your ChatGPT exports can contain sensitive personal information.
Review any output before sharing it.
