# Quick Start Guide

Get up and running with MCP Skills Server in 5 minutes!

## Prerequisites

- Python 3.13+ **OR** Docker
- A directory for your skills

## Step 1: Install

### Option A: Using Poetry (Development)

```bash
# Clone the repository
git clone https://github.com/srprasanna/mcp-skill-hub.git
cd mcp-skill-hub

# Install dependencies
poetry install
```

### Option B: Using Docker (Production)

```bash
# Build the Docker image
docker build -t mcp-skill-hub .
```

## Step 2: Create Your First Skill

**IMPORTANT:** Each skill must be in its own folder!

```bash
# Create skills directory and first skill folder
mkdir -p ~/claude-skills/my-first-skill

# Create the skill file
cat > ~/claude-skills/my-first-skill/SKILL.md << 'EOF'
---
name: "my-first-skill"
description: "My first Claude skill"
version: "1.0.0"
tags: ["example", "beginner"]
complexity: "beginner"
---

# My First Skill

This is my first skill for Claude!

## What It Does

This skill demonstrates the basic structure:
- A dedicated folder (`my-first-skill/`)
- A SKILL.md file with YAML frontmatter
- Required fields: name and description

## Usage

Simply reference this skill when you need it.

## Next Steps

- Add more metadata fields (see `advanced-example`)
- Include example files in an `examples/` subdirectory
- Create templates in a `templates/` subdirectory
EOF
```

## Step 3: Run the Server

### Option A: Poetry

```bash
export MCP_SKILLS_DIR=~/claude-skills
poetry run mcp-skills
```

### Option B: Docker

```bash
docker run -i --rm \
  -v ~/claude-skills:/skills:ro \
  mcp-skill-hub
```

## Step 4: Verify It Works

You should see output like:

```
[INFO] MCP Skills Server - Dynamic Claude Skill Loading
[INFO] ====================================================================
[INFO]
[INFO] IMPORTANT: Each skill MUST be in its own dedicated folder:
[INFO]
[INFO]   /skills/
[INFO]   ├── skill-one/
[INFO]   │   └── SKILL.md      ← Required
[INFO]   ├── skill-two/
[INFO]   │   ├── SKILL.md      ← Required
[INFO]   │   └── examples/     ← Optional
[INFO]
[INFO] ====================================================================
[INFO] Scanning /skills for skill folders...
[INFO] Found skill folder: my-first-skill
[INFO]   ✓ Loaded skill: my-first-skill (version 1.0.0, folder: my-first-skill)
[INFO] Scan complete: 1 skill(s) loaded, 0 folder(s) skipped, 0 parse failure(s)
[INFO] MCP Skills Server started successfully
[INFO] Serving 1 skill(s)
```

## Step 5: Integrate with Claude Desktop

Add to your Claude Desktop config file:

**macOS/Linux:** `~/.config/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skills": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "${HOME}/claude-skills:/skills:ro",
        "mcp-skill-hub"
      ]
    }
  }
}
```

Or for Poetry:

```json
{
  "mcpServers": {
    "skills": {
      "command": "poetry",
      "args": ["run", "mcp-skills"],
      "cwd": "/path/to/mcp-skill-hub",
      "env": {
        "MCP_SKILLS_DIR": "/path/to/your/claude-skills"
      }
    }
  }
}
```

## Common Mistakes to Avoid

### ❌ SKILL.md in Root Directory

```
~/claude-skills/
└── SKILL.md          ← WRONG! Will be skipped
```

### ✅ SKILL.md in a Folder

```
~/claude-skills/
└── my-skill/
    └── SKILL.md      ← CORRECT!
```

### ❌ Hidden or System Folders

```
~/claude-skills/
├── .hidden-skill/    ← WRONG! Hidden folders are skipped
│   └── SKILL.md
└── __pycache__/      ← WRONG! System folders are skipped
    └── SKILL.md
```

## Next Steps

1. **Explore examples:** Check out `examples/skills/` for more examples
2. **Add metadata:** Enhance your skills with tags, categories, complexity
3. **Include examples:** Add `examples/` subdirectories with working code
4. **Enable hot-reload:** Edit skills and see them reload automatically
5. **Read the docs:** See README.md for complete documentation

## Troubleshooting

### No Skills Loaded

Check that:
1. Skills are in dedicated folders: `/skills/skill-name/SKILL.md`
2. Folder names don't start with `.` or `_`
3. YAML frontmatter is valid
4. Required fields (`name`, `description`) are present

### Skills Not Reloading

1. Ensure `MCP_SKILLS_HOT_RELOAD=true`
2. Check file is named exactly `SKILL.md`
3. Verify file is in a valid skill folder
4. Look at server logs for errors

### Need More Help?

- Read [README.md](README.md) for full documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guide
- Review example skills in `examples/skills/`

## Summary

Congratulations! You now have a working MCP Skills Server with your first skill. The key points to remember:

1. **Each skill in its own folder** - This is non-negotiable
2. **SKILL.md with YAML frontmatter** - Required format
3. **name and description are required** - Everything else is optional
4. **Use hot-reload** - Edit skills without restarting

Happy skill building! 🎉
