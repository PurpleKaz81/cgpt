# Security Policy

## Overview

This repository has been audited for sensitive data and is safe for public access. This document outlines the security measures in place and best practices for contributors.

## Security Audit Summary

**Last Audit Date:** February 2026  
**Status:** ✅ Safe for public repository

### What Was Checked

- ✅ No hardcoded API keys, tokens, or secrets
- ✅ No passwords or credentials in source code
- ✅ No private keys or certificates
- ✅ No database connection strings with credentials
- ✅ No email addresses in source files
- ✅ Configuration files contain only non-sensitive settings
- ✅ .gitignore properly configured to prevent sensitive data commits

## Data Protection Measures

### 1. .gitignore Configuration

The repository's `.gitignore` is configured to prevent accidental commits of:

- **User Data Directories:**
  - `extracted/` - ChatGPT conversation exports
  - `dossiers/` - Generated research dossiers
  - `zips/` - ChatGPT ZIP files

- **Sensitive Files:**
  - Environment files (`.env`, `.env.*`, `*.env`)
  - Secret/credential files (`*secret*`, `*credential*`, `*password*`)
  - Private keys (`*.key`, `*.pem`, `*.p12`, `*.pfx`)
  - Database files (`*.db`, `*.sqlite`, `*.sqlite3`)

- **Development Files:**
  - Python cache (`__pycache__/`, `*.pyc`, `*.pyo`)
  - Virtual environments (`.venv/`, `venv/`)
  - IDE files (`.vscode/`, `.idea/`)
  - Temporary files (`*.tmp`, `*.log`)

### 2. Environment Variables

The application uses environment variables for configuration:
- `CGPT_HOME` - Path to working directory
- `CGPT_FORCE_COLOR` - Color output control
- `CGPT_DEFAULT_MODE` - Default operation mode

**No secrets or credentials are required** by this application.

### 3. Local Data Storage

All user data (ChatGPT exports, dossiers, databases) is stored in directories that are:
- Explicitly excluded from version control
- Kept in local directories only
- Never pushed to the repository

## Best Practices for Contributors

### Before Committing

1. **Never commit sensitive data:**
   - API keys or tokens
   - Passwords or credentials
   - Personal information
   - Private keys or certificates

2. **Check your changes:**
   ```bash
   git diff
   git status
   ```

3. **Verify .gitignore is working:**
   ```bash
   git add -A -n  # Dry-run to see what would be added
   ```

### Safe Configuration

- Use environment variables for any configuration
- Never hardcode credentials in source code
- Keep sample/template files generic (no real data)

## Reporting Security Issues

If you discover a security vulnerability in this repository:

1. **Do NOT** open a public issue
2. Contact the repository owner directly via GitHub
3. Provide details about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## Security Features

### What This Tool Does NOT Store

- API keys or authentication tokens
- User credentials
- Personal information beyond what's in ChatGPT exports (which users provide)
- Network credentials
- Cloud service credentials

### What Users Should Know

1. **ChatGPT exports may contain:**
   - Your conversation history
   - Any personal information you shared with ChatGPT
   - Links and references you discussed

2. **Keep your exports secure:**
   - Store exports in the designated directories (`zips/`, `extracted/`, `dossiers/`)
   - These directories are automatically excluded from git
   - Do not share your exports unless you've reviewed the content

3. **Before sharing a dossier:**
   - Review the generated files
   - Ensure no sensitive information is included
   - Remove any personal data if necessary

## Compliance

This repository follows security best practices:
- No credentials in source code
- Proper .gitignore configuration
- Environment variable usage for configuration
- Clear documentation of data handling

---

**Note:** This is a local tool that processes your ChatGPT exports on your machine. No data is sent to external servers or services.
