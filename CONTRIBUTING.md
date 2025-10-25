# Contributing to MCP Skills Server

Thank you for your interest in contributing to the MCP Skills Server! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.13+
- Poetry 1.7+
- Git
- Docker (optional, for container testing)

### Setting Up Development Environment

1. **Fork and clone the repository:**

```bash
git clone https://github.com/your-username/mcp-skill-hub.git
cd mcp-skill-hub
```

2. **Install dependencies:**

```bash
poetry install
```

3. **Activate the virtual environment:**

```bash
poetry shell
```

4. **Verify installation:**

```bash
poetry run pytest
poetry run mypy src
```

## Development Workflow

### Creating a New Feature

1. **Create a new branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests:**

```bash
poetry run pytest
poetry run pytest --cov=mcp_skills
```

4. **Check code quality:**

```bash
poetry run black .
poetry run ruff check .
poetry run mypy src
```

5. **Commit your changes:**

```bash
git add .
git commit -m "feat: add new feature description"
```

6. **Push to your fork:**

```bash
git push origin feature/your-feature-name
```

7. **Create a pull request** on GitHub

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `style:` Code style changes (formatting, etc.)
- `chore:` Maintenance tasks

Examples:
```
feat: add validation command for skills directory
fix: resolve parser issue with nested frontmatter
docs: update README with folder structure examples
test: add integration tests for hot-reload
```

## Code Standards

### Python Style

- **Python 3.13+** with modern type hints
- **Black** for code formatting (88 character line length)
- **Ruff** for linting
- **Mypy** for type checking in strict mode

### Type Hints

All functions and methods must have complete type hints:

```python
def parse_skill(path: Path) -> Optional[Skill]:
    """Parse a skill file."""
    ...
```

### Docstrings

Use Google-style docstrings for all public APIs:

```python
def scan(self) -> dict[str, Skill]:
    """
    Scan the skills directory for valid skill folders.

    Returns:
        Dictionary mapping skill names to Skill objects

    Raises:
        ValueError: If directory doesn't exist

    Example:
        >>> scanner = SkillScanner(Path("/skills"))
        >>> skills = scanner.scan()
    """
    ...
```

### Error Handling

- Provide detailed error messages with folder context
- Log errors appropriately
- Raise exceptions with helpful information
- Handle edge cases gracefully

Example:
```python
if not folder.exists():
    logger.error(
        f"Skill folder does not exist: {folder}\n"
        f"  Expected structure: {self.skills_dir}/<skill-name>/SKILL.md"
    )
    return None
```

### Logging

- Use module-level loggers: `logger = logging.getLogger(__name__)`
- Include folder context in messages
- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for recoverable issues
  - `ERROR`: Error messages for failures

Example:
```python
logger.info(f"Successfully loaded skill '{skill.name}' from folder '{folder.name}'")
logger.error(f"Failed to parse skill in folder '{folder.name}': {error}")
```

## Testing Guidelines

### Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── conftest.py           # Pytest fixtures
├── test_models.py        # Model tests
├── test_parsers.py       # Parser tests
├── test_scanner.py       # Scanner tests
├── test_repository.py    # Repository tests
├── test_structure.py     # Folder structure tests
└── fixtures/             # Test data
    └── sample_skills/
```

### Writing Tests

1. **Use descriptive test names:**

```python
def test_skill_must_be_in_folder():
    """Test that skills not in folders are rejected."""
    ...

def test_scanner_skips_hidden_folders():
    """Test that folders starting with . are skipped."""
    ...
```

2. **Test both success and failure cases:**

```python
def test_parse_valid_skill():
    """Test parsing a valid skill succeeds."""
    ...

def test_parse_invalid_yaml_fails():
    """Test parsing invalid YAML fails gracefully."""
    ...
```

3. **Use fixtures for common setup:**

```python
@pytest.fixture
def sample_skill_folder(tmp_path):
    """Create a sample skill folder for testing."""
    skill_folder = tmp_path / "test-skill"
    skill_folder.mkdir()
    skill_file = skill_folder / "SKILL.md"
    skill_file.write_text("---\nname: test\n---\n# Test")
    return skill_folder
```

4. **Test folder structure validation:**

```python
def test_validate_folder_structure_rejects_root_files():
    """Test that SKILL.md in root directory is rejected."""
    ...
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_scanner.py

# Run with coverage
poetry run pytest --cov=mcp_skills --cov-report=html

# Run with verbose output
poetry run pytest -v

# Run specific test
poetry run pytest tests/test_scanner.py::test_scan_valid_skills
```

### Test Coverage

- Maintain >80% code coverage
- Test edge cases and error conditions
- Include integration tests for critical paths
- Test folder structure validation thoroughly

## Documentation

### Code Documentation

- Document all public APIs with docstrings
- Include examples in docstrings
- Explain folder structure requirements
- Document error conditions

### User Documentation

When adding features, update:
- `README.md` - Main user documentation
- `CONTRIBUTING.md` - This file
- Inline code comments for complex logic
- Example skills if relevant

### Folder Structure Emphasis

When writing documentation or error messages:
- Always emphasize the folder structure requirement
- Provide visual examples
- Show both valid and invalid structures
- Include folder context in error messages

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   poetry run pytest
   ```

2. **Check code quality:**
   ```bash
   poetry run black .
   poetry run ruff check .
   poetry run mypy src
   ```

3. **Update documentation:**
   - Update README if adding features
   - Add/update docstrings
   - Update changelog if applicable

4. **Test your changes:**
   - Test manually with example skills
   - Verify folder structure validation works
   - Test hot-reload if applicable

### PR Guidelines

1. **Title:** Use conventional commit format
   - `feat: add skill validation command`
   - `fix: resolve parser issue with nested YAML`

2. **Description:** Include:
   - What changed and why
   - Any breaking changes
   - How to test the changes
   - Related issues (if any)

3. **Review:** Address reviewer feedback promptly

4. **Merge:** Squash commits when merging

### Example PR Description

```markdown
## Description
Add validation command to check skills directory structure

## Changes
- Add `--validate` CLI flag
- Implement directory structure validation
- Add comprehensive error reporting
- Include folder structure examples in output

## Testing
1. Create test skills directory with valid/invalid structures
2. Run `poetry run mcp-skills --validate`
3. Verify output shows clear validation results

## Related Issues
Closes #123
```

## Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** of the code
3. **Check documentation** for known issues

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**Folder Structure**
Show your skills directory structure:
```
/skills/
├── my-skill/
│   └── SKILL.md
```

**To Reproduce**
Steps to reproduce:
1. Create skill folder with...
2. Run command...
3. See error...

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Logs**
```
Paste relevant log output
```

**Environment**
- Python version:
- Poetry version:
- OS:
- Installation method: (Poetry/Docker)

**Additional context**
Any other relevant information.
```

## Suggesting Enhancements

### Enhancement Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Would this affect folder structure requirements?**
Yes/No - If yes, explain how.

**Additional context**
Any other context, examples, or screenshots.
```

## Questions?

If you have questions:
1. Check the [README](README.md)
2. Look through existing [issues](https://github.com/yourusername/mcp-skill-hub/issues)
3. Open a new issue with your question

## Recognition

Contributors will be recognized in:
- README acknowledgments
- Release notes
- Git commit history

Thank you for contributing! 🎉
