# Quick Fix: Permission Denied Error

## Error Message
```
Permission to srprasanna/mcp-skill-hub.git denied to github-actions[bot]
```

## Solution

### Step 1: Enable Write Permissions (Takes 30 seconds)

1. Go to your repository: https://github.com/srprasanna/mcp-skill-hub
2. Click **Settings** (top right)
3. Click **Actions** → **General** (left sidebar)
4. Scroll down to **Workflow permissions**
5. Select **"Read and write permissions"**
6. Click **Save**

![Workflow Permissions](https://docs.github.com/assets/cb-45233/images/help/repository/actions-workflow-permissions-read-write.png)

### Step 2: Re-run the Workflow

1. Go to **Actions** tab
2. Click on the failed workflow run
3. Click **Re-run all jobs** (top right)

✅ **Done!** The workflow should now complete successfully.

---

## What This Does

The workflow needs to:
1. Commit the version bump to `pyproject.toml`
2. Push the commit to your repository
3. Create a git tag

By default, GitHub Actions only has **read** permissions. Enabling **write** permissions allows the workflow to push commits and tags.

## Already Fixed in Workflow

The workflow file already includes these permissions:
```yaml
permissions:
  contents: write      # ✅ Push commits and tags
  packages: write      # ✅ Push Docker images
  pull-requests: write # ✅ Create PRs
```

But this **requires** repository settings to allow write access.

---

## Still Having Issues?

### Alternative: Use Personal Access Token

If repository-level permissions don't work (e.g., in organization repos):

1. **Create a Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Click **Generate new token (classic)**
   - Name: `mcp-skills-release`
   - Select scopes:
     - ✅ `repo` (all sub-scopes)
     - ✅ `write:packages`
   - Click **Generate token**
   - **Copy the token** (you won't see it again!)

2. **Add Token as Secret:**
   - Go to your repo **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PAT_TOKEN`
   - Value: Paste the token
   - Click **Add secret**

3. **Update Workflow** (only if using PAT):

   Edit `.github/workflows/release.yml`:

   Change this:
   ```yaml
   - name: Checkout code
     uses: actions/checkout@v4
     with:
       fetch-depth: 0
       token: ${{ secrets.GITHUB_TOKEN }}
   ```

   To this:
   ```yaml
   - name: Checkout code
     uses: actions/checkout@v4
     with:
       fetch-depth: 0
       token: ${{ secrets.PAT_TOKEN }}
   ```

4. **Re-run the workflow**

---

## Verification

After fixing, you should see:
- ✅ `bump-version` job completes successfully
- ✅ New commit appears in your repo: `"chore: bump version to X.X.X"`
- ✅ New tag created: `vX.X.X`
- ✅ GitHub release created
- ✅ Docker image published

## Need More Help?

See full documentation:
- [SETUP.md](SETUP.md) - Complete setup guide
- [RELEASING.md](../RELEASING.md) - Release process details
