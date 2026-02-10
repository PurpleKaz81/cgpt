# cgpt — ChatGPT Export → Clean Dossier

Turn messy ChatGPT conversation exports into clean, organized research dossiers.

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│  ChatGPT ZIP    │ ──▶ │   cgpt.py   │ ──▶ │  Clean dossier for ChatGPT       │
│  (messy export) │     │             │     │  (no noise, organized sources)   │
└─────────────────┘     └─────────────┘     └──────────────────────────────────┘
```

---

## ⚡ 30-Second Quick Start

```bash
# 1. Set up alias (one time only)
echo 'alias cgpt="python3 /path/to/cgpt.py"' >> ~/.zshrc && source ~/.zshrc

# 2. Extract your ChatGPT export
cgpt extract conversations.zip

# 3. Build a dossier (interactive menu)
cgpt r 30 --split --name "my-project"
```

**That's it.** Upload the `__working.txt` file to ChatGPT.

---

## 🎯 The Two Commands You Need

```bash
# Browse recent conversations → pick → build dossier
cgpt r 30 --split --name "project-name"

# Search by keyword → pick → build dossier
cgpt q --split --name "project-name" "your search term"
```

### What the flags mean

| Flag | What it does | Required? |
|------|--------------|-----------|
| `--split` | Creates TWO files: full + cleaned for ChatGPT | **YES, always use this** |
| `--name "X"` | Organizes output into `dossiers/X/` folder | Optional but recommended |

---

## 📁 How Output is Organized

```
Without --name:                          With --name "thesis":
─────────────────────────────────        ─────────────────────────────────
dossiers/                                dossiers/
├── dossier__topic__20260204.txt         └── thesis/
└── dossier__topic__20260204__working.txt    ├── 2026-02-04_143022.txt
                                             └── 2026-02-04_143022__working.txt
     (flat, gets messy fast)                      (organized by project)
```

---

## 📄 Which File Goes to ChatGPT?

```
┌────────────────────────────────┐     ┌────────────────────────────────────────┐
│  2026-02-04_143022.txt         │     │  2026-02-04_143022__working.txt        │
│  ───────────────────────────   │     │  ────────────────────────────────────  │
│  • Full raw transcript         │     │  • Tool noise REMOVED                  │
│  • All original messages       │     │  • Citations CLEANED                   │
│  • For YOUR records            │     │  • Duplicates REMOVED                  │
│                                │     │  • Sources ORGANIZED                   │
│  ❌ Don't upload this          │     │  • Navigation INDEX added              │
│                                │     │                                        │
│                                │     │  ✅ UPLOAD THIS TO CHATGPT             │
└────────────────────────────────┘     └────────────────────────────────────────┘
```

---

## 🔧 All Commands

### Extract ZIP

```bash
cgpt extract conversations.zip    # Full command
cgpt x conversations.zip          # Short form
```

### Recent (browse by date)

```bash
cgpt recent 30 --split --name "project"    # Show last 30, pick interactively
cgpt r 30 --split --name "project"         # Short form
cgpt r 50 --split                          # Last 50, no project folder
```

### Quick (search by keyword)

```bash
cgpt quick --split --name "project" "machine learning"     # Full command
cgpt q --split --name "project" "machine learning"         # Short form
cgpt q --split "AI" "neural networks"                      # Multiple keywords
cgpt q --where all --split "deep search"                   # Search content too
```

### Build-Dossier (specific IDs)

```bash
cgpt d --ids abc123,def456 --split --name "project"
```

### List IDs

```bash
cgpt ids                    # List all conversations (newest first)
cgpt ids | head -30         # Last 30 only
cgpt i "keyword"            # Filter by keyword
```

---

## 🎮 Interactive Selection

When you run `cgpt r` or `cgpt q`, you'll see a numbered list:

```
=== 30 Most Recent Conversations ===

  1. 69827cba-...   Adam Curtis Radical Islamists       2026-02-03
  2. 69816199-...   Thinking About MBL and Populism     2026-02-02
  3. 69815055-...   Cambridge Texts in Politics         2026-02-02
  ...

