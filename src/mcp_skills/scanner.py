"""
Skill directory scanner with folder structure validation.

This module scans a skills directory for valid skill folders and parses
SKILL.md files. It enforces strict folder structure requirements.

**CRITICAL SCANNING RULES:**
1. Only scan immediate subdirectories (depth = 1)
2. Skip hidden folders (starting with '.')
3. Skip system folders (__pycache__, node_modules, .git, etc.)
4. Each skill must have SKILL.md directly in its folder
5. Ignore any SKILL.md files not in a dedicated folder
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import aiofiles

from mcp_skills.models.skill import Skill
from mcp_skills.parsers.base import SkillParser

logger = logging.getLogger(__name__)


class SkillScanner:
    """
    Scanner for discovering and loading skills from a directory.

    **Required Directory Structure:**
        /skills/                      ← skills_dir
        ├── skill-one/                ← Valid skill folder
        │   └── SKILL.md              ← Required
        ├── skill-two/                ← Valid skill folder
        │   ├── SKILL.md
        │   └── examples/
        ├── .hidden/                  ← Skipped (hidden)
        ├── __pycache__/              ← Skipped (system folder)
        └── SKILL.md                  ← Skipped (not in folder)

    The scanner will:
    1. Iterate through immediate children of skills_dir only
    2. Skip hidden folders (starting with '.')
    3. Skip system/ignored folders
    4. Look for SKILL.md inside each valid folder
    5. Parse and validate each found skill
    6. Log detailed information about the scanning process

    Example:
        >>> scanner = SkillScanner(
        ...     skills_dir=Path("/skills"),
        ...     parser=MarkdownSkillParser(Path("/skills"))
        ... )
        >>> skills = scanner.scan()
        >>> print(f"Loaded {len(skills)} skills")
    """

    # System and hidden folders to ignore
    IGNORED_FOLDERS = {
        "__pycache__",
        "node_modules",
        ".git",
        ".vscode",
        ".idea",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        ".env",
    }

    def __init__(self, skills_dir: Path, parser: SkillParser) -> None:
        """
        Initialize the skill scanner.

        Args:
            skills_dir: Root directory containing skill folders
            parser: Parser instance for parsing SKILL.md files

        Example:
            >>> scanner = SkillScanner(
            ...     Path("/skills"),
            ...     MarkdownSkillParser(Path("/skills"))
            ... )
        """
        self.skills_dir = Path(skills_dir).resolve()
        self.parser = parser
        logger.debug(f"Initialized SkillScanner for directory: {self.skills_dir}")

    def scan(self) -> dict[str, Skill]:
        """
        Scan the skills directory for valid skill folders.

        **Scanning Process:**
        1. Check if skills_dir exists
        2. Iterate through immediate children (depth = 1 only)
        3. For each item:
           - Is it a directory? → Continue
           - Is it hidden or in IGNORED_FOLDERS? → Skip
           - Does it contain SKILL.md? → Parse it
           - No SKILL.md? → Log warning and skip
        4. Collect all successfully parsed skills
        5. Log summary statistics

        Returns:
            Dictionary mapping skill names to Skill objects

        Logs:
            - INFO: Each skill found and loaded
            - WARNING: Invalid folder structures, missing SKILL.md
            - ERROR: Parse failures with details

        Example:
            >>> skills = scanner.scan()
            >>> for name, skill in skills.items():
            ...     print(f"{name}: {skill.description}")

        Expected log output:
            [INFO] Scanning /skills for skill folders...
            [INFO] Found folder: excel-advanced
            [INFO]   ✓ Loaded skill: excel-advanced (version 1.2.0)
            [WARN] Found folder: .hidden-skill (skipping hidden folder)
            [WARN] Folder 'empty-folder' has no SKILL.md file (skipping)
            [INFO] Scan complete: 1 skill loaded, 1 skipped, 0 failed
        """
        logger.info(f"Scanning {self.skills_dir} for skill folders...")
        logger.info(
            f"Expected structure: Each skill must be in its own folder "
            f"with SKILL.md inside"
        )

        # Check if directory exists
        if not self.skills_dir.exists():
            logger.error(
                f"Skills directory does not exist: {self.skills_dir}\n"
                f"Please create the directory and add skill folders."
            )
            return {}

        if not self.skills_dir.is_dir():
            logger.error(
                f"Skills path is not a directory: {self.skills_dir}\n"
                f"Please provide a valid directory path."
            )
            return {}

        skills: dict[str, Skill] = {}
        stats = {"loaded": 0, "skipped": 0, "failed": 0}

        # Scan immediate children only (depth = 1)
        try:
            items = sorted(self.skills_dir.iterdir())
        except Exception as e:
            logger.error(f"Failed to list directory contents: {e}")
            return {}

        for item in items:
            # Skip files in root directory
            if item.is_file():
                if item.name == "SKILL.md":
                    logger.warning(
                        f"Found SKILL.md in root directory (skipping)\n"
                        f"  File: {item}\n"
                        f"  Skills must be in dedicated folders:\n"
                        f"    ✗ {self.skills_dir}/SKILL.md\n"
                        f"    ✓ {self.skills_dir}/my-skill/SKILL.md"
                    )
                    stats["skipped"] += 1
                continue

            # Only process directories
            if not item.is_dir():
                continue

            # Check if folder is valid for containing a skill
            if not self._is_valid_skill_folder(item):
                folder_type = self._get_folder_skip_reason(item)
                logger.debug(f"Skipping folder '{item.name}': {folder_type}")
                stats["skipped"] += 1
                continue

            # Look for SKILL.md in this folder
            logger.debug(f"Checking folder: {item.name}")
            skill_file = self._find_skill_file(item)

            if skill_file is None:
                logger.warning(
                    f"Folder '{item.name}' has no SKILL.md file (skipping)\n"
                    f"  Folder: {item}\n"
                    f"  Expected: {item}/SKILL.md"
                )
                stats["skipped"] += 1
                continue

            # Parse the skill file
            logger.info(f"Found skill folder: {item.name}")
            skill = self.parser.parse(skill_file)

            if skill is None:
                logger.error(
                    f"  ✗ Failed to parse skill in folder '{item.name}'\n"
                    f"    File: {skill_file}\n"
                    f"    Check the logs above for detailed error information"
                )
                stats["failed"] += 1
                continue

            # Successfully loaded
            logger.info(
                f"  ✓ Loaded skill: {skill.name} "
                f"(version {skill.version}, folder: {item.name})"
            )
            skills[skill.name] = skill
            stats["loaded"] += 1

        # Log summary
        logger.info(
            f"Scan complete: {stats['loaded']} skill(s) loaded, "
            f"{stats['skipped']} folder(s) skipped, "
            f"{stats['failed']} parse failure(s)"
        )

        if stats["loaded"] == 0:
            logger.warning(
                f"No skills were loaded from {self.skills_dir}\n"
                f"Make sure you have skill folders with SKILL.md files:\n"
                f"  {self.skills_dir}/\n"
                f"  ├── my-skill/\n"
                f"  │   └── SKILL.md\n"
                f"  └── another-skill/\n"
                f"      └── SKILL.md"
            )

        return skills

    async def scan_async(self) -> dict[str, Skill]:
        """
        Async version of scan for use in async contexts.

        This is useful when integrating with async frameworks or when
        you want non-blocking scanning.

        Returns:
            Dictionary mapping skill names to Skill objects

        Example:
            >>> skills = await scanner.scan_async()
            >>> print(f"Loaded {len(skills)} skills asynchronously")
        """
        # For now, run sync scan in executor
        # In a more advanced implementation, this could use aiofiles
        # for async file I/O
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan)

    def _is_valid_skill_folder(self, folder: Path) -> bool:
        """
        Check if folder is valid for containing a skill.

        A valid skill folder must:
        1. Be a directory
        2. Not start with '.' (not hidden)
        3. Not be in IGNORED_FOLDERS

        Args:
            folder: Path to check

        Returns:
            True if folder should be scanned for skills

        Example:
            >>> scanner._is_valid_skill_folder(Path("/skills/my-skill"))
            True
            >>> scanner._is_valid_skill_folder(Path("/skills/.hidden"))
            False
        """
        # Must be a directory
        if not folder.is_dir():
            return False

        # Skip hidden folders (starting with '.')
        if folder.name.startswith("."):
            return False

        # Skip folders starting with '_' (private folders)
        if folder.name.startswith("_"):
            return False

        # Skip system/ignored folders
        if folder.name in self.IGNORED_FOLDERS:
            return False

        return True

    def _get_folder_skip_reason(self, folder: Path) -> str:
        """
        Get human-readable reason why a folder is being skipped.

        Args:
            folder: Folder being skipped

        Returns:
            Reason string

        Example:
            >>> scanner._get_folder_skip_reason(Path("/skills/.hidden"))
            'Hidden folder (starts with ".")'
        """
        if folder.name.startswith("."):
            return 'Hidden folder (starts with ".")'
        if folder.name.startswith("_"):
            return 'Private folder (starts with "_")'
        if folder.name in self.IGNORED_FOLDERS:
            return f"System folder ({folder.name})"
        return "Unknown reason"

    def _find_skill_file(self, folder: Path) -> Optional[Path]:
        """
        Find SKILL.md in the given folder.

        Only looks for SKILL.md directly in the folder, not in subdirectories.

        Args:
            folder: Folder to search in

        Returns:
            Path to SKILL.md if found, None otherwise

        Example:
            >>> skill_file = scanner._find_skill_file(Path("/skills/my-skill"))
            >>> if skill_file:
            ...     print(f"Found: {skill_file}")
        """
        skill_file = folder / "SKILL.md"
        return skill_file if skill_file.exists() and skill_file.is_file() else None

    def validate_directory_structure(self) -> tuple[bool, list[str]]:
        """
        Validate the overall skills directory structure.

        Checks:
        1. Skills directory exists
        2. Skills directory is actually a directory
        3. Skills directory is readable
        4. At least one valid skill folder exists

        Returns:
            Tuple of (is_valid, list_of_issues)

        Example:
            >>> valid, issues = scanner.validate_directory_structure()
            >>> if not valid:
            ...     for issue in issues:
            ...         print(f"Issue: {issue}")
        """
        issues = []

        # Check existence
        if not self.skills_dir.exists():
            issues.append(f"Skills directory does not exist: {self.skills_dir}")
            return False, issues

        # Check it's a directory
        if not self.skills_dir.is_dir():
            issues.append(f"Skills path is not a directory: {self.skills_dir}")
            return False, issues

        # Check readability
        try:
            list(self.skills_dir.iterdir())
        except Exception as e:
            issues.append(f"Cannot read skills directory: {e}")
            return False, issues

        # Check for at least one valid skill folder
        has_valid_folder = False
        for item in self.skills_dir.iterdir():
            if item.is_dir() and self._is_valid_skill_folder(item):
                skill_file = self._find_skill_file(item)
                if skill_file:
                    has_valid_folder = True
                    break

        if not has_valid_folder:
            issues.append(
                f"No valid skill folders found in {self.skills_dir}\n"
                f"Expected structure:\n"
                f"  {self.skills_dir}/\n"
                f"  ├── skill-name/\n"
                f"  │   └── SKILL.md\n"
                f"  └── another-skill/\n"
                f"      └── SKILL.md"
            )

        return len(issues) == 0, issues

    def __repr__(self) -> str:
        """String representation."""
        return f"SkillScanner(skills_dir={self.skills_dir})"
