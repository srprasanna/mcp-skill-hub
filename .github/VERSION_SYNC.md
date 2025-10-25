# Version Synchronization Explained

This document explains how version numbers are automatically synchronized between `pyproject.toml` and `server.json`.

## The Problem

Your project has two version sources:
1. **`pyproject.toml`** - Python package version (source of truth)
2. **`server.json`** - MCP Registry version (must match)

Keeping these in sync manually is error-prone. The workflows handle this automatically.

## How It Works

### Method 1: During Release (Best)

When you create a release, the version bump includes `server.json`:

```
Release Workflow Flow:
┌─────────────────────────────────────────────────┐
│ 1. User triggers release workflow               │
│    - version_bump: patch (0.1.0 → 0.1.1)       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Bump version in pyproject.toml               │
│    poetry version patch                         │
│    Result: version = "0.1.1"                    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Update server.json version ✅ NEW!           │
│    jq '.version = "0.1.1"' server.json          │
│    Result: "version": "0.1.1"                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. Commit BOTH files in ONE commit              │
│    git add pyproject.toml server.json           │
│    git commit -m "chore: bump version to 0.1.1" │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 5. Push to repository                           │
│    Both files now have version 0.1.1 ✅         │
└─────────────────────────────────────────────────┘
```

**Result**: One commit updates both files!

### Method 2: During MCP Registry Publish

If you manually publish to MCP Registry (without release), it also syncs:

```
MCP Registry Workflow Flow:
┌─────────────────────────────────────────────────┐
│ 1. Read version from pyproject.toml             │
│    VERSION=0.1.1                                │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Update server.json to match                  │
│    jq '.version = "0.1.1"' server.json          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Commit server.json update                    │
│    git commit -m "chore: update server.json..." │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. Publish to MCP Registry                      │
│    With correct version 0.1.1 ✅                │
└─────────────────────────────────────────────────┘
```

## Code Implementation

### Release Workflow (`.github/workflows/release.yml`)

**Lines 85-109:**
```yaml
- name: Update server.json version
  run: |
    NEW_VERSION="${{ steps.bump.outputs.new_version }}"

    if [ -f "server.json" ]; then
      jq --arg version "$NEW_VERSION" '.version = $version' server.json > server.json.tmp
      mv server.json.tmp server.json
      echo "✅ Updated server.json to version $NEW_VERSION"
    fi

- name: Commit version bump
  run: |
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    git add pyproject.toml

    # Also commit server.json if it was updated
    if [ -f "server.json" ]; then
      git add server.json
    fi

    git commit -m "chore: bump version to ${{ steps.bump.outputs.new_version }}"
```

### MCP Registry Workflow (`.github/workflows/publish-mcp-registry.yml`)

**Lines 32-59:**
```yaml
- name: Get version from pyproject.toml
  id: get_version
  run: |
    VERSION=$(grep -m 1 '^version = ' pyproject.toml | cut -d'"' -f2)
    echo "version=$VERSION" >> $GITHUB_OUTPUT

- name: Update server.json version
  run: |
    jq --arg version "${{ steps.get_version.outputs.version }}" '.version = $version' server.json > server.json.tmp
    mv server.json.tmp server.json

- name: Commit server.json version update
  run: |
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"

    if git diff --quiet server.json; then
      echo "No changes to server.json"
    else
      git add server.json
      git commit -m "chore: update server.json version to ${{ steps.get_version.outputs.version }}"
      git push
    fi
```

## Example Workflow Run

### Scenario: Bump from 0.1.0 to 0.1.1

**Before:**
```
pyproject.toml:  version = "0.1.0"
server.json:     "version": "0.1.0"
```

**Run Release Workflow:**
```bash
Actions → Release → Run workflow
- version_bump: patch
- docker_registry: docker.io
```

**During Workflow:**
1. ✅ Poetry bumps `pyproject.toml` → `0.1.1`
2. ✅ Workflow updates `server.json` → `0.1.1`
3. ✅ Both files committed together
4. ✅ Tag created: `v0.1.1`
5. ✅ GitHub release created
6. ✅ Docker image built with version `0.1.1`
7. ✅ MCP Registry publishes version `0.1.1`

**After:**
```
pyproject.toml:  version = "0.1.1"  ✅
server.json:     "version": "0.1.1"  ✅
Git commit:      "chore: bump version to 0.1.1"
Git tag:         v0.1.1
```

## Benefits

✅ **Single Source of Truth** - `pyproject.toml` is the master version
✅ **Automatic Sync** - No manual updates needed
✅ **One Commit** - Both files updated in same commit
✅ **Always Consistent** - Version numbers never mismatch
✅ **Fail-Safe** - If `server.json` doesn't exist, workflow continues

## Verification

After a release, verify sync:

```bash
# Check pyproject.toml version
grep '^version = ' pyproject.toml

# Check server.json version
jq '.version' server.json

# Both should match!
```

Or use this one-liner:

```bash
# Compare versions
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
SERVER_VERSION=$(jq -r '.version' server.json)

if [ "$PYPROJECT_VERSION" = "$SERVER_VERSION" ]; then
  echo "✅ Versions match: $PYPROJECT_VERSION"
else
  echo "❌ Version mismatch!"
  echo "  pyproject.toml: $PYPROJECT_VERSION"
  echo "  server.json: $SERVER_VERSION"
fi
```

## Manual Override (Not Recommended)

If you need to manually set a specific version:

```bash
# Update pyproject.toml
poetry version 1.5.0

# Update server.json
jq '.version = "1.5.0"' server.json > server.json.tmp && mv server.json.tmp server.json

# Commit both
git add pyproject.toml server.json
git commit -m "chore: bump version to 1.5.0"
git push
```

But it's better to use the workflow!

## Troubleshooting

### "server.json version doesn't match pyproject.toml"

**Cause**: Manual edit or workflow failed to update

**Fix**: Re-run the release workflow or MCP Registry workflow

### "git push failed in workflow"

**Cause**: Insufficient permissions

**Fix**: Ensure workflow has write permissions (already configured)

### "jq command not found"

**Cause**: Missing jq in workflow environment

**Fix**: Already installed in GitHub Actions Ubuntu runners (no action needed)

## Summary

- 🎯 **`pyproject.toml` is the source of truth**
- 🔄 **Workflows automatically sync `server.json`**
- 📦 **Release workflow updates both in one commit**
- 🚀 **MCP Registry workflow ensures sync before publishing**
- ✅ **No manual version management needed!**

---

**Your versions are always in sync automatically!** 🎉
