# Publishing to MCP Registry

This document explains how to publish the MCP Skills Server to the official MCP Registry.

## What is the MCP Registry?

The [MCP Registry](https://registry.modelcontextprotocol.io) is an open catalog of publicly available MCP servers. It's like an app store for MCP servers, making it easy for users to discover and install your server.

## Benefits of Publishing

✅ **Discoverability** - Users can find your server through the official registry
✅ **Easy Installation** - One-command installation for users
✅ **Credibility** - Official listing validates your server
✅ **Updates** - Users get notified of new versions
✅ **Community** - Join the MCP ecosystem

## Prerequisites

Before publishing, ensure:

1. ✅ **Docker Image Published** - Your Docker image must be available on Docker Hub
2. ✅ **GitHub Release Created** - A GitHub release must exist for the version
3. ✅ **server.json Configured** - The `server.json` file is properly configured
4. ✅ **Tests Passing** - All tests pass successfully

## Configuration

The `server.json` file defines your server's metadata and deployment configuration.

### Key Fields

```json
{
  "name": "io.github.srprasanna/mcp-skill-hub",
  "displayName": "MCP Skills Server",
  "description": "A production-ready MCP server...",
  "version": "1.0.0",
  "deployment": {
    "type": "package",
    "package": {
      "type": "docker",
      "image": "srprasanna/mcp-skill-hub"
    }
  }
}
```

### Namespace

The `name` field uses the **GitHub namespace** format: `io.github.{username}/{server-name}`

This means:
- ✅ Authentication via GitHub (automatic)
- ✅ No domain verification needed
- ✅ Ownership proven by GitHub username

## Publishing Methods

### Method 1: Automatic (Recommended)

Publishing happens automatically when you create a Docker Hub release:

1. **Trigger a Release**:
   ```bash
   # Via GitHub UI
   Actions → Release → Run workflow
   - version_bump: patch/minor/major
   - docker_registry: docker.io
   ```

2. **Workflow Steps**:
   - ✅ Bumps version
   - ✅ Creates GitHub release
   - ✅ Builds and pushes Docker image
   - ✅ Runs tests
   - ✅ **Publishes to MCP Registry** (automatic)

3. **Verification**:
   - Check workflow output for MCP Registry publication
   - View your server at: `https://registry.modelcontextprotocol.io/servers/io.github.srprasanna/mcp-skill-hub`

### Method 2: Manual Trigger

Publish to MCP Registry independently:

1. **Via GitHub UI**:
   ```
   Actions → Publish to MCP Registry → Run workflow
   - dry_run: false (to publish) or true (to validate only)
   ```

2. **Via GitHub CLI**:
   ```bash
   # Dry run (validate only)
   gh workflow run publish-mcp-registry.yml -f dry_run=true

   # Publish for real
   gh workflow run publish-mcp-registry.yml -f dry_run=false
   ```

### Method 3: Local Publishing (Advanced)

Install and run the MCP Publisher CLI locally:

```bash
# Install mcp-publisher
brew install mcp-publisher

# Validate configuration
mcp-publisher validate server.json

# Authenticate with GitHub
export GITHUB_TOKEN="your-github-token"

# Publish to registry
mcp-publisher publish server.json --token $GITHUB_TOKEN
```

## Workflow Details

### Publish to MCP Registry Workflow

**File**: `.github/workflows/publish-mcp-registry.yml`

**Triggers**:
- Manual trigger via `workflow_dispatch`
- Automatic on GitHub release creation
- Automatic after successful Docker Hub release

**Steps**:
1. Extract version from `pyproject.toml`
2. Update `server.json` with current version
3. Validate `server.json` against MCP schema
4. Install MCP Publisher CLI
5. Authenticate with GitHub
6. Publish to MCP Registry
7. Verify publication
8. Create summary report

**Dry Run Mode**:
```bash
gh workflow run publish-mcp-registry.yml -f dry_run=true
```
- ✅ Validates configuration
- ✅ Checks authentication
- ❌ Does NOT publish
- Great for testing before real publication

## Registry URL

After publishing, your server will be available at:

```
https://registry.modelcontextprotocol.io/servers/io.github.srprasanna/mcp-skill-hub
```

## User Installation

Once published, users can install your server:

### Via MCP CLI (if available)
```bash
mcp install io.github.srprasanna/mcp-skill-hub
```

### Via Docker
```bash
docker pull srprasanna/mcp-skill-hub:latest
docker run -v ~/skills:/skills srprasanna/mcp-skill-hub
```

### Via Claude Desktop Config
Users add to their `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-skills": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "${HOME}/skills:/skills:ro",
        "srprasanna/mcp-skill-hub"
      ]
    }
  }
}
```

## Updating Published Server

When you release a new version:

1. **Create Release** (with Docker Hub):
   ```bash
   Actions → Release → Run workflow
   - version_bump: patch (e.g., 1.0.0 → 1.0.1)
   - docker_registry: docker.io
   ```

2. **MCP Registry Auto-Updates**:
   - The release workflow automatically triggers MCP Registry publication
   - Registry updates with new version
   - Users get notified of updates

## Troubleshooting

### "Server name already exists"

**Cause**: Server already published under this name

**Fix**:
- If you own it: Update instead of creating new
- If someone else owns it: Choose different name

### "Authentication failed"

**Cause**: GitHub token issues

**Fix**:
1. Check workflow has `id-token: write` permission
2. Verify `GITHUB_TOKEN` is accessible
3. Confirm GitHub username matches namespace

### "Docker image not found"

**Cause**: Docker image not available on Docker Hub

**Fix**:
1. Publish Docker image first (via Release workflow)
2. Verify image exists: `docker pull srprasanna/mcp-skill-hub:latest`
3. Wait a few minutes for Docker Hub to propagate

### "server.json validation failed"

**Cause**: Invalid configuration

**Fix**:
1. Run dry run: `gh workflow run publish-mcp-registry.yml -f dry_run=true`
2. Check schema: https://registry.modelcontextprotocol.io/schema/server.json
3. Validate JSON syntax: `jq empty server.json`

## Best Practices

1. **Version Sync**: Always keep `server.json` version in sync with `pyproject.toml` (workflow does this automatically)

2. **Docker First**: Always publish Docker image before MCP Registry

3. **Test Locally**: Use dry run mode to validate before publishing

4. **Semantic Versioning**: Follow semver (major.minor.patch) for versions

5. **Clear Description**: Write a clear, concise description in `server.json`

6. **Categories & Tags**: Choose relevant categories and tags for discoverability

## Monitoring

After publishing, monitor:

- **Registry Listing**: Check your server appears correctly
- **Installation Success**: Verify users can install successfully
- **User Feedback**: Monitor issues and discussions
- **Download Metrics**: Track usage via Docker Hub

## Support & Resources

- 📚 [MCP Registry Docs](https://github.com/modelcontextprotocol/registry/tree/main/docs)
- 🐛 [Report Issues](https://github.com/modelcontextprotocol/registry/issues)
- 💬 [MCP Community](https://discord.gg/modelcontextprotocol)
- 📖 [MCP Specification](https://modelcontextprotocol.io)

## Quick Reference

| Task | Command |
|------|---------|
| Validate config | `gh workflow run publish-mcp-registry.yml -f dry_run=true` |
| Publish manually | `gh workflow run publish-mcp-registry.yml -f dry_run=false` |
| View in registry | https://registry.modelcontextprotocol.io/servers/io.github.srprasanna/mcp-skill-hub |
| Update server | Create new release via Release workflow |

---

**Status**: ✅ **Ready to Publish**

Your MCP Skills Server is configured and ready to be published to the MCP Registry!
