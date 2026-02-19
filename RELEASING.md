# Releasing cgpt

This file is the single source of truth for creating a release.

## Documentation Contract (Every Code Change)

This repository uses a controlled markdown policy:

Core markdown files (canonical):

- `README.md`
- `TECHNICAL.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `RELEASING.md`

Governance markdown files (allowed root-level docs):

- `CONTRIBUTING.md`
- `AGENTS.md`

Scoped supplemental markdown files (allowed):

- `docs/INDEX.md`
- `docs/specs/**/*.md`
- `docs/adr/**/*.md`
- `docs/runbooks/**/*.md`
- `docs/roadmap/**/*.md`

Rules:

- Every scoped supplemental markdown file must be linked from `docs/INDEX.md`.
- Every change to `cgpt/**/*.py` (including `cgpt.py`), `config.json`, or `requirements.txt` must update at least one core markdown file.
- User-visible behavior changes should update `README.md` and `CHANGELOG.md`, and update `TECHNICAL.md` when command behavior/flags/examples change.
- Security/data-handling changes should update `SECURITY.md`.

Enforcement:

- CI workflow `.github/workflows/docs-guard.yml` enforces this policy on PRs and pushes to `main`.

## Release Checklist

- [ ] Working tree is clean (`git status`).
- [ ] No private config files are tracked/staged (`config.personal.json`, `*.private.json`).
- [ ] `cgpt/core/constants.py` version (`__version__`) is updated.
- [ ] `CHANGELOG.md` has a new version section with date and changes.
- [ ] `CHANGELOG.md` numbered release subsections use unique version-qualified H3 headings (`Added/Changed/Fixed in X.Y.Z`) to satisfy markdown lint.
- [ ] `docs/specs/current-capabilities.md` is reviewed and reflects shipped behavior.
- [ ] `docs/roadmap/shared-roadmap.md` status/commitment/horizon tags are reviewed for this release.
- [ ] `docs/runbooks/engineering-quality-backlog.md` baseline/backlog status is reviewed for this release.
- [ ] `README.md` high-level positioning still matches current scope and constraints.
- [ ] Core smoke tests pass (see below).
- [ ] CI `lint` workflow is green for the release commit/PR.
- [ ] Release PR is merged to `main`.
- [ ] Annotated git tag is created and pushed.
- [ ] GitHub release is created from that tag.

## 1. Prepare a release branch and release commit

```bash
git checkout main
git pull origin main
git checkout -b release/vX.Y.Z
```

Update:

- `cgpt/core/constants.py` (`__version__`)
- `pyproject.toml` version mapping remains `cgpt.core.constants.__version__` under `[tool.setuptools.dynamic]`
- `CHANGELOG.md`
- Any docs changed by the release
- `docs/specs/current-capabilities.md` (current-state sync)
- `docs/roadmap/shared-roadmap.md` (status/priority sync)
- `docs/runbooks/engineering-quality-backlog.md` (quality baseline/backlog sync)
- `README.md` (if user-facing positioning changed)
- `CHANGELOG.md` subsection heading convention for lint compliance:
  - use `### Added in X.Y.Z`, `### Changed in X.Y.Z`, and `### Fixed in X.Y.Z` under the numbered release heading.
  - keep `[Unreleased]` headings concise (`### Added`, `### Changed`, `### Fixed`) as needed.

Then commit:

```bash
git add cgpt.py cgpt/
git add config.json requirements.txt pyproject.toml Makefile tox.ini
git add README.md TECHNICAL.md SECURITY.md CHANGELOG.md RELEASING.md CONTRIBUTING.md AGENTS.md LICENSE
git add .github/CODEOWNERS .github/dependabot.yml
git add .github/workflows/tests.yml .github/workflows/docs-guard.yml .github/workflows/lint.yml
git add .ruff.toml .markdownlint.yml .gitignore .githooks/pre-commit .githooks/pre-push
git add scripts/release_check.sh scripts/release_via_pr.sh scripts/gh_retry.sh
git add docs/INDEX.md docs/specs docs/adr docs/runbooks docs/roadmap
git commit -m "Release vX.Y.Z"
```

Before commit, verify no private files are staged:

```bash
git diff --cached --name-only
```

## 2. Run local quality gates

Preferred:

```bash
./scripts/release_check.sh
make lint-py
make lint-md
```

Manual equivalent from repo root:

```bash
python3 cgpt.py --version
python3 cgpt.py --help
python3 cgpt.py extract --help
python3 cgpt.py recent --help
python3 cgpt.py quick --help
python3 cgpt.py build-dossier --help
python3 cgpt.py make-dossiers --help
python3 cgpt.py search --help
python3 cgpt.py doctor
python3 -m unittest discover -s tests -p "test_*.py"
make lint-py
npx --yes markdownlint-cli2@0.16.0 "**/*.md" "#node_modules" "#.venv" "#.tox"
```

If any command fails, fix before opening the release PR.

## GitHub CLI Resilience

When running `gh` commands locally (for example PR checks or release creation), use the retry wrapper to tolerate transient `api.github.com` connectivity failures:

```bash
./scripts/gh_retry.sh gh pr checks <PR_NUMBER>
./scripts/gh_retry.sh gh release create vX.Y.Z --title "cgpt vX.Y.Z" --notes-file /tmp/notes.md
```

You can tune retry behavior with:

- `GH_RETRY_ATTEMPTS` (default: `5`)
- `GH_RETRY_INITIAL_DELAY` (default: `2`)
- `GH_RETRY_MAX_DELAY` (default: `30`)
- `GH_RETRY_BACKOFF` (default: `2`)

## 3. Open release PR and merge to main

Use PR flow for protected `main`:

```bash
git push -u origin release/vX.Y.Z
./scripts/gh_retry.sh gh pr create --base main --head release/vX.Y.Z --title "Release vX.Y.Z" --body "Release vX.Y.Z"
./scripts/gh_retry.sh gh pr checks <PR_NUMBER>
./scripts/gh_retry.sh gh pr merge <PR_NUMBER> --merge --delete-branch
git checkout main
git pull origin main
```

Optional helper from `release/vX.Y.Z`:

```bash
./scripts/release_via_pr.sh X.Y.Z
```

## 4. Tag and push

Replace `X.Y.Z` with the release version:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Tag only after the release PR is merged and local `main` is synced.

Verify tag exists remotely:

```bash
git ls-remote --tags origin | rg "vX.Y.Z"
```

## 5. Create GitHub release

1. Open: `https://github.com/PurpleKaz81/cgpt/releases/new`
2. Choose tag: `vX.Y.Z`
3. Release title: `cgpt vX.Y.Z`
4. Release notes body:
   - Copy from the matching `CHANGELOG.md` section.
   - Add upgrade notes or breaking changes if needed.
5. Mark as pre-release only when appropriate.
6. Publish.

## 6. Post-release verification

- [ ] `git status` is clean.
- [ ] `main` and `origin/main` are in sync.
- [ ] Release page shows the correct tag and notes.
- [ ] `CHANGELOG.md` link for the version points to the correct release URL.
- [ ] Roadmap and capability docs still agree with the released behavior.

## Notes

- Do not maintain separate version-specific release docs in this repo.
- Keep release notes in `CHANGELOG.md` and use this file only for process.
