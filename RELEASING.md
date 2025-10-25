# Release Process

This document describes the automated release process for the MCP Skills Server.

## Overview

The release process is fully automated using GitHub Actions. It handles:

1. **Version Bumping** - Automatically increments the version in `pyproject.toml`
2. **Git Tagging** - Creates a git tag for the new version
3. **GitHub Release** - Creates a GitHub release with auto-generated changelog
4. **Docker Build** - Builds a multi-arch Docker image
5. **Docker Push** - Publishes to Docker Hub or GitHub Container Registry
6. **Testing** - Runs tests to verify the release

## Prerequisites

Before triggering a release, ensure:

### 1. GitHub Secrets

Configure the following secrets in your GitHub repository:

**For Docker Hub:**
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_PASSWORD` - Your Docker Hub access token (not password!)

**For GitHub Container Registry:**
- No additional secrets needed (uses `GITHUB_TOKEN` automatically)

### 2. Permissions

Ensure the GitHub Actions workflow has:
- Write permissions for repository contents (to commit version bumps)
- Write permissions for packages (to push Docker images)

Go to: `Settings` → `Actions` → `General` → `Workflow permissions` → Select "Read and write permissions"

## Triggering a Release

### Option 1: Using GitHub UI

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Select **Release** workflow from the left sidebar
4. Click **Run workflow** button (top right)
5. Fill in the parameters:
   - **Version bump type**: Choose one of:
     - `patch` - Bug fixes (0.1.0 → 0.1.1)
     - `minor` - New features (0.1.0 → 0.2.0)
     - `major` - Breaking changes (0.1.0 → 1.0.0)
     - Or enter a specific version like `1.2.3`
   - **Docker registry**: Choose `docker.io` or `ghcr.io`
6. Click **Run workflow**

### Option 2: Using GitHub CLI

```bash
# Patch release to Docker Hub
gh workflow run release.yml -f version_bump=patch -f docker_registry=docker.io

# Minor release to GitHub Container Registry
gh workflow run release.yml -f version_bump=minor -f docker_registry=ghcr.io

# Specific version
gh workflow run release.yml -f version_bump=1.5.0 -f docker_registry=docker.io
```

## Release Workflow

The workflow consists of 4 jobs that run in sequence:

### 1. Bump Version

- Checks out the code
- Installs Python and Poetry
- Bumps the version in `pyproject.toml`
- Commits and pushes the version change
- Outputs the new version for subsequent jobs

### 2. Create Release

- Generates a changelog from git commits since the last tag
- Creates a GitHub Release with:
  - Tag: `v{version}` (e.g., `v0.1.1`)
  - Title: `Release v{version}`
  - Body: Auto-generated changelog

### 3. Build and Push Docker

- Builds a multi-stage Docker image
- Tags the image with:
  - Full version: `1.2.3`
  - Major.Minor: `1.2`
  - Major only: `1`
  - `latest`
- Pushes to selected registry:
  - **Docker Hub**: `{username}/mcp-skills-server:{version}`
  - **GHCR**: `ghcr.io/{owner}/mcp-skills-server:{version}`
- Uses layer caching for faster builds

### 4. Test Release

- Verifies the version was bumped correctly
- Runs the full test suite
- Pulls and verifies the Docker image was published

## Version Numbering

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backwards compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backwards compatible

### Examples

```bash
# Current version: 0.1.0

# Patch release (bug fix)
version_bump=patch  # → 0.1.1

# Minor release (new feature)
version_bump=minor  # → 0.2.0

# Major release (breaking change)
version_bump=major  # → 1.0.0

# Specific version (for hotfixes or pre-releases)
version_bump=0.1.5  # → 0.1.5
```

## Docker Images

### Image Structure

The Docker image uses a multi-stage build:

1. **Builder stage**: Installs dependencies using Poetry
2. **Runtime stage**: Minimal image with only runtime dependencies

### Image Tags

Each release creates multiple tags:

```bash
# For version 1.2.3:
mcp-skills-server:1.2.3      # Full version
mcp-skills-server:1.2        # Major.Minor
mcp-skills-server:1          # Major only
mcp-skills-server:latest     # Always points to latest release
```

### Using the Docker Image

**Docker Hub:**
```bash
docker pull {username}/mcp-skills-server:latest
docker run -v /path/to/skills:/skills {username}/mcp-skills-server:latest
```

**GitHub Container Registry:**
```bash
docker pull ghcr.io/{owner}/mcp-skills-server:latest
docker run -v /path/to/skills:/skills ghcr.io/{owner}/mcp-skills-server:latest
```

## Monitoring Releases

### Check Workflow Progress

1. Go to **Actions** tab
2. Click on the running workflow
3. Monitor each job's progress
4. Check logs if any job fails

### Verify Release

After successful completion:

1. **GitHub Release**: Check the [Releases](https://github.com/{owner}/{repo}/releases) page
2. **Git Tag**: `git fetch --tags && git tag -l`
3. **Docker Hub**: Visit https://hub.docker.com/r/{username}/mcp-skills-server/tags
4. **GHCR**: Visit https://github.com/{owner}/{repo}/pkgs/container/mcp-skills-server

## Troubleshooting

### Version Bump Fails

**Problem**: "Invalid version bump type"
- **Solution**: Ensure you're using `major`, `minor`, `patch`, or a valid semver (e.g., `1.2.3`)

### Docker Push Fails

**Problem**: "Error: Cannot perform an interactive login from a non TTY device"
- **Solution**: Check that `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are set correctly

**Problem**: "denied: requested access to the resource is denied"
- **Solution**:
  - For Docker Hub: Verify credentials and repository exists
  - For GHCR: Ensure workflow has package write permissions

### Tests Fail

**Problem**: Tests fail in the test-release job
- **Solution**: Fix tests locally first, commit, and trigger a new release

### Changelog is Empty

**Problem**: No commits shown in changelog
- **Solution**: This happens on first release. Subsequent releases will show commits since last tag

## Best Practices

1. **Test Before Release**: Always run tests locally before triggering a release
2. **Meaningful Commits**: Write clear commit messages - they appear in the changelog
3. **Breaking Changes**: Document breaking changes clearly in commit messages
4. **Security**: Never commit Docker Hub password directly - always use access tokens
5. **Rollback**: If a release has issues, create a new patch release with fixes

## Manual Release (Fallback)

If the automated workflow fails, you can release manually:

```bash
# Bump version
poetry version patch  # or minor, major

# Get new version
NEW_VERSION=$(poetry version -s)

# Commit version bump
git add pyproject.toml
git commit -m "chore: bump version to $NEW_VERSION"
git push

# Create tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
git push --tags

# Build Docker image
docker build -t mcp-skills-server:$NEW_VERSION --build-arg VERSION=$NEW_VERSION .

# Tag and push
docker tag mcp-skills-server:$NEW_VERSION {username}/mcp-skills-server:$NEW_VERSION
docker tag mcp-skills-server:$NEW_VERSION {username}/mcp-skills-server:latest
docker push {username}/mcp-skills-server:$NEW_VERSION
docker push {username}/mcp-skills-server:latest

# Create GitHub release manually via UI
```

## Related Documentation

- [GitHub Actions Workflows](.github/workflows/release.yml)
- [Dockerfile](Dockerfile)
- [Poetry Version Management](https://python-poetry.org/docs/cli/#version)
- [Semantic Versioning](https://semver.org/)
