# cgpt — ChatGPT Export → Clean Dossier

Turn messy ChatGPT conversation exports into clean, organized research dossiers.

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│  ChatGPT ZIP    │ ──▶ │   cgpt.py   │ ──▶ │  Clean dossier for ChatGPT       │
│  (messy export) │     │             │     │  (no noise, organized sources)   │
└─────────────────┘     └─────────────┘     └──────────────────────────────────┘
```

## 🎯 What Does This Do?

**cgpt** transforms ChatGPT conversation exports into research-grade dossiers by:

1. **Extracting** ChatGPT ZIP files and indexing conversations in SQLite with FTS5 search
2. **Searching & Selecting** conversations by date, keyword, or full-text content search
3. **Cleaning & Organizing** by removing tool noise, fixing citations, deduplicating content
4. **Categorizing Sources** into deliverables, used links, and supplementary references
5. **Building Two Versions**: 
   - Full raw transcript for your records
   - Cleaned working file ready to upload back to ChatGPT

**Perfect for:** Researchers, writers, developers, and anyone managing long-term ChatGPT projects who needs to:
- Combine multiple conversations into a single reference document
- Share clean context with ChatGPT without noise
- Track sources and deliverables across conversations
- Build searchable archives of your AI interactions

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

### Search (Advanced FTS5)

```bash
cgpt search "machine learning"           # Search in titles
cgpt search --where messages "algorithm" # Search in message content
cgpt search --where all "neural"         # Search everywhere
```

### Find (Simple Search)

```bash
cgpt find "thesis"          # Case-insensitive title search
cgpt f "research"           # Short form
```

### Other Commands

```bash
cgpt make-dossiers --recent 10          # Generate individual files (not combined)
cgpt index                              # Rebuild search index
cgpt latest-zip                         # Show path to newest ZIP
cgpt                                    # No command = auto-extract newest ZIP
```

---

## 🚀 Advanced Features

### Excerpts Mode (Topic Extraction)

Instead of full conversations, extract only relevant portions:

```bash
# Extract only portions matching your search, with ±2 messages context
cgpt q --mode excerpts --context 2 --split --name "ml" "machine learning"

# Full conversation (default)
cgpt q --mode full --split --name "ml" "machine learning"
```

**When to use excerpts:**
- Long conversations where only some parts are relevant
- Building focused dossiers from sprawling discussions
- Reducing token count for ChatGPT uploads

### Output Formats

```bash
# Plain text (default)
cgpt r 30 --split --format txt

# Markdown with headers and formatting
cgpt r 30 --split --format md

# Microsoft Word document (requires python-docx)
cgpt r 30 --split --format docx
```

### Custom Configuration

Create your own `my-config.json` based on `config.json` to customize:

```json
{
  "segment_scoring": {
    "mechanism_terms": ["analysis", "finding", "decision"],
    "bridging_terms": ["next steps", "follow-up"],
    "min_score": 0.5
  },
  "thread_filters": {
    "include": {"research": ["study", "analysis"]},
    "exclude": ["recipe", "weather"]
  }
}
```

Then use it:
```bash
cgpt r 30 --config my-config.json --split
```

### Deliverable Patterns

Customize what gets highlighted as "deliverables":

```bash
# Create patterns.txt with one pattern per line
echo "## " > patterns.txt
echo "Decision:" >> patterns.txt
echo "Draft:" >> patterns.txt

cgpt r 30 --patterns-file patterns.txt --split
```

### Source Prioritization

Mark URLs you've already used so they appear first in sources:

```bash
# Create used-links.txt with one URL per line
echo "https://example.com/important-source" > used-links.txt

cgpt r 30 --used-links-file used-links.txt --split
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

# Advanced FTS5 search
cgpt search --where all "algorithm"

# Extract only relevant excerpts with context
cgpt r 30 --mode excerpts --context 3 --split --name "project"

# Output as Markdown
cgpt r 30 --split --format md --name "project"

# Extract a new ChatGPT export (or just run 'cgpt' with no args)
cgpt extract conversations.zip

# List all conversations
cgpt ids | head -50

# Find by simple title search
cgpt find "thesis"

# Rebuild search index
cgpt index
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
- Standard library (no dependencies for basic use)
- **Optional:** `python-docx` (only needed if using `--format docx`)

### Setup

