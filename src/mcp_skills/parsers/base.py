"""
Base parser interface for skill files.

This module defines the abstract base class that all skill parsers must implement.
All parsers enforce the critical requirement that skills must be in dedicated folders.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from mcp_skills.models.skill import Skill

logger = logging.getLogger(__name__)


class SkillParser(ABC):
    """
    Abstract base class for skill parsers.

    All skill parsers must validate that SKILL.md files are located in
    dedicated skill folders, not loose in the root directory.

    **Required Folder Structure:**
        /skills/
        ├── my-skill/
        │   └── SKILL.md      ✓ Valid
        └── SKILL.md          ✗ Invalid (not in a folder)

    Subclasses must implement:
        - parse(path: Path) -> Optional[Skill]
        - validate(content: str) -> bool
    """

    def __init__(self, skills_dir: Path) -> None:
        """
        Initialize the parser.

        Args:
            skills_dir: Root directory containing skill folders
        """
        self.skills_dir = Path(skills_dir)

    @abstractmethod
    def parse(self, path: Path) -> Optional[Skill]:
        """
        Parse a skill file and return a Skill object.

        This method must validate that the skill file is in a proper folder structure
        before attempting to parse it.

        Args:
            path: Full path to the SKILL.md file (must be inside a dedicated folder)

        Returns:
            Skill object if parsing succeeds, None if parsing fails

        Example:
            ✓ /skills/excel-advanced/SKILL.md  → Valid
            ✗ /skills/SKILL.md                  → Invalid (not in folder)

        Note:
            Implementations should log detailed errors including folder context
            when parsing fails.
        """
        pass

    @abstractmethod
    def validate(self, content: str) -> bool:
        """
        Validate skill file format without fully parsing it.

        Args:
            content: Raw file content to validate

        Returns:
            True if the content appears to be a valid skill file format

        Example:
            >>> parser = MarkdownSkillParser(Path("/skills"))
            >>> content = "---\\nname: test\\n---\\n# Content"
            >>> parser.validate(content)
            True
        """
        pass

    def validate_folder_structure(self, skill_file: Path) -> tuple[bool, Optional[str]]:
        """
        Validate that the skill file is in a proper folder structure.

        **CRITICAL VALIDATION:**
        The SKILL.md file must be:
        1. Inside a folder (not in the root skills directory)
        2. The folder must be a direct child of skills_dir (depth = 1)
        3. The folder must not be hidden or a system folder

        Args:
            skill_file: Full path to SKILL.md file

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if structure is valid
            - (False, error_message) if structure is invalid

        Example:
            Valid structures:
                /skills/my-skill/SKILL.md           ✓
                /skills/excel-advanced/SKILL.md     ✓
                /skills/python_tips/SKILL.md        ✓

            Invalid structures:
                /skills/SKILL.md                    ✗ Not in a folder
                /skills/subfolder/skill/SKILL.md    ✗ Too deeply nested
                /skills/.hidden/SKILL.md            ✗ Hidden folder
        """
        skill_file = Path(skill_file).resolve()
        folder = skill_file.parent

        # Check 1: File must be named SKILL.md
        if skill_file.name != "SKILL.md":
            return False, (
                f"Skill file must be named 'SKILL.md', got: {skill_file.name}\n"
                f"  Path: {skill_file}"
            )

        # Check 2: Must be in a folder (not in root skills directory)
        if folder == self.skills_dir:
            return False, (
                f"SKILL.md cannot be in the root skills directory.\n"
                f"  Found: {skill_file}\n"
                f"  Each skill must be in its own dedicated folder:\n"
                f"    ✓ {self.skills_dir}/my-skill/SKILL.md\n"
                f"    ✗ {self.skills_dir}/SKILL.md"
            )

        # Check 3: Folder must be a direct child of skills_dir (depth = 1)
        if folder.parent != self.skills_dir:
            return False, (
                f"Skill folders must be direct children of the skills directory.\n"
                f"  Skills dir: {self.skills_dir}\n"
                f"  Skill file: {skill_file}\n"
                f"  Skill folder: {folder}\n"
                f"  Expected structure: {self.skills_dir}/<skill-name>/SKILL.md\n"
                f"  Skills nested more than 1 level deep are not supported."
            )

        # Check 4: Folder must not be hidden (starting with '.')
        if folder.name.startswith('.'):
            return False, (
                f"Hidden skill folders (starting with '.') are not allowed.\n"
                f"  Found: {folder}\n"
                f"  Please use a visible folder name."
            )

        # Check 5: Folder must not be a system folder
        from mcp_skills.scanner import SkillScanner
        if folder.name in SkillScanner.IGNORED_FOLDERS:
            return False, (
                f"System folders are not allowed for skills.\n"
                f"  Found: {folder.name}\n"
                f"  Ignored folders: {', '.join(sorted(SkillScanner.IGNORED_FOLDERS))}"
            )

        # Check 6: Folder must exist and be a directory
        if not folder.exists():
            return False, f"Skill folder does not exist: {folder}"

        if not folder.is_dir():
            return False, (
                f"Skill folder path is not a directory: {folder}\n"
                f"Each skill must be in its own folder."
            )

        return True, None

    def _extract_folder_path(self, skill_file: Path) -> Path:
        """
        Extract the skill folder path from a SKILL.md file path.

        Args:
            skill_file: Path to SKILL.md file

        Returns:
            Path to the skill's parent folder

        Example:
            >>> parser._extract_folder_path(Path("/skills/my-skill/SKILL.md"))
            Path("/skills/my-skill")
        """
        return skill_file.parent
