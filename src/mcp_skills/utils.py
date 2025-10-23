"""Utility functions for MCP Skills Server."""

import json
from pathlib import Path
from typing import Any


def format_skill_uri(skill_name: str) -> str:
    """
    Format a skill name into a URI.

    Args:
        skill_name: Name of the skill

    Returns:
        URI in format 'skill://{name}'

    Example:
        >>> format_skill_uri("excel-advanced")
        'skill://excel-advanced'
    """
    return f"skill://{skill_name}"


def safe_json_dumps(data: Any, indent: int = 2) -> str:
    """
    Safely serialize data to JSON, handling Path objects.

    Args:
        data: Data to serialize
        indent: JSON indentation level

    Returns:
        JSON string

    Example:
        >>> safe_json_dumps({"path": Path("/test")})
        '{\\n  "path": "/test"\\n}'
    """
    def default_encoder(obj: Any) -> Any:
        """Custom encoder for non-serializable objects."""
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(data, indent=indent, default=default_encoder)


def validate_skill_name(name: str) -> tuple[bool, str]:
    """
    Validate a skill name format.

    Valid formats:
    - Lowercase with hyphens: my-skill
    - Lowercase with underscores: my_skill
    - Alphanumeric: myskill123

    Invalid:
    - Starting with numbers: 123skill
    - Special characters: my@skill
    - Empty or whitespace only

    Args:
        name: Skill name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_skill_name("my-skill")
        (True, '')
        >>> validate_skill_name("my@skill")
        (False, 'Skill names can only contain...')
    """
    if not name or not name.strip():
        return False, "Skill name cannot be empty"

    name = name.strip()

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not all(c.isalnum() or c in "-_" for c in name):
        return False, "Skill names can only contain letters, numbers, hyphens, and underscores"

    # Should not start with number
    if name[0].isdigit():
        return False, "Skill names should not start with a number"

    # Recommend lowercase
    if name != name.lower():
        return True, "Warning: Skill names should be lowercase"

    return True, ""
