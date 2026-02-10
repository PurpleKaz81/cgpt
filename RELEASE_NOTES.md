# cgpt v0.1.0 - Initial Feedback Release

**This is a pre-release version intended for gathering feedback from the community.** 🚧

Turn messy ChatGPT conversation exports into clean, organized research dossiers.

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│  ChatGPT ZIP    │ ──▶ │   cgpt.py   │ ──▶ │  Clean dossier for ChatGPT       │
│  (messy export) │     │             │     │  (no noise, organized sources)   │
└─────────────────┘     └─────────────┘     └──────────────────────────────────┘
```

## 🎯 What This Tool Does

cgpt is a command-line tool that:
- **Extracts** ChatGPT conversation exports from ZIP files
- **Organizes** conversations with interactive browse and search
- **Cleans** transcripts by removing tool noise, fixing citations, and removing duplicates
- **Builds** structured dossiers ready to upload back to ChatGPT
- **Manages** research projects with organized folder structure

## ⚡ Quick Start

```bash
# 1. Download cgpt.py from this release
# 2. Set up alias (one time only)
echo 'alias cgpt="python3 /path/to/cgpt.py"' >> ~/.zshrc && source ~/.zshrc

# 3. Extract your ChatGPT export
cgpt extract conversations.zip

# 4. Build a dossier (interactive menu)
cgpt r 30 --split --name "my-project"
```

## 📦 What's Included

- **cgpt.py** - The main tool (single Python file, no external dependencies required)
- **README.md** - Comprehensive documentation
- **config.json** - Default research-focused configuration
- **requirements.txt** - Optional: for DOCX export support

## ✨ Key Features

### Interactive Selection
Browse recent conversations or search by keyword, then select which ones to include:
```bash
cgpt r 30 --split --name "thesis"        # Browse 30 recent
cgpt q --split --name "research" "AI"    # Search for "AI"
```

### Dual Output Files
- **Full transcript** (.txt) - Complete conversation for your records
- **Working file** (__working.txt) - Cleaned version ready for ChatGPT

### Smart Cleaning
- Removes JSON tool call noise
- Cleans up citation markers
- Removes duplicate content
- Organizes sources by category
- Adds navigation index for large dossiers

### Project Organization
Use `--name` to organize dossiers into project folders:
```bash
dossiers/
├── thesis/
├── research/
└── work-project/
```

## 🔧 Requirements

- **Python 3.8+** (no pip installs required for basic functionality)
- **Optional**: `python-docx` for DOCX export support

## 📖 Documentation

See [README.md](https://github.com/PurpleKaz81/cgpt/blob/main/README.md) for:
- Complete command reference
- Interactive selection guide
- All available flags and options
- FAQ and troubleshooting
- Common mistakes and how to fix them

## 🆘 Getting Help

```bash
cgpt --help           # General help
cgpt r --help         # Help for 'recent' command
cgpt q --help         # Help for 'quick' command
```

## 💬 Feedback Welcome!

This is an early release, and I'm looking for feedback on:
- ✅ **What works well** - Features you find useful
- 🐛 **What breaks** - Bugs, errors, or unexpected behavior
- 💡 **What's missing** - Features you'd like to see
- 📝 **Documentation** - What's unclear or needs improvement
- 🎨 **UX/UI** - Command naming, output formatting, etc.

Please open an issue on GitHub or reach out with your thoughts!

## 📝 Known Limitations

- No automated tests yet (coming in future releases)
- Limited error handling in some edge cases
- Performance not optimized for very large exports (1000+ conversations)

## 🔜 Future Plans

- Automated test suite
- Better error messages and validation
- Performance improvements for large datasets
- More export format options
- Enhanced source extraction and categorization
- Configuration templates for different use cases

## 📄 License

[Add license information here]

---

**Note**: This is version 0.1.0 - not production-ready, but functional for everyday use. Breaking changes may occur in future versions as we refine the API based on feedback.
