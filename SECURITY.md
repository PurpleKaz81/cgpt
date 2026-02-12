# Security Policy

## Scope

`cgpt` is a local CLI tool that processes ChatGPT exports on your machine.

This repository does not require API keys, credentials, or cloud accounts.

## Data Handling Model

`cgpt` reads and writes data in these folders:

- `zips/`: original ChatGPT export ZIP files.
- `extracted/`: extracted export data and search index (`cgpt_index.db`).
- `dossiers/`: generated dossier outputs.

These directories can contain sensitive personal data from your conversations.

## Git Protection Rules

`.gitignore` is configured to:

- Keep folder placeholders tracked:
  - `zips/.gitkeep`
  - `extracted/.gitkeep`
  - `dossiers/.gitkeep`
- Ignore actual user content under those folders.

Current pattern style:

```gitignore
/zips/**
!/zips/.gitkeep
/extracted/**
!/extracted/.gitkeep
/dossiers/**
!/dossiers/.gitkeep
```

It also ignores common sensitive and local-only files (env files, key files, DB files, virtual envs, IDE folders, temp files).

Private config protection:

- Keep public defaults in tracked `config.json`.
- Keep personal rules in untracked files such as `config.personal.json` or `*.private.json`.
- `.gitignore` ignores these private config patterns.
- `.git/info/exclude` can add local-only protection in each clone.

Pre-commit safety net:

- Hook file: `.githooks/pre-commit`
- Purpose: block commits that include private config files (`config.personal.json`, `*.private.json`, etc.)
- Activation (local git setting): `git config --local core.hooksPath .githooks`

## Contributor Checklist (Before Every Commit)

Run these commands before pushing:

```bash
git status
git diff --cached
git add -n -A
```

What to verify:

- No real user exports or dossier outputs are staged.
- No credentials/secrets are staged.
- No private config files are staged (`config.personal.json`, `*.private.json`).
- Only intended source/docs/config changes are staged.

Recommended secret scan:

```bash
rg -n "(api[_-]?key|token|secret|password|BEGIN (RSA|EC|OPENSSH) PRIVATE KEY)" .
```

## Safe Usage Guidance

- Treat all data in `zips/`, `extracted/`, and `dossiers/` as sensitive by default.
- Review generated dossiers before sharing externally.
- Remove personal identifiers if you plan to publish outputs.

## Environment Variables

Used for configuration only:

- `CGPT_HOME`
- `CGPT_DEFAULT_MODE`
- `CGPT_FORCE_COLOR`

No environment variable is used as an authentication secret.

## Reporting a Security Issue

If you discover a vulnerability:

1. Do not open a public issue with exploit details.
2. Contact the repository owner privately on GitHub.
3. Include reproduction steps and impact.
4. Allow time for remediation before public disclosure.

## Security Expectations for Changes

Any change that affects file I/O, path handling, or git-ignore behavior should include:

- Updated documentation in `README.md` and/or `SECURITY.md`.
- A manual verification note in the PR description showing that sensitive files remain ignored.