```bash
# 1. Put cgpt.py somewhere permanent
mkdir -p ~/Documents/chatgpt_exports
cp cgpt.py ~/Documents/chatgpt_exports/
cd ~/Documents/chatgpt_exports

# 2. Install optional dependencies (if needed)
pip install python-docx  # Only if you want --format docx

# 3. Add alias to your shell (bash or zsh)
echo 'alias cgpt="python3 ~/Documents/chatgpt_exports/cgpt.py"' >> ~/.zshrc
source ~/.zshrc
# For bash: use ~/.bashrc instead of ~/.zshrc

# 4. Test it
cgpt --help
```

### Environment Variables

You can customize cgpt's behavior with these environment variables:

```bash
export CGPT_HOME="/path/to/your/chatgpt_exports"  # Override home directory
export CGPT_DEFAULT_MODE="excerpts"               # Set default mode (full or excerpts)
```

---

## 🎛️ All Flags Reference

| Flag | Commands | What it does |
|------|----------|--------------|
| `--split` | r, q, d | **Creates both raw + working files** |
| `--name "X"` | r, q, d | Organizes into `dossiers/X/` folder |
| `--where all` | q, search | Search content, not just titles |
| `--all` | r, q | ⚠️ Skip selection (use with caution) |
| `--mode full` | r, q, d | Include full conversations (default) |
| `--mode excerpts` | r, q, d | Only topic-matching snippets with context |
| `--context N` | r, q, d | Include ±N messages around matches (excerpts mode) |
| `--format txt` | r, q, d | Output as plain text (default) |
| `--format md` | r, q, d | Output as Markdown |
| `--format docx` | r, q, d | Output as Word (needs python-docx) |
| `--dedup` | r, q, d | Remove duplicates (default: enabled) |
| `--no-dedup` | r, q, d | Keep duplicates |
| `--color` | all | Force colored output |
| `--no-color` | all | Disable colored output |
| `--config X.json` | r, q, d | Use custom filter config |
| `--patterns-file X` | r, q, d | Custom deliverable patterns |
| `--used-links-file X` | r, q, d | Prioritize these URLs in sources |
| `--no-index` | extract | Skip auto-indexing after extraction |

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

**Q: What's the difference between `--mode full` and `--mode excerpts`?**
A: `full` includes entire conversations. `excerpts` extracts only relevant portions based on topic matching, with `--context N` controlling how much surrounding context to include.

**Q: Do I need to manually extract ZIPs?**
A: No! Running `cgpt` with no command automatically extracts the newest ZIP from `zips/` folder.

**Q: What's config.json for?**
A: Advanced filtering configuration. It defines:
- Segment scoring criteria (mechanism terms, bridging terms)
- Thread filters (include/exclude patterns)
- Deliverable extraction patterns
- Control layer sections for research-grade output

You can use a custom config with `--config your-config.json`.

**Q: Where does cgpt look for files?**
A: It searches for a folder with `zips/`, `extracted/`, and `dossiers/` subfolders, starting from:
1. Current directory
2. Parent directories (up to 8 levels)
3. Directory containing cgpt.py

You can override with `CGPT_HOME` environment variable.

---

## 🔍 Troubleshooting

### "ERROR: No conversations.json found"

You need to extract a ChatGPT export first:
```bash
cgpt extract path/to/conversations.zip
# Or just put the ZIP in zips/ folder and run:
cgpt
```

### "ERROR: Directory layout missing"

cgpt expects this structure:
```
your-folder/
├── zips/
├── extracted/
└── dossiers/
```

Create it manually or let cgpt create it in the current directory:
```bash
mkdir -p zips extracted dossiers
```

### "ModuleNotFoundError: No module named 'docx'"

You're using `--format docx` without python-docx installed:
```bash
pip install python-docx
```

### "No matching conversations found"

Your search returned nothing. Try:
- Broader keywords
- Using `--where all` to search content
- Running `cgpt ids` to see all available conversations

### Interactive selection isn't working

Make sure you're entering valid formats:
- Single: `3`
- Multiple: `1 3 7`
- Range: `2-5`
- Mixed: `1-3 7 9-11`
- All: `all`

### Colors look weird in my terminal

Disable them:
```bash
cgpt r 30 --no-color --split
```

Or set as default:
```bash
export CGPT_DEFAULT_COLOR=false
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
