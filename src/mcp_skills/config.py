"""
Configuration management for MCP Skills Server.

This module provides configuration loading from environment variables
using Pydantic Settings.
"""

import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Try to find .env file in current directory or project root
ENV_FILE = Path(".env")
if not ENV_FILE.exists():
    # Try parent directories
    for parent in [Path.cwd(), Path(__file__).parent.parent.parent]:
        candidate = parent / ".env"
        if candidate.exists():
            ENV_FILE = candidate
            break

# Load .env file explicitly using python-dotenv
# This ensures environment variables are set before Pydantic reads them
# Don't load during tests to avoid interfering with test isolation
import sys
if ENV_FILE.exists() and "pytest" not in sys.modules:
    load_dotenv(ENV_FILE)


class ServerConfig(BaseSettings):
    """
    Configuration for the MCP Skills Server.

    All configuration can be set via environment variables with the
    prefix 'MCP_SKILLS_'. For example, to set skills_dir:
        export MCP_SKILLS_DIR=/path/to/skills

    **Configuration Options:**

    skills_dir:
        Root directory containing skill folders.
        Each skill must be in its own dedicated folder with SKILL.md inside.
        Default: /skills

    hot_reload:
        Enable automatic reloading when SKILL.md files change.
        Default: True

    debounce_delay:
        Delay in seconds before triggering reload after file changes.
        Prevents reload spam during rapid edits.
        Default: 0.5

    log_level:
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        Default: INFO

    scan_depth:
        Maximum depth for scanning skill folders.
        Should always be 1 (only immediate subdirectories).
        Default: 1

    Example:
        >>> # From environment
        >>> import os
        >>> os.environ['MCP_SKILLS_DIR'] = '/my/skills'
        >>> os.environ['MCP_SKILLS_LOG_LEVEL'] = 'DEBUG'
        >>> config = ServerConfig()
        >>> print(config.skills_dir)
        /my/skills

        >>> # Programmatically
        >>> config = ServerConfig(
        ...     skills_dir=Path("/skills"),
        ...     hot_reload=True,
        ...     log_level="INFO"
        ... )
    """

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from environment
        populate_by_name=True,  # Allow both field name and alias
    )

    skills_dir: Path = Field(
        default=Path("/skills"),
        description="Root directory containing skill folders (each skill in its own folder)",
        validation_alias="MCP_SKILLS_DIR",
    )

    hot_reload: bool = Field(
        default=True,
        description="Enable hot-reloading of skills when SKILL.md files change",
        validation_alias="MCP_SKILLS_HOT_RELOAD",
    )

    debounce_delay: float = Field(
        default=0.5,
        ge=0.0,
        le=10.0,
        description="Debounce delay in seconds for file change events",
        validation_alias="MCP_SKILLS_DEBOUNCE_DELAY",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="MCP_SKILLS_LOG_LEVEL",
    )

    scan_depth: int = Field(
        default=1,
        ge=1,
        le=1,
        description="Scan depth for skill folders (should always be 1)",
        validation_alias="MCP_SKILLS_SCAN_DEPTH",
    )

    def configure_logging(self) -> None:
        """
        Configure logging based on log_level setting.

        Sets up a console handler with a detailed format including folder context.

        Example:
            >>> config = ServerConfig(log_level="DEBUG")
            >>> config.configure_logging()
        """
        # Convert log level string to logging level
        numeric_level = getattr(logging, self.log_level.upper(), None)
        if not isinstance(numeric_level, int):
            logger.warning(
                f"Invalid log level: {self.log_level}, defaulting to INFO"
            )
            numeric_level = logging.INFO

        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format="[%(levelname)s] %(name)s: %(message)s",
            force=True,
        )

        logger.info(f"Logging configured with level: {self.log_level}")

    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate configuration settings.

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            >>> config = ServerConfig()
            >>> valid, errors = config.validate_config()
            >>> if not valid:
            ...     for error in errors:
            ...         print(f"Error: {error}")
        """
        errors = []

        # Validate skills_dir
        if not self.skills_dir.exists():
            errors.append(
                f"Skills directory does not exist: {self.skills_dir}\n"
                f"  Create it with: mkdir -p {self.skills_dir}"
            )
        elif not self.skills_dir.is_dir():
            errors.append(
                f"Skills path is not a directory: {self.skills_dir}"
            )

        # Validate debounce_delay
        if self.debounce_delay < 0:
            errors.append(
                f"Debounce delay must be >= 0, got: {self.debounce_delay}"
            )

        # Validate log_level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(
                f"Invalid log level: {self.log_level}\n"
                f"  Valid levels: {', '.join(valid_levels)}"
            )

        # Validate scan_depth
        if self.scan_depth != 1:
            errors.append(
                f"Scan depth must be 1 (only immediate subdirectories), got: {self.scan_depth}\n"
                f"  Skills must be in direct subfolders of {self.skills_dir}"
            )

        return len(errors) == 0, errors

    def display_config(self) -> str:
        """
        Get a human-readable display of current configuration.

        Returns:
            Formatted configuration string

        Example:
            >>> config = ServerConfig()
            >>> print(config.display_config())
        """
        return f"""
MCP Skills Server Configuration
================================
Skills Directory:  {self.skills_dir}
Hot Reload:        {self.hot_reload}
Debounce Delay:    {self.debounce_delay}s
Log Level:         {self.log_level}
Scan Depth:        {self.scan_depth}

Expected Folder Structure:
  {self.skills_dir}/
  ├── skill-one/
  │   └── SKILL.md
  ├── skill-two/
  │   ├── SKILL.md
  │   └── examples/
  └── skill-three/
      └── SKILL.md

Note: Each skill MUST be in its own dedicated folder.
""".strip()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ServerConfig(skills_dir={self.skills_dir}, "
            f"hot_reload={self.hot_reload}, log_level={self.log_level})"
        )
