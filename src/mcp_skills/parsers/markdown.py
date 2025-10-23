"""
Markdown skill parser with YAML frontmatter support.

This parser handles SKILL.md files with YAML frontmatter metadata.
It enforces strict folder structure requirements.
"""

import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from mcp_skills.models.skill import Skill
from mcp_skills.parsers.base import SkillParser

logger = logging.getLogger(__name__)


class MarkdownSkillParser(SkillParser):
    """
    Parser for SKILL.md files with YAML frontmatter.

    Expected format:
        ---
        name: "skill-name"
        description: "Brief description"
        version: "1.0.0"
        tags: ["tag1", "tag2"]
        ---

        # Skill Content

        Markdown content here...

    **CRITICAL**: This parser enforces that SKILL.md files must be in
    dedicated skill folders:

        ✓ /skills/my-skill/SKILL.md
        ✗ /skills/SKILL.md

    Example:
        >>> parser = MarkdownSkillParser(Path("/skills"))
        >>> skill = parser.parse(Path("/skills/excel-advanced/SKILL.md"))
        >>> if skill:
        ...     print(f"Loaded: {skill.name}")
    """

    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL | re.MULTILINE
    )

    def parse(self, path: Path) -> Optional[Skill]:
        """
        Parse a SKILL.md file with YAML frontmatter.

        Args:
            path: Full path to SKILL.md file (must be in a dedicated folder)

        Returns:
            Skill object if parsing succeeds, None otherwise

        Logs errors with full folder context for debugging.

        Example:
            >>> parser = MarkdownSkillParser(Path("/skills"))
            >>> skill = parser.parse(Path("/skills/my-skill/SKILL.md"))
        """
        path = Path(path)

        # Validate folder structure FIRST
        is_valid, error_msg = self.validate_folder_structure(path)
        if not is_valid:
            logger.error(
                f"Invalid folder structure for skill file:\n{error_msg}\n"
                f"  File: {path}"
            )
            return None

        # Read file content
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(
                f"Failed to read skill file in folder '{path.parent.name}':\n"
                f"  File: {path}\n"
                f"  Error: {e}"
            )
            return None

        # Validate format
        if not self.validate(content):
            logger.error(
                f"Invalid SKILL.md format in folder '{path.parent.name}':\n"
                f"  File: {path}\n"
                f"  Expected: YAML frontmatter between '---' delimiters\n"
                f"  Example:\n"
                f"    ---\n"
                f"    name: \"my-skill\"\n"
                f"    description: \"Description\"\n"
                f"    ---\n"
                f"    # Content here"
            )
            return None

        # Parse frontmatter and content
        try:
            metadata, markdown_content = self._parse_frontmatter(content)
        except Exception as e:
            logger.error(
                f"Failed to parse YAML frontmatter in folder '{path.parent.name}':\n"
                f"  File: {path}\n"
                f"  Error: {e}\n"
                f"  Make sure YAML is properly formatted between '---' delimiters"
            )
            return None

        # Extract required fields
        name = metadata.get("name")
        description = metadata.get("description")

        if not name:
            logger.error(
                f"Missing required field 'name' in skill folder '{path.parent.name}':\n"
                f"  File: {path}\n"
                f"  Add 'name: \"your-skill-name\"' to the YAML frontmatter"
            )
            return None

        if not description:
            logger.error(
                f"Missing required field 'description' in skill '{name}':\n"
                f"  Folder: {path.parent.name}\n"
                f"  File: {path}\n"
                f"  Add 'description: \"Brief description\"' to the YAML frontmatter"
            )
            return None

        # Extract folder path
        folder_path = self._extract_folder_path(path)

        # Parse dependencies (support both flat list and nested dict)
        dependencies = self._parse_dependencies(metadata.get("dependencies", []))

        # Create Skill object
        try:
            skill = Skill(
                name=name,
                description=description,
                content=markdown_content.strip(),
                path=path,
                folder_path=folder_path,
                version=metadata.get("version", "1.0.0"),
                author=metadata.get("author"),
                created=metadata.get("created"),
                updated=metadata.get("updated"),
                dependencies=dependencies,
                tags=metadata.get("tags", []),
                category=metadata.get("category"),
                complexity=metadata.get("complexity"),
                when_to_use=metadata.get("when_to_use", []),
                related_skills=metadata.get("related_skills", []),
                has_examples=metadata.get("has_examples", False),
                example_files=metadata.get("example_files", []),
            )

            # Validate the skill
            is_valid, errors = skill.validate_skill()
            if not is_valid:
                logger.error(
                    f"Skill validation failed for '{name}' in folder '{path.parent.name}':\n"
                    f"  Folder: {folder_path}\n"
                    f"  Errors:\n" + "\n".join(f"    - {err}" for err in errors)
                )
                return None

            logger.debug(
                f"Successfully parsed skill '{name}' from folder '{path.parent.name}'"
            )
            return skill

        except Exception as e:
            logger.error(
                f"Failed to create Skill object for '{name}' in folder '{path.parent.name}':\n"
                f"  Folder: {folder_path}\n"
                f"  Error: {e}"
            )
            return None

    def validate(self, content: str) -> bool:
        """
        Validate that content has proper YAML frontmatter format.

        Args:
            content: Raw file content

        Returns:
            True if content has valid frontmatter format

        Example:
            >>> parser = MarkdownSkillParser(Path("/skills"))
            >>> content = "---\\nname: test\\n---\\n# Content"
            >>> parser.validate(content)
            True
        """
        return self.FRONTMATTER_PATTERN.match(content) is not None

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """
        Parse YAML frontmatter and markdown content.

        Args:
            content: Raw file content with frontmatter

        Returns:
            Tuple of (metadata_dict, markdown_content)

        Raises:
            ValueError: If frontmatter is malformed or YAML is invalid
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError("Content does not contain valid YAML frontmatter")

        yaml_content = match.group(1)
        markdown_content = match.group(2)

        try:
            metadata = yaml.safe_load(yaml_content)
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, dict):
                raise ValueError(
                    f"YAML frontmatter must be a dictionary, got: {type(metadata)}"
                )
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

        return metadata, markdown_content

    def _parse_dependencies(self, deps: Any) -> list[str]:
        """
        Parse dependencies from various formats.

        Supports:
        - Flat list: ["package1", "package2"]
        - Nested dict: {"python": ["pkg1"], "system": ["tool1"]}

        Args:
            deps: Dependencies in various formats

        Returns:
            Flat list of dependency strings

        Example:
            >>> parser._parse_dependencies(["numpy", "pandas"])
            ['numpy', 'pandas']
            >>> parser._parse_dependencies({"python": ["numpy"], "system": ["git"]})
            ['python:numpy', 'system:git']
        """
        if isinstance(deps, list):
            return deps

        if isinstance(deps, dict):
            result = []
            for category, items in deps.items():
                if isinstance(items, list):
                    for item in items:
                        result.append(f"{category}:{item}")
                else:
                    result.append(f"{category}:{items}")
            return result

        return []
