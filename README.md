# MCP Skills Server

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/poetry-1.7+-blue.svg)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that dynamically loads and exposes Claude skills from a mounted volume with hot-reloading support.

## Features

- **Dynamic Skill Loading**: Automatically discovers and loads skills from a directory
- **Hot-Reloading**: Detects changes to SKILL.md files and reloads without restart
- **Folder Structure Validation**: Enforces best practices with clear error messages
- **MCP Protocol Compliant**: Full implementation of resources and tools
- **Production Ready**: Comprehensive error handling, logging, and validation
- **Docker Support**: Run in containers with volume mounting
- **Type Safe**: Full type hints using Python 3.13 features
- **Well Tested**: >80% code coverage with comprehensive test suite

## Table of Contents

- [Skills Directory Structure](#skills-directory-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Skill File Format](#skill-file-format)
- [MCP Resources and Tools](#mcp-resources-and-tools)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Skills Directory Structure

**CRITICAL REQUIREMENT**: Each skill MUST be in its own dedicated folder within the skills directory. The server will ONLY recognize skills that follow this structure.

### ✅ Valid Structure

```
your-skills-directory/
├── skill-one/
│   └── SKILL.md          ← Required
├── skill-two/
│   ├── SKILL.md          ← Required
│   └── examples/         ← Optional
│       └── example.py
└── skill-three/
    ├── SKILL.md
    ├── examples/
    │   └── demo.py
    └── templates/
        └── template.txt
```

### ❌ Invalid Structures (Will Be Ignored)

```
your-skills-directory/
├── SKILL.md                  ❌ Not in a folder - WILL BE SKIPPED
├── random-file.txt           ❌ Not a skill folder
├── .hidden-folder/           ❌ Hidden folder - WILL BE SKIPPED
│   └── SKILL.md
└── __pycache__/              ❌ System folder - WILL BE SKIPPED
    └── SKILL.md
```

### Folder Naming Conventions

**Valid folder names:**
- Lowercase with hyphens: `my-skill-name`
- Lowercase with underscores: `excel_advanced`
- Alphanumeric: `skill-name-v2`

**Invalid (will be skipped):**
- Hidden folders starting with `.`
- Private folders starting with `_`
- System folders: `__pycache__`, `node_modules`, `.git`, etc.

## Quick Start

### Using Docker (Recommended)

1. **Create your skills directory:**

```bash
mkdir -p ~/claude-skills/my-first-skill
```

2. **Create a skill file:**

```bash
cat > ~/claude-skills/my-first-skill/SKILL.md << 'EOF'
---
name: "my-first-skill"
description: "My first Claude skill"
---

# My First Skill

This is my first skill for Claude!

## Usage

Simply describe what your skill does here.
EOF
```

3. **Run the server:**

```bash
docker run -i --rm \
  -v ~/claude-skills:/skills:ro \
  mcp-skills-server
```

### Using Poetry (Development)

1. **Clone and install:**

```bash
git clone https://github.com/yourusername/mcp-skills-server.git
cd mcp-skills-server
poetry install
```

2. **Create your skills directory:**

```bash
mkdir -p ~/claude-skills/my-first-skill
# Create SKILL.md as shown above
```

3. **Run the server:**

```bash
export MCP_SKILLS_DIR=~/claude-skills
poetry run mcp-skills
```

## Installation

### Prerequisites

- **Python 3.13+** (for development)
- **Poetry 1.7+** (for dependency management)
- **Docker** (optional, for containerized deployment)

### Install with Poetry

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-skills-server.git
cd mcp-skills-server

# Install dependencies
poetry install

# Verify installation
poetry run mcp-skills --help
```

### Build Docker Image

```bash
# Build the image
docker build -t mcp-skills-server .

# Or use docker-compose
docker-compose build
```

## Usage

### Running Locally

```bash
# Set the skills directory
export MCP_SKILLS_DIR=/path/to/your/skills

# Run the server
poetry run mcp-skills
```

### Running with Docker

```bash
docker run -i --rm \
  -v /path/to/your/skills:/skills:ro \
  -e MCP_SKILLS_LOG_LEVEL=INFO \
  mcp-skills-server
```

### Running with Docker Compose

```bash
# Edit docker-compose.yml to set your skills directory path
docker-compose up mcp-skills
```

### Integrating with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

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
        "mcp-skills-server"
      ]
    }
  }
}
```

**Or using Poetry:**

```json
{
  "mcpServers": {
    "skills": {
      "command": "poetry",
      "args": ["run", "mcp-skills"],
      "cwd": "/path/to/mcp-skills-server",
      "env": {
        "MCP_SKILLS_DIR": "/path/to/your/skills"
      }
    }
  }
}
```

**Important:** Make sure your `${HOME}/claude-skills` directory contains skill folders, not loose SKILL.md files!

## Configuration

Configuration is done via environment variables with the prefix `MCP_SKILLS_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SKILLS_DIR` | `/skills` | Root directory containing skill folders |
| `MCP_SKILLS_HOT_RELOAD` | `true` | Enable automatic reloading |
| `MCP_SKILLS_DEBOUNCE_DELAY` | `0.5` | Delay (seconds) before reload |
| `MCP_SKILLS_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `MCP_SKILLS_SCAN_DEPTH` | `1` | Scan depth (always 1) |

### Example .env File

```bash
MCP_SKILLS_DIR=/path/to/skills
MCP_SKILLS_HOT_RELOAD=true
MCP_SKILLS_DEBOUNCE_DELAY=0.5
MCP_SKILLS_LOG_LEVEL=INFO
```

## Skill File Format

Skills are defined in `SKILL.md` files with YAML frontmatter:

### Minimal Example

```markdown
---
name: "my-skill"
description: "Brief description"
---

# My Skill

Your skill content here in Markdown.
```

### Complete Example

```markdown
---
# Required fields
name: "excel-advanced"
description: "Advanced Excel automation techniques"

# Version and authorship
version: "1.2.0"
author: "Your Name"
created: "2025-01-15"
updated: "2025-10-23"

# Dependencies
dependencies:
  python: ["openpyxl>=3.0.0", "pandas>=2.0.0"]
  system: ["libreoffice"]

# Categorization
category: "office-automation"
tags: ["excel", "spreadsheet", "automation"]
complexity: "intermediate"  # beginner|intermediate|advanced

# Usage guidance
when_to_use:
  - "Automating Excel report generation"
  - "Processing multiple Excel files"
  - "Creating complex formulas programmatically"

# Relationships
related_skills: ["csv-processing", "data-analysis"]

# Examples
has_examples: true
example_files: ["examples/report_generator.py", "templates/report_template.xlsx"]
---

# Excel Advanced Automation

This skill covers advanced Excel automation techniques...

## Features

- Automated report generation
- Formula creation
- Bulk processing

## Examples

See `examples/report_generator.py` for a working example.
```

### Available Metadata Fields

**Required:**
- `name`: Unique identifier (kebab-case recommended)
- `description`: Brief description

**Optional:**
- `version`: Semantic version
- `author`: Creator name
- `created`, `updated`: ISO dates (YYYY-MM-DD)
- `dependencies`: Python packages or system tools
- `category`: Main category for grouping
- `tags`: Array of tags for search
- `complexity`: beginner, intermediate, or advanced
- `when_to_use`: Array of usage scenarios
- `related_skills`: Names of related skills
- `has_examples`: Boolean flag
- `example_files`: Paths to example files (relative to skill folder)

## MCP Resources and Tools

### Resources

The server exposes these MCP resources:

1. **`skill://catalog`** - JSON catalog of all skills with metadata
2. **`skill://{name}`** - Individual skill markdown content

### Tools

Four tools are available for interacting with skills:

#### 1. `search_skills`

Search for skills by query, category, tag, or complexity.

```json
{
  "query": "excel",
  "category": "office-automation",
  "tag": "automation",
  "complexity": "intermediate"
}
```

#### 2. `reload_skills`

Manually trigger a reload of all skills from the directory.

```json
{}
```

#### 3. `get_skill_info`

Get metadata for a specific skill without loading full content.

```json
{
  "name": "excel-advanced"
}
```

#### 4. `list_skill_folders`

List all valid skill folders found in the skills directory.

```json
{}
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/mcp-skills-server.git
cd mcp-skills-server

# Install dependencies (including dev dependencies)
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=mcp_skills --cov-report=html

# Run specific test file
poetry run pytest tests/test_scanner.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy src

# Run all quality checks
poetry run black . && poetry run ruff check . && poetry run mypy src
```

### Development Workflow

1. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test:**
   ```bash
   poetry run pytest
   poetry run mypy src
   ```

3. **Format and lint:**
   ```bash
   poetry run black .
   poetry run ruff check .
   ```

4. **Commit and push:**
   ```bash
   git commit -m "Add feature: description"
   git push origin feature/my-feature
   ```

### Project Structure

```
mcp-skills-server/
├── src/mcp_skills/          # Source code
│   ├── models/              # Data models
│   ├── parsers/             # Skill parsers
│   ├── storage/             # Repository pattern
│   ├── scanner.py           # Directory scanning
│   ├── watcher.py           # Hot-reload watcher
│   ├── server.py            # MCP server
│   ├── config.py            # Configuration
│   └── __main__.py          # CLI entry point
├── tests/                   # Test suite
├── examples/                # Example skills
├── docs/                    # Documentation
└── pyproject.toml           # Poetry configuration
```

## Troubleshooting

### Common Issues

#### Skills Not Loading

**Problem:** No skills are loaded when the server starts.

**Solution:**
1. Check that your skills are in dedicated folders:
   ```
   /skills/my-skill/SKILL.md  ✓
   /skills/SKILL.md           ✗
   ```
2. Verify folder names don't start with `.` or `_`
3. Check logs for detailed error messages

#### Hot-Reload Not Working

**Problem:** Changes to SKILL.md files aren't detected.

**Solution:**
1. Ensure `MCP_SKILLS_HOT_RELOAD=true`
2. Check file is named exactly `SKILL.md`
3. Verify file is in a valid skill folder
4. Look for file watcher errors in logs

#### Parsing Errors

**Problem:** SKILL.md files fail to parse.

**Solution:**
1. Validate YAML frontmatter syntax
2. Ensure frontmatter is between `---` delimiters
3. Check required fields (`name`, `description`) are present
4. Use a YAML validator to check syntax

### Validation Command

Check your skills directory structure:

```bash
poetry run mcp-skills --validate
```

Expected output:
```
✓ /skills/excel-advanced: Valid skill
✓ /skills/python-automation: Valid skill
✗ /skills/SKILL.md: Error - Skills must be in folders
✗ /skills/.hidden: Skipped - Hidden folder
⚠ /skills/empty-folder: Warning - No SKILL.md found

Summary: 2 valid, 1 error, 1 warning, 1 skipped
```

### Logging

Enable debug logging for detailed information:

```bash
export MCP_SKILLS_LOG_LEVEL=DEBUG
poetry run mcp-skills
```

Logs include:
- Folder structure validation messages
- Scan progress and results
- Parse successes and failures
- Hot-reload events
- Detailed error context

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contributing Guide

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass and code is formatted
5. Submit a pull request

### Code Standards

- **Python 3.13+** with type hints
- **Black** for formatting (88 char line length)
- **Ruff** for linting
- **Mypy** for type checking (strict mode)
- **Pytest** for testing (>80% coverage)

## Releases

This project uses automated releases via GitHub Actions.

### Creating a Release

1. Go to **Actions** → **Release** workflow
2. Click **Run workflow**
3. Choose version bump type:
   - `patch` - Bug fixes (0.1.0 → 0.1.1)
   - `minor` - New features (0.1.0 → 0.2.0)
   - `major` - Breaking changes (0.1.0 → 1.0.0)
   - Or specify exact version (e.g., `1.2.3`)
4. Select Docker registry (`docker.io` or `ghcr.io`)
5. Click **Run workflow**

The workflow will:
- ✅ Bump version in `pyproject.toml`
- ✅ Create Git tag and GitHub release
- ✅ Build and push Docker image
- ✅ Run tests to verify release

**Docker Images:**
- Docker Hub: `{username}/mcp-skills-server:{version}`
- GitHub: `ghcr.io/{owner}/mcp-skills-server:{version}`

See [RELEASING.md](RELEASING.md) for detailed release documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/anthropics/python-mcp-sdk)
- Inspired by the need for dynamic skill management in Claude
- Thanks to all contributors!

---

**Note:** This server makes it impossible to misunderstand the folder structure requirement through:
- Clear error messages with folder context
- Comprehensive logging
- Validation at multiple levels
- Detailed documentation
- Working examples

Each skill MUST be in its own folder. This design decision ensures clean organization, easy management, and unambiguous structure. 🎯
