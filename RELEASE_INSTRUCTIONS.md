# Creating the GitHub Release

This file contains instructions for creating the GitHub release for v0.1.0.

## Steps to Create the Release

### 1. Push the tag to GitHub

After merging the PR, run:
```bash
git checkout main
git pull
git tag -a v0.1.0 -m "Release v0.1.0 - Initial feedback release"
git push origin v0.1.0
```

Or if the tag is already created locally:
```bash
git push origin v0.1.0
```

### 2. Create the GitHub Release

1. Go to https://github.com/PurpleKaz81/cgpt/releases/new
2. Select the tag: `v0.1.0`
3. Set the release title: **cgpt v0.1.0 - Initial Feedback Release**
4. Mark as pre-release: ✅ (check the box)
5. Copy the content from `RELEASE_NOTES.md` into the release description
6. Attach the following files (optional but recommended):
   - `cgpt.py` - The main tool
   - `config.json` - Default configuration
   - `requirements.txt` - Optional dependencies

### 3. Announce the Release

After creating the release, consider:
- Sharing on relevant communities/forums
- Creating a discussion thread for feedback
- Adding a link to the release in the README (if desired)

## What's Already Done

✅ Version 0.1.0 added to cgpt.py with `--version` flag
✅ CHANGELOG.md created with full release notes
✅ RELEASE_NOTES.md created for GitHub release page
✅ Git tag v0.1.0 created locally with detailed annotation
✅ All changes committed to the branch

## Next Steps for Future Releases

1. Update the version in `cgpt.py` (`__version__` variable)
2. Add a new section to `CHANGELOG.md` with changes
3. Create release notes in a new file or update `RELEASE_NOTES.md`
4. Create and push a new git tag
5. Create the GitHub release with the new tag

## Testing the Release

Users can test the release by:
```bash
# Download the cgpt.py file from the release
curl -O https://github.com/PurpleKaz81/cgpt/releases/download/v0.1.0/cgpt.py

# Make it executable
chmod +x cgpt.py

# Test it
./cgpt.py --version

# Or set up the alias
echo 'alias cgpt="python3 /path/to/cgpt.py"' >> ~/.zshrc
source ~/.zshrc
```
