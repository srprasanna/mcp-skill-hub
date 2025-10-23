"""
MCP Skills Server implementation.

This module implements the main MCP server that exposes skills as
resources and provides tools for searching and managing skills.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool

from mcp_skills.config import ServerConfig
from mcp_skills.parsers.markdown import MarkdownSkillParser
from mcp_skills.scanner import SkillScanner
from mcp_skills.storage.repository import SkillRepository
from mcp_skills.utils import format_skill_uri, safe_json_dumps
from mcp_skills.watcher import SkillWatcher

logger = logging.getLogger(__name__)


class SkillsServer:
    """
    MCP server for dynamically loading and serving Claude skills.

    This server:
    1. Scans a directory for skill folders (each with SKILL.md)
    2. Exposes skills as MCP resources
    3. Provides tools for searching and managing skills
    4. Supports hot-reloading when files change (optional)

    **Folder Structure Requirement:**
        /skills/
        ├── skill-one/
        │   └── SKILL.md
        ├── skill-two/
        │   ├── SKILL.md
        │   └── examples/
        └── skill-three/
            └── SKILL.md

    Example:
        >>> config = ServerConfig(skills_dir=Path("/skills"))
        >>> server = SkillsServer(config)
        >>> await server.start()
        >>> # ... server is running ...
        >>> await server.stop()
    """

    def __init__(self, config: ServerConfig) -> None:
        """
        Initialize the skills server.

        Args:
            config: Server configuration

        Example:
            >>> config = ServerConfig(
            ...     skills_dir=Path("/skills"),
            ...     hot_reload=True
            ... )
            >>> server = SkillsServer(config)
        """
        self.config = config
        self.repository = SkillRepository()
        self.parser = MarkdownSkillParser(config.skills_dir)
        self.scanner = SkillScanner(config.skills_dir, self.parser)
        self.watcher: Optional[SkillWatcher] = None
        self.mcp_server = Server("mcp-skills-server")

        # Setup MCP handlers
        self._setup_handlers()

        logger.info("Initialized SkillsServer")
        logger.info(f"Skills directory: {config.skills_dir}")
        logger.info(f"Hot reload: {config.hot_reload}")

    def _setup_handlers(self) -> None:
        """Setup MCP protocol handlers."""

        @self.mcp_server.list_resources()
        async def list_resources() -> list[Resource]:
            """List all available skill resources."""
            return await self._list_resources()

        @self.mcp_server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a skill resource by URI."""
            return await self._read_resource(uri)

        @self.mcp_server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return await self._list_tools()

        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Call a tool."""
            return await self._call_tool(name, arguments)

    async def start(self) -> None:
        """
        Start the server and perform initial skill loading.

        This method:
        1. Validates configuration
        2. Logs expected folder structure
        3. Performs initial skill scan
        4. Starts file watcher if hot-reload is enabled

        Example:
            >>> await server.start()
        """
        logger.info("Starting MCP Skills Server...")
        logger.info("=" * 60)
        logger.info(self.config.display_config())
        logger.info("=" * 60)

        # Validate configuration
        is_valid, errors = self.config.validate_config()
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  {error}")
            raise ValueError("Invalid configuration")

        # Validate directory structure
        is_valid, issues = self.scanner.validate_directory_structure()
        if not is_valid:
            logger.warning("Directory structure validation:")
            for issue in issues:
                logger.warning(f"  {issue}")

        # Initial scan
        await self.reload_skills()

        # Start watcher if hot-reload is enabled
        if self.config.hot_reload:
            loop = asyncio.get_event_loop()
            self.watcher = SkillWatcher(
                skills_dir=self.config.skills_dir,
                callback=self._on_skill_change,
                loop=loop,
                debounce_delay=self.config.debounce_delay,
            )
            self.watcher.start()

        logger.info("MCP Skills Server started successfully")
        logger.info(f"Serving {self.repository.count()} skill(s)")

    async def stop(self) -> None:
        """
        Stop the server and cleanup resources.

        Stops the file watcher and cleans up any resources.

        Example:
            >>> await server.stop()
        """
        logger.info("Stopping MCP Skills Server...")

        if self.watcher:
            self.watcher.stop()
            self.watcher = None

        logger.info("MCP Skills Server stopped")

    async def reload_skills(self) -> dict[str, Any]:
        """
        Reload all skills from the directory.

        Returns:
            Dictionary with reload statistics

        Example:
            >>> stats = await server.reload_skills()
            >>> print(f"Loaded {stats['loaded']} skills")
        """
        logger.info("Reloading skills from directory...")

        # Scan for skills
        skills = await self.scanner.scan_async()

        # Clear repository and add all skills
        self.repository.clear()
        loaded_count = 0
        failed_count = 0

        for name, skill in skills.items():
            try:
                self.repository.add(skill)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to add skill '{name}' to repository: {e}")
                failed_count += 1

        stats = {
            "loaded": loaded_count,
            "failed": failed_count,
            "total": self.repository.count(),
        }

        logger.info(
            f"Reload complete: {stats['loaded']} loaded, "
            f"{stats['failed']} failed, "
            f"{stats['total']} total in repository"
        )

        return stats

    async def _on_skill_change(self, path: Path) -> None:
        """
        Callback for file system changes.

        Args:
            path: Path to the changed SKILL.md file
        """
        folder_name = path.parent.name
        logger.info(f"Detected change in skill folder '{folder_name}', reloading...")

        try:
            # Parse the changed skill
            skill = self.parser.parse(path)

            if skill:
                # Update in repository
                self.repository.add(skill)
                logger.info(f"Successfully reloaded skill '{skill.name}'")
            else:
                # Parsing failed, try to remove from repository
                # (skill might have been deleted or become invalid)
                existing_skill = self.repository.get_by_folder(folder_name)
                if existing_skill:
                    self.repository.remove(existing_skill.name)
                    logger.info(
                        f"Removed skill from repository (parsing failed or file deleted): "
                        f"{folder_name}"
                    )

        except Exception as e:
            logger.error(f"Error handling change in folder '{folder_name}': {e}")

    # MCP Protocol Handlers

    async def _list_resources(self) -> list[Resource]:
        """
        List all available resources.

        Resources:
        1. skill://catalog - JSON catalog of all skills
        2. skill://{name} - Individual skill content
        """
        resources = [
            Resource(
                uri="skill://catalog",
                name="Skill Catalog",
                description="Complete catalog of all available skills with metadata",
                mimeType="application/json",
            )
        ]

        # Add resource for each skill
        for skill in self.repository.get_all():
            resources.append(
                Resource(
                    uri=skill.uri(),
                    name=skill.name,
                    description=skill.description,
                    mimeType="text/markdown",
                )
            )

        return resources

    async def _read_resource(self, uri: str) -> str:
        """
        Read a resource by URI.

        Args:
            uri: Resource URI (skill://catalog or skill://{name})

        Returns:
            Resource content

        Raises:
            ValueError: If resource not found
        """
        if uri == "skill://catalog":
            return await self._get_catalog()

        # Extract skill name from URI
        if uri.startswith("skill://"):
            skill_name = uri[8:]  # Remove 'skill://' prefix
            skill = self.repository.get(skill_name)

            if skill:
                return skill.content

            raise ValueError(f"Skill not found: {skill_name}")

        raise ValueError(f"Unknown resource URI: {uri}")

    async def _get_catalog(self) -> str:
        """
        Get the complete skill catalog as JSON.

        Returns:
            JSON string with catalog data
        """
        skills = self.repository.get_all()
        categories = self.repository.group_by_category()

        catalog = {
            "total_skills": len(skills),
            "skills_directory": str(self.config.skills_dir),
            "hot_reload_enabled": self.config.hot_reload,
            "folder_structure": "Each skill must be in its own folder with SKILL.md inside",
            "categories": categories,
            "skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                    "author": skill.author,
                    "folder": skill.folder_path.name,
                    "category": skill.category,
                    "tags": skill.tags,
                    "complexity": skill.complexity,
                    "has_examples": skill.has_examples,
                    "dependencies": skill.dependencies,
                    "uri": skill.uri(),
                }
                for skill in skills
            ],
        }

        return safe_json_dumps(catalog)

    async def _list_tools(self) -> list[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="search_skills",
                description="Search for skills by query, category, tag, or complexity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (searches in name and description)",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category",
                        },
                        "tag": {
                            "type": "string",
                            "description": "Filter by tag",
                        },
                        "complexity": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                            "description": "Filter by complexity level",
                        },
                    },
                },
            ),
            Tool(
                name="reload_skills",
                description="Manually trigger a reload of all skills from the directory",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_skill_info",
                description="Get metadata for a specific skill without loading full content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Skill name",
                        }
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="list_skill_folders",
                description="List all valid skill folders found in the skills directory",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    async def _call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """
        Call a tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of text content responses
        """
        if name == "search_skills":
            return await self._tool_search_skills(arguments)
        elif name == "reload_skills":
            return await self._tool_reload_skills()
        elif name == "get_skill_info":
            return await self._tool_get_skill_info(arguments)
        elif name == "list_skill_folders":
            return await self._tool_list_skill_folders()
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _tool_search_skills(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Search skills tool implementation."""
        results = self.repository.search(
            query=arguments.get("query"),
            category=arguments.get("category"),
            tag=arguments.get("tag"),
            complexity=arguments.get("complexity"),
        )

        response = {
            "found": len(results),
            "query": arguments,
            "results": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                    "category": skill.category,
                    "tags": skill.tags,
                    "complexity": skill.complexity,
                    "folder": skill.folder_path.name,
                    "uri": skill.uri(),
                }
                for skill in results
            ],
        }

        return [TextContent(type="text", text=safe_json_dumps(response))]

    async def _tool_reload_skills(self) -> list[TextContent]:
        """Reload skills tool implementation."""
        stats = await self.reload_skills()
        return [
            TextContent(
                type="text",
                text=f"Reload complete: {stats['loaded']} skills loaded, "
                f"{stats['failed']} failed, {stats['total']} total",
            )
        ]

    async def _tool_get_skill_info(
        self, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Get skill info tool implementation."""
        skill_name = arguments.get("name")
        if not skill_name:
            raise ValueError("Skill name is required")

        skill = self.repository.get(skill_name)
        if not skill:
            return [TextContent(type="text", text=f"Skill not found: {skill_name}")]

        info = {
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "author": skill.author,
            "folder": skill.folder_path.name,
            "folder_path": str(skill.folder_path),
            "category": skill.category,
            "tags": skill.tags,
            "complexity": skill.complexity,
            "has_examples": skill.has_examples,
            "example_files": skill.example_files,
            "dependencies": skill.dependencies,
            "when_to_use": skill.when_to_use,
            "related_skills": skill.related_skills,
            "uri": skill.uri(),
        }

        return [TextContent(type="text", text=safe_json_dumps(info))]

    async def _tool_list_skill_folders(self) -> list[TextContent]:
        """List skill folders tool implementation."""
        folders = []

        if self.config.skills_dir.exists():
            for item in sorted(self.config.skills_dir.iterdir()):
                if not item.is_dir():
                    continue

                has_skill_file = (item / "SKILL.md").exists()
                is_valid = self.scanner._is_valid_skill_folder(item)

                folders.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "has_skill_file": has_skill_file,
                        "is_valid": is_valid,
                        "status": (
                            "valid" if is_valid and has_skill_file
                            else "missing_skill_file" if is_valid
                            else "invalid_folder"
                        ),
                    }
                )

        response = {
            "skills_directory": str(self.config.skills_dir),
            "total_folders": len(folders),
            "folders": folders,
        }

        return [TextContent(type="text", text=safe_json_dumps(response))]

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SkillsServer(skills_dir={self.config.skills_dir}, "
            f"skills={self.repository.count()}, "
            f"hot_reload={self.config.hot_reload})"
        )
