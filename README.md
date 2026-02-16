# cgpt: Beginner Guide (Idiot-Proof)

If you can copy and paste commands, you can use this tool.

`cgpt` takes your ChatGPT export ZIP and turns it into clean text files you can work with.

If you want full technical details and every flag, go to [TECHNICAL.md](TECHNICAL.md).

## Project Snapshot

- Mission: transform previous AI chats into reusable context dossiers for new conversations.
- Product posture: local-first, single-user CLI in `v0.x`.
- Current hard constraint: supported ingestion is ChatGPT export ZIP data.
- Product strategy and future horizons live in [`docs/roadmap/shared-roadmap.md`](docs/roadmap/shared-roadmap.md).

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
- Pre-commit hook blocks accidental commit of private config files.

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
git add cgpt.py README.md TECHNICAL.md CHANGELOG.md SECURITY.md RELEASING.md config.json .gitignore .githooks/pre-commit
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

`ERROR: No JSON found under ...`

Fix:

```bash
cgpt extract
```

`ERROR: Unsafe ZIP member path detected: ...`

Cause: the ZIP contains unsafe extraction paths.  
Fix: re-export the archive from ChatGPT and retry.

`ERROR: Config file not found: ...` or `ERROR: Error loading config: ...`

Cause: explicit `--config` file is missing or invalid JSON.  
Fix: verify path and JSON format.

`ERROR: Failed to read ... file as UTF-8 text: ...`

Cause: IDs/patterns/used-links file is not UTF-8/UTF-8-BOM decodable.  
Fix: re-save the file as UTF-8 (or UTF-8 with BOM).

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

## Where To Go Next

- Complete command and flag reference: [TECHNICAL.md](TECHNICAL.md)
- Scoped docs index (specs, ADRs, runbooks, roadmap notes): [docs/INDEX.md](docs/INDEX.md)
- Security and safe data handling: [SECURITY.md](SECURITY.md)
- Release process (maintainers): [RELEASING.md](RELEASING.md)
- Full change history: [CHANGELOG.md](CHANGELOG.md)

## Safety Reminder

Your ChatGPT exports can contain sensitive personal information.
Review any output before sharing it.
