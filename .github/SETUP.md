# GitHub Actions Setup Guide

This guide walks you through setting up the automated release workflow for the MCP Skills Server.

## Step 1: Configure GitHub Secrets

The release workflow requires secrets to push Docker images. Set these up based on your chosen registry.

### For Docker Hub

1. Create a Docker Hub Access Token:
   - Go to [Docker Hub](https://hub.docker.com/)
   - Click your profile → **Account Settings** → **Security**
   - Click **New Access Token**
   - Name: `github-actions-mcp-skills`
   - Permissions: **Read, Write, Delete**
   - Copy the token (you won't see it again!)

2. Add GitHub Secrets:
   - Go to your GitHub repository
   - Navigate to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Add these secrets:

   | Name | Value | Description |
   |------|-------|-------------|
   | `DOCKER_USERNAME` | Your Docker Hub username | Used for login |
   | `DOCKER_PASSWORD` | Your access token | NOT your Docker Hub password! |

### For GitHub Container Registry (GHCR)

No additional secrets needed! The workflow automatically uses `GITHUB_TOKEN`.

However, you need to ensure packages are public or configure permissions:

1. Go to **Settings** → **Packages**
2. Find your package after first push
3. Click **Package settings** → **Change visibility** → **Public** (optional)

## Step 2: Configure Workflow Permissions

The workflow needs permissions to commit version bumps and push Docker images.

### Option 1: Repository-Level Permissions (Recommended)

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests** (optional)
5. Click **Save**

### Option 2: Workflow-Level Permissions (Already Configured)

The workflow file already includes these permissions at the top:
```yaml
permissions:
  contents: write      # Push commits and tags
  packages: write      # Push Docker images to GHCR
  pull-requests: write # Create PRs (if needed)
```

**If you still get "Permission denied" errors:**
- Ensure Step 2.1 (Repository-Level Permissions) is configured
- Or create a Personal Access Token (PAT) with `repo` scope and use it instead of `GITHUB_TOKEN`

## Step 3: Verify Repository Settings

### Branch Protection (Optional but Recommended)

For production repositories, configure branch protection:

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators
3. Click **Create**

### Actions Settings

1. Go to **Settings** → **Actions** → **General**
2. Under **Actions permissions**, select:
   - **Allow all actions and reusable workflows**
3. Under **Fork pull request workflows**, configure as needed
4. Click **Save**

## Step 4: Test the Workflow

### Test with a Dry Run

Before creating a real release, test that everything works:

1. Create a test branch:
   ```bash
   git checkout -b test-release
   git push origin test-release
   ```

2. Modify the workflow temporarily to run on push to test-release:
   ```yaml
   on:
     push:
       branches:
         - test-release
   ```

3. Push and verify all jobs pass

4. Delete the test branch when done

### Create Your First Release

1. Go to **Actions** tab
2. Select **Release** workflow
3. Click **Run workflow**
4. Set parameters:
   - **version_bump**: `0.1.0` (or your desired starting version)
   - **docker_registry**: Choose `docker.io` or `ghcr.io`
5. Click **Run workflow**

Monitor the workflow execution. All jobs should turn green ✅

## Troubleshooting

### Common Issues

#### "Permission to {user}/{repo}.git denied to github-actions[bot]"

**Cause**: Workflow doesn't have permission to push commits

**Fix**:

1. **Check Repository Settings** (Most Common):
   - Go to **Settings** → **Actions** → **General**
   - Scroll to **Workflow permissions**
   - Select **Read and write permissions**
   - Click **Save**

2. **Verify Workflow Permissions** (Already Added):
   - The workflow file already includes `permissions: contents: write`
   - This should work with repository setting above

3. **Alternative: Use Personal Access Token**:
   - Create a PAT: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Select scopes: `repo`, `write:packages`
   - Add as secret: `PAT_TOKEN`
   - Update workflow to use it:
     ```yaml
     - name: Checkout code
       uses: actions/checkout@v4
       with:
         token: ${{ secrets.PAT_TOKEN }}
     ```

#### "Error: Cannot perform an interactive login"

**Cause**: Docker credentials not configured correctly

**Fix**:
- Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are set
- Ensure `DOCKER_PASSWORD` is an access token, not your password
- Check the token has write permissions

#### "denied: requested access to the resource is denied"

**Cause**: Insufficient permissions

**Fix for Docker Hub**:
- Verify username is correct
- Ensure access token has write permissions
- Check repository exists or will be auto-created

**Fix for GHCR**:
- Verify workflow has write permissions (Step 2)
- Check package visibility settings

#### "Error: Version already exists"

**Cause**: Trying to create a release that already exists

**Fix**:
- Check existing releases: `git tag -l`
- Use a different version bump or specific version

#### "Tests failed"

**Cause**: Code quality issues

**Fix**:
- Run tests locally: `poetry run pytest`
- Fix failing tests
- Commit and push fixes
- Re-run workflow

### Getting Help

If you encounter issues:

1. Check the [Actions logs](../../actions) for detailed error messages
2. Review [RELEASING.md](../../RELEASING.md) for detailed documentation
3. Check [GitHub Actions documentation](https://docs.github.com/en/actions)
4. Open an issue with:
   - Workflow run URL
   - Error message
   - Steps to reproduce

## Security Best Practices

### Secrets Management

- ✅ Use access tokens, not passwords
- ✅ Rotate tokens regularly (every 90 days)
- ✅ Use minimal required permissions
- ✅ Never commit secrets to code
- ✅ Review secret access logs periodically

### Workflow Security

- ✅ Pin action versions with SHA (e.g., `actions/checkout@v4`)
- ✅ Review third-party actions before use
- ✅ Enable branch protection
- ✅ Require code reviews
- ✅ Use Dependabot for action updates

### Docker Security

- ✅ Multi-stage builds (already configured)
- ✅ Non-root user (already configured)
- ✅ Minimal base image (python:3.13-slim)
- ✅ Regular dependency updates
- ✅ Scan images for vulnerabilities

## Next Steps

After successful setup:

1. ✅ Create your first release
2. ✅ Verify Docker image on registry
3. ✅ Test pulling and running the image
4. ✅ Set up automated dependency updates (Dependabot)
5. ✅ Configure additional CI checks (optional)

## Maintenance

### Regular Tasks

- **Weekly**: Review dependabot PRs
- **Monthly**: Rotate access tokens
- **Quarterly**: Review and update workflows
- **As needed**: Update Python/Poetry versions

### Monitoring

Keep an eye on:
- Workflow success rate
- Docker image pull counts
- GitHub release downloads
- Security alerts

---

**Need Help?** See [RELEASING.md](../../RELEASING.md) or open an issue!
