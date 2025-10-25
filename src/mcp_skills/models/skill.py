"""
Skill data model.

This module defines the Skill Pydantic model that represents a skill
loaded from a SKILL.md file within a dedicated skill folder.

**IMPORTANT**: Skills must be located in their own folders:
    /skills/my-skill/SKILL.md  ✓ Valid
    /skills/SKILL.md           ✗ Invalid
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Skill(BaseModel):
    """
    Represents a skill with metadata and content.

    A skill must be located in a dedicated folder within the skills directory:
        /skills/
        ├── my-skill/
        │   ├── SKILL.md          ← Required
        │   └── examples/         ← Optional
        │       └── demo.py

    Required Fields:
        name: Unique identifier for the skill (e.g., "excel-advanced")
        description: Brief description of what the skill does
        content: Markdown content (excluding YAML frontmatter)
        path: Full path to the SKILL.md file
        folder_path: Full path to the skill's parent folder

    Optional Metadata:
        version: Semantic version (default: "1.0.0")
        author: Skill author name
        created: ISO date when skill was created
        updated: ISO date when skill was last updated
        dependencies: List of dependencies (Python packages, system tools)
        tags: Categorization tags
        category: Main category
        complexity: Difficulty level (beginner|intermediate|advanced)
        when_to_use: List of use case scenarios
        related_skills: Names of related skills
        has_examples: Whether the skill folder contains examples
        example_files: Paths to example files (relative to skill folder)

    Example:
        >>> skill = Skill(
        ...     name="excel-advanced",
        ...     description="Advanced Excel automation",
        ...     content="# Excel Advanced Skill...",
        ...     path=Path("/skills/excel-advanced/SKILL.md"),
        ...     folder_path=Path("/skills/excel-advanced"),
        ...     version="1.2.0",
        ...     tags=["excel", "automation"],
        ...     complexity="intermediate"
        ... )
        >>> skill.uri()
        'skill://excel-advanced'
    """

    # Required fields
    name: str = Field(..., description="Unique skill identifier")
    description: str = Field(..., description="Brief skill description")
    content: str = Field(..., description="Markdown content without frontmatter")
    path: Path = Field(..., description="Full path to SKILL.md file")
    folder_path: Path = Field(..., description="Full path to skill folder")

    # Version and authorship
    version: str = Field(default="1.0.0", description="Semantic version")
    author: Optional[str] = Field(default=None, description="Skill author")
    created: Optional[str] = Field(default=None, description="Creation date (ISO)")
    updated: Optional[str] = Field(default=None, description="Last update date (ISO)")

    # Dependencies
    dependencies: list[str] = Field(
        default_factory=list, description="Python packages or system dependencies"
    )

    # Categorization
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    category: Optional[str] = Field(default=None, description="Main category")
    complexity: Optional[str] = Field(
        default=None, description="Difficulty level: beginner|intermediate|advanced"
    )

    # Usage guidance
    when_to_use: list[str] = Field(
        default_factory=list, description="Usage scenarios"
    )

    # Relationships
    related_skills: list[str] = Field(
        default_factory=list, description="Related skill names"
    )

    # Examples
    has_examples: bool = Field(default=False, description="Has example files")
    example_files: list[str] = Field(
        default_factory=list, description="Example file paths (relative to folder)"
    )

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
        json_encoders = {Path: str}

    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v: Optional[str]) -> Optional[str]:
        """Validate complexity level."""
        if v is not None and v not in ["beginner", "intermediate", "advanced"]:
            raise ValueError(
                f"Complexity must be 'beginner', 'intermediate', or 'advanced', got: {v}"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name format."""
        if not v or not v.strip():
            raise ValueError("Skill name cannot be empty")
        return v.strip()

    @field_validator("folder_path")
    @classmethod
    def validate_folder_structure(cls, v: Path, info: any) -> Path:
        """
        Validate that the skill is in a proper folder structure.

        The SKILL.md file must be directly inside a skill folder, not in the root.

        Example:
            ✓ /skills/my-skill/SKILL.md
            ✗ /skills/SKILL.md
        """
        if not v.is_dir():
            raise ValueError(
                f"Folder path must be a directory: {v}\n"
                f"Skills must be in dedicated folders, not loose files."
            )
        return v

    def uri(self) -> str:
        """
        Get the MCP resource URI for this skill.

        Returns:
            URI in the format 'skill://{name}'

        Example:
            >>> skill.uri()
            'skill://excel-advanced'
        """
        return f"skill://{self.name}"

    def to_dict(self) -> dict[str, any]:
        """
        Convert skill to a serializable dictionary.

        Returns:
            Dictionary representation with paths converted to strings

        Example:
            >>> skill.to_dict()
            {
                'name': 'excel-advanced',
                'description': '...',
                'uri': 'skill://excel-advanced',
                ...
            }
        """
        data = self.model_dump()
        data["path"] = str(self.path)
        data["folder_path"] = str(self.folder_path)
        data["uri"] = self.uri()
        return data

    def validate_skill(self) -> tuple[bool, list[str]]:
        """
        Validate skill data integrity.

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> valid, errors = skill.validate_skill()
            >>> if not valid:
            ...     print(f"Validation errors: {errors}")
        """
        errors = []

        # Check required fields
        if not self.name:
            errors.append("Skill name is required")
        if not self.description:
            errors.append("Skill description is required")
        if not self.content:
            errors.append("Skill content is required")

        # Check file exists
        if not self.path.exists():
            errors.append(f"SKILL.md file not found: {self.path}")

        # Check folder exists and is valid
        if not self.folder_path.exists():
            errors.append(f"Skill folder not found: {self.folder_path}")
        elif not self.folder_path.is_dir():
            errors.append(
                f"Skill folder path is not a directory: {self.folder_path}\n"
                f"Each skill must be in its own folder."
            )

        # Check folder structure: SKILL.md should be directly in folder
        if self.path.parent != self.folder_path:
            errors.append(
                f"Invalid folder structure: SKILL.md must be directly in skill folder\n"
                f"  Expected: {self.folder_path}/SKILL.md\n"
                f"  Got: {self.path}\n"
                f"Each skill must be in its own dedicated folder."
            )

        # Validate example files if specified
        if self.has_examples and not self.example_files:
            errors.append("has_examples is True but no example_files specified")

        for example_file in self.example_files:
            example_path = self.folder_path / example_file
            if not example_path.exists():
                errors.append(f"Example file not found: {example_path}")

        return len(errors) == 0, errors

    def get_example_path(self, filename: str) -> Path:
        """
        Get full path to an example file.

        Args:
            filename: Relative path to example file (e.g., "examples/demo.py")

        Returns:
            Full path to the example file

        Example:
            >>> path = skill.get_example_path("examples/demo.py")
            >>> print(path)
            /skills/my-skill/examples/demo.py
        """
        return self.folder_path / filename

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Skill(name={self.name!r}, version={self.version}, "
            f"folder={self.folder_path.name})"
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Skill(name={self.name!r}, description={self.description!r}, "
            f"version={self.version}, folder={self.folder_path})"
        )
