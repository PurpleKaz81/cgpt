# Removing Sourcery Bot from GitHub

This guide explains how to remove the Sourcery bot from your GitHub account and this repository.

## Repository-Level Removal

### Good News
✅ **No Sourcery configuration files found in this repository.**

This repository does not contain any of the following Sourcery-related files:
- `.sourcery.yaml` (Sourcery configuration file)
- GitHub Actions workflows using Sourcery
- `.github/sourcery` configuration

### Prevention
A `.gitignore` rule has been added to prevent Sourcery configuration files from being committed in the future.

## GitHub Account-Level Removal

Since no repository files were found, Sourcery is likely configured at the **GitHub account or organization level**. Follow these steps to remove it:

### Step 1: Remove Sourcery GitHub App

1. Go to your GitHub account settings: **https://github.com/settings/installations**
2. Look for "Sourcery" in the list of installed GitHub Apps
3. Click "Configure" next to Sourcery
4. Scroll down and click "Uninstall" or adjust repository access to exclude this repository

**OR** for organizations:

1. Go to your organization settings: **https://github.com/organizations/YOUR_ORG/settings/installations**
2. Find "Sourcery" and click "Configure"
3. Either uninstall it completely or remove access to specific repositories

### Step 2: Revoke Sourcery OAuth Access (Optional)

1. Go to: **https://github.com/settings/applications**
2. Look under "Authorized OAuth Apps"
3. Find "Sourcery" and click "Revoke"

### Step 3: Remove Any Sourcery Webhooks (if applicable)

1. Go to your repository settings: **https://github.com/PurpleKaz81/cgpt/settings/hooks**
2. Look for any webhooks pointing to Sourcery
3. Delete them if found

### Step 4: Verify Removal

After completing the above steps:
1. Check that Sourcery no longer appears in pull request reviews
2. Verify no automated Sourcery comments appear on new PRs
3. Confirm Sourcery is not listed in your installed apps

## Additional Resources

- **Sourcery Documentation**: https://docs.sourcery.ai/
- **GitHub Apps Settings**: https://github.com/settings/installations
- **Repository Settings**: https://github.com/PurpleKaz81/cgpt/settings

## Summary

✅ Repository is clean - no Sourcery configuration files to remove  
⚠️ Check GitHub account/org settings to fully remove Sourcery integration  
✅ Future protection added via .gitignore  
