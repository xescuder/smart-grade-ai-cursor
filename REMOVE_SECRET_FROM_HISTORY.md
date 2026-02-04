# Remove Exposed API Key from Git History

**⚠️ WARNING:** This operation rewrites git history and requires force-push. Coordinate with all team members before proceeding.

## Overview

Even after removing an API key from current files, it remains in the repository's git history. Anyone with access to the repository can still retrieve the exposed key from historical commits.

**You must clean the git history to fully remove the exposed secret.**

## Prerequisites

Before starting:

1. ✅ **Revoke the exposed key** at https://aistudio.google.com/apikey
2. ✅ **Generate a new API key** 
3. ✅ **Update your local `.env` file** with the new key
4. ✅ **Notify all team members** about the upcoming history rewrite
5. ✅ **Ensure all team members have pushed their changes** (they will need to re-clone after cleanup)

## Method 1: Using BFG Repo-Cleaner (Recommended)

BFG Repo-Cleaner is faster and simpler than git-filter-branch for removing sensitive data.

### Step 1: Install BFG

Download from: https://rtyley.github.io/bfg-repo-cleaner/

```bash
# macOS
brew install bfg

# Or download the JAR file directly
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
alias bfg='java -jar bfg-1.14.0.jar'
```

### Step 2: Clone a Fresh Mirror

```bash
git clone --mirror https://github.com/xescuder/smart-grade-ai-cursor.git
cd smart-grade-ai-cursor.git
```

### Step 3: Create Replacements File

Create a file named `passwords.txt` with the exposed key:

```text
AIzaSyDDWEU3VnoGadZI5lNiBOrviAoUY4NGyJ8
```

### Step 4: Run BFG to Remove the Key

```bash
bfg --replace-text passwords.txt smart-grade-ai-cursor.git
```

### Step 5: Clean Up and Force-Push

```bash
cd smart-grade-ai-cursor.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

## Method 2: Using git-filter-repo (Alternative)

git-filter-repo is a powerful tool for rewriting git history.

### Step 1: Install git-filter-repo

```bash
# Using pip
pip install git-filter-repo

# Or using package manager
# macOS
brew install git-filter-repo

# Ubuntu/Debian
apt-get install git-filter-repo
```

### Step 2: Create Replacements File

Create a file named `replacements.txt`:

```text
AIzaSyDDWEU3VnoGadZI5lNiBOrviAoUY4NGyJ8==>YOUR_GOOGLE_AI_API_KEY_HERE
```

### Step 3: Run git-filter-repo

```bash
# Make sure you're in the repository directory
cd /path/to/smart-grade-ai-cursor

# Create a backup first (recommended)
git clone --mirror . ../smart-grade-ai-cursor-backup.git

# Run filter-repo
git filter-repo --replace-text replacements.txt --force
```

### Step 4: Re-add Remote and Force-Push

```bash
# git-filter-repo removes remotes for safety
git remote add origin https://github.com/xescuder/smart-grade-ai-cursor.git

# Force-push to rewrite remote history
git push --force --all
git push --force --tags
```

## Method 3: Using git-filter-branch (Legacy, Not Recommended)

Only use this if BFG and git-filter-repo are not available.

```bash
git filter-branch --tree-filter '
  find . -type f -exec sed -i "s/AIzaSyDDWEU3VnoGadZI5lNiBOrviAoUY4NGyJ8/YOUR_GOOGLE_AI_API_KEY_HERE/g" {} +
' --tag-name-filter cat -- --all

git push --force --all
git push --force --tags
```

## Post-Cleanup Steps

After successfully cleaning the git history:

### 1. Verify the Key is Removed

```bash
# Search for the exposed key in git history
git log -S "AIzaSyDDWEU3VnoGadZI5lNiBOrviAoUY4NGyJ8" --all

# This should return no results
```

### 2. Notify All Collaborators

Send a message to all team members:

```
🚨 IMPORTANT: Git history has been rewritten to remove an exposed API key.

Action Required:
1. Delete your local clone of the repository
2. Clone a fresh copy: git clone https://github.com/xescuder/smart-grade-ai-cursor.git
3. Update your .env file with the new API key (contact maintainer for the key)
4. Do NOT try to merge or rebase old branches - they contain the exposed key

If you have local uncommitted changes, save them elsewhere before deleting your clone.
```

### 3. Update Protected Branch Settings (if needed)

If your repository has protected branches:

1. Temporarily disable branch protection
2. Force-push the cleaned history
3. Re-enable branch protection

### 4. Consider Enabling Secret Scanning

Enable GitHub's secret scanning to prevent future exposures:

1. Go to repository Settings → Security → Code security and analysis
2. Enable "Secret scanning"
3. Enable "Push protection" to block commits with secrets

## Troubleshooting

### "Cannot force-push to protected branch"

Temporarily remove branch protection in repository settings, then re-enable after pushing.

### "Remote rejected (protected branch hook)"

Some organizations have additional hooks preventing force-push. Contact your repository administrator.

### "Reference not found"

This may happen after filter-repo. Re-add the remote:
```bash
git remote add origin https://github.com/xescuder/smart-grade-ai-cursor.git
```

## Important Notes

- **This cannot be undone** - make sure you have backups before proceeding
- **All team members must re-clone** - their existing clones will be out of sync
- **Open pull requests will be invalid** - they'll need to be recreated from the cleaned history
- **GitHub Actions history will show failures** - old workflow runs reference commits that no longer exist
- **The key is STILL compromised** - history cleanup doesn't un-expose the key to anyone who already saw it

## Why This Matters

Even after removing a secret from current files, it remains accessible in:
- Git commit history
- GitHub's commit browser
- Clones of the repository
- Pull request diffs
- Cached versions on various systems

Cleaning the history reduces the attack surface, but the key should still be considered compromised and must be revoked.
