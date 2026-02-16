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

Scoped supplemental markdown files (allowed):
- `docs/INDEX.md`
- `docs/specs/**/*.md`
- `docs/adr/**/*.md`
- `docs/runbooks/**/*.md`
- `docs/roadmap/**/*.md`

Rules:
- Every scoped supplemental markdown file must be linked from `docs/INDEX.md`.
- Every change to `cgpt.py`, `config.json`, or `requirements.txt` must update at least one core markdown file.
- User-visible behavior changes should update `README.md` and `CHANGELOG.md`, and update `TECHNICAL.md` when command behavior/flags/examples change.
- Security/data-handling changes should update `SECURITY.md`.

Enforcement:
- CI workflow `.github/workflows/docs-guard.yml` enforces this policy on PRs and pushes to `main`.

## Release Checklist

- [ ] Working tree is clean (`git status`).
- [ ] No private config files are tracked/staged (`config.personal.json`, `*.private.json`).
- [ ] `cgpt.py` version (`__version__`) is updated.
- [ ] `CHANGELOG.md` has a new version section with date and changes.
- [ ] Core smoke tests pass (see below).
- [ ] Release commit is on `main`.
- [ ] Annotated git tag is created and pushed.
- [ ] GitHub release is created from that tag.

## 1. Prepare the release commit

```bash
git checkout main
git pull origin main
```

Update:
- `cgpt.py` (`__version__`)
- `CHANGELOG.md`
- Any docs changed by the release

Then commit:

```bash
git add cgpt.py CHANGELOG.md README.md TECHNICAL.md SECURITY.md RELEASING.md .gitignore .githooks/pre-commit config.json
git add docs/INDEX.md docs/specs docs/adr docs/runbooks docs/roadmap
git commit -m "Release vX.Y.Z"
```

Before commit, verify no private files are staged:

```bash
git diff --cached --name-only
```

## 2. Run smoke tests

Preferred (one command):

```bash
./scripts/release_check.sh
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
python3 -m unittest discover -s tests -p "test_*.py"
```

If any command fails, fix before tagging.

## 3. Tag and push

Replace `X.Y.Z` with the release version:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Verify tag exists remotely:

```bash
git ls-remote --tags origin | rg "vX.Y.Z"
```

## 4. Create GitHub release

1. Open: `https://github.com/PurpleKaz81/cgpt/releases/new`
2. Choose tag: `vX.Y.Z`
3. Release title: `cgpt vX.Y.Z`
4. Release notes body:
   - Copy from the matching `CHANGELOG.md` section.
   - Add upgrade notes or breaking changes if needed.
5. Mark as pre-release only when appropriate.
6. Publish.

## 5. Post-release verification

- [ ] `git status` is clean.
- [ ] `main` and `origin/main` are in sync.
- [ ] Release page shows the correct tag and notes.
- [ ] `CHANGELOG.md` link for the version points to the correct release URL.

## Notes

- Do not maintain separate version-specific release docs in this repo.
- Keep release notes in `CHANGELOG.md` and use this file only for process.
