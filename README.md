# cgpt: Start Here

`cgpt` turns your ChatGPT export ZIP into clean dossier files you can reuse in new ChatGPT chats.

This page is intentionally non-technical. If you want every command, flag, and edge case, see [TECHNICAL.md](TECHNICAL.md).

## What This Tool Does

You give `cgpt` a ChatGPT export ZIP file.

`cgpt` then:

1. Extracts it
2. Lets you pick conversations
3. Builds clean output files inside `dossiers/`

Visual flow:

```text
ChatGPT ZIP -> zips/ -> cgpt -> extracted/ + dossiers/
```

## 2-Minute Setup

From this repo folder:

```bash
python3 cgpt.py --help
```

Optional alias (so you can type `cgpt` instead of `python3 cgpt.py`):

```bash
echo 'alias cgpt="python3 /path/to/cgpt/cgpt.py"' >> ~/.zshrc
source ~/.zshrc
```

## Daily Workflow (Copy/Paste)

1. Put your export ZIP in `zips/`.

```bash
cp ~/Downloads/chatgpt_export.zip zips/
```

2. Build a dossier from recent conversations.

```bash
cgpt recent 30 --name "my-project" --split
```

3. Upload the `__working.txt` file to ChatGPT.

Example output location:

```text
dossiers/my-project/YYYY-MM-DD_HHMMSS__working.txt
```

## Most Common Commands

Quick search by keyword:

```bash
cgpt q "topic"
```

Quick search but only in recent conversations:

```bash
cgpt q --recent 25 "topic"
```

Quick search but only in last N days:

```bash
cgpt q --days 7 "topic"
```

Build from exact IDs:

```bash
cgpt build-dossier --ids <id1> <id2> --name "my-project" --split
```

## Personal vs Public Config (One Repo)

If you keep personal writing constraints, do this once:

```bash
cp config.json config.personal.json
```

Then use your private config in commands:

```bash
cgpt q --config config.personal.json "topic"
```

`config.personal.json` is intentionally ignored by git.

## Full Documentation

- Full command reference and technical details: `TECHNICAL.md`
- Security/data-handling policy: `SECURITY.md`
- Release process for maintainers: `RELEASING.md`
- Version history: `CHANGELOG.md`

## Safety Reminder

Your exports can contain sensitive personal information.

Before sharing any generated dossier, review it first.

For details, see `SECURITY.md`.