Pick by number (e.g. 1 3 7), range (1-5), or 'all':
```

**Type your selection:**

| Input | Selects |
|-------|---------|
| `3` | Just #3 |
| `1 3 7` | #1, #3, and #7 |
| `2-5` | #2, #3, #4, #5 |
| `1-3 7 9-11` | Mix of ranges and singles |
| `all` | Everything shown |

Then hit Enter → dossier is built.

---

## ⚠️ Common Mistakes

### ❌ Forgot `--split`

```bash
cgpt q "topic"                    # Only creates ONE file (raw only)
```

**Fix:** Always add `--split`:

```bash
cgpt q --split "topic"            # Creates BOTH files ✅
```

### ❌ Used `--all` by accident

```bash
cgpt q --all "topic"              # Skips selection, processes EVERYTHING
```

**Fix:** Don't use `--all` unless you mean it. Use interactive selection instead.

### ❌ Uploaded wrong file

```bash
# You uploaded: dossier__topic__20260204.txt
# Should be:    dossier__topic__20260204__working.txt
```

**Fix:** Always upload the `__working.txt` file.

---

## 📋 Cheat Sheet (Copy/Paste)

```bash
# Most common: browse recent + pick + build clean dossier
cgpt r 30 --split --name "project"

# Search keywords + pick + build clean dossier
cgpt q --split --name "project" "search term"

# Search in content (not just titles)
cgpt q --where all --split --name "project" "search term"

# Extract a new ChatGPT export
cgpt extract conversations.zip

# List all conversations
cgpt ids | head -50
```

---

## 🗂️ Project Structure

```
chatgpt_chat_exports/
├── cgpt.py              # The tool (this is all you need)
├── README.md            # This file
├── config.json          # Optional: advanced filtering config
├── zips/                # Put your ChatGPT ZIPs here
├── extracted/           # Extracted conversations go here
└── dossiers/            # Your dossiers appear here
    ├── thesis/          # Project folders (from --name)
    ├── research/
    └── recent/
```

---

## 🔧 Installation

### Requirements

- Python 3.8+
- No pip installs needed (standard library only)

### Setup

```bash
# 1. Put cgpt.py somewhere permanent
mkdir -p ~/Documents/chatgpt_exports
cp cgpt.py ~/Documents/chatgpt_exports/

# 2. Add alias to your shell
echo 'alias cgpt="python3 ~/Documents/chatgpt_exports/cgpt.py"' >> ~/.zshrc
source ~/.zshrc

# 3. Test it
cgpt --help
```

---

## 🎛️ All Flags Reference

| Flag | Commands | What it does |
|------|----------|--------------|
| `--split` | r, q, d | **Creates both raw + working files** |
| `--name "X"` | r, q, d | Organizes into `dossiers/X/` folder |
| `--where all` | q | Search content, not just titles |
| `--all` | r, q | ⚠️ Skip selection (use with caution) |
| `--format md` | r, q, d | Output as Markdown |
| `--format docx` | r, q, d | Output as Word (needs python-docx) |
| `--no-dedup` | r, q, d | Keep duplicates (default: remove) |
| `--config X.json` | r, q, d | Use custom filter config |
| `--patterns-file X` | r, q, d | Custom deliverable patterns |
| `--used-links-file X` | r, q, d | Prioritize these URLs in sources |

---

## ❓ FAQ

**Q: Which file do I give ChatGPT?**
A: The `__working.txt` file. Always.

**Q: Why do I need `--split`?**
A: Without it, you only get the raw file. `--split` creates the cleaned version for ChatGPT.

**Q: What's `--name` for?**
A: Organizes your dossiers into project folders. Without it, everything dumps into `dossiers/` flat.

**Q: How do I search conversation content, not just titles?**
A: Add `--where all`:
```bash
cgpt q --where all --split "keyword"
```

**Q: What gets removed in the working file?**
A: JSON tool calls, citation markers, UI noise, duplicates. Sources get categorized.

**Q: Can I combine flags?**
A: Yes, order doesn't matter:
```bash
cgpt r 30 --split --name "project"
cgpt r 30 --name "project" --split    # Same result
```

---

## 🆘 Help

```bash
cgpt --help           # General help
cgpt r --help         # Help for 'recent' command
cgpt q --help         # Help for 'quick' command
cgpt d --help         # Help for 'build-dossier' command
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   cgpt r 30 --split --name "project"                                │
│   ─────────────────────────────────────                             │
│                                                                     │
│   This one command:                                                 │
│   1. Shows your 30 most recent conversations                        │
│   2. Lets you pick which ones to include                            │
│   3. Builds a clean dossier for ChatGPT                             │
│   4. Organizes it in dossiers/project/                              │
│                                                                     │
│   Then upload the __working.txt file to ChatGPT. Done.              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
