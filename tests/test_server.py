"""
Tests for the MCP Skills Server.

These tests use mocking to test server functionality without
requiring actual MCP protocol integration.

Tests cover:
- Server initialization
- Resource listing and reading
- Tool execution
- Hot-reload integration
- Lifecycle management
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mcp_skills.config import ServerConfig
from mcp_skills.models.skill import Skill
from mcp_skills.server import SkillsServer


@pytest.fixture
def mock_config(tmp_path: Path) -> ServerConfig:
    """Create a mock server configuration."""
    skills_dir = tmp_path / "skills_test"
    skills_dir.mkdir(exist_ok=True)
    return ServerConfig(
        skills_dir=skills_dir,
        hot_reload=True,
        debounce_delay=0.5,
        log_level="INFO",
    )


@pytest.fixture
def sample_skill(tmp_path: Path) -> Skill:
    """Create a sample skill for testing."""
    folder = tmp_path / "test-skill"
    folder.mkdir()
    skill_file = folder / "SKILL.md"
    skill_file.write_text("content")

    return Skill(
        name="test-skill",
        description="Test skill",
        content="Test content",
        path=skill_file,
        folder_path=folder,
        tags=["test"],
        category="testing",
    )


class TestServerInitialization:
    """Tests for server initialization."""

    def test_create_server(self, mock_config: ServerConfig) -> None:
        """Test creating a server instance."""
        server = SkillsServer(mock_config)

        assert server.config == mock_config
        assert server.repository is not None
        assert server.parser is not None
        assert server.scanner is not None
        assert server.watcher is None  # Not started yet

    def test_server_repr(self, mock_config: ServerConfig) -> None:
        """Test server string representation."""
        server = SkillsServer(mock_config)

        repr_str = repr(server)

        assert "SkillsServer" in repr_str
        assert "skills=0" in repr_str
        assert "hot_reload=True" in repr_str


class TestServerLifecycle:
    """Tests for server lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_server(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test starting the server."""
        # Update config to use the test skills directory
        mock_config.skills_dir = valid_skill_folder.parent
        mock_config.hot_reload = False  # Disable to avoid threading issues in test

        server = SkillsServer(mock_config)

        await server.start()

        # Verify skills were loaded
        assert server.repository.count() >= 1

    @pytest.mark.asyncio
    async def test_start_server_without_hot_reload(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test starting server with hot-reload disabled."""
        mock_config.hot_reload = False
        mock_config.skills_dir = valid_skill_folder.parent

        server = SkillsServer(mock_config)

        await server.start()

        # Watcher should not be created
        assert server.watcher is None

    @pytest.mark.asyncio
    async def test_stop_server(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test stopping the server."""
        mock_config.skills_dir = valid_skill_folder.parent

        server = SkillsServer(mock_config)

        # Mock watcher
        with patch("mcp_skills.server.SkillWatcher") as mock_watcher_class:
            mock_watcher = Mock()
            mock_watcher_class.return_value = mock_watcher

            await server.start()
            await server.stop()

            # Verify watcher was stopped
            mock_watcher.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_skills(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test reloading skills."""
        mock_config.skills_dir = valid_skill_folder.parent
        mock_config.hot_reload = False  # Disable to avoid threading issues in test

        server = SkillsServer(mock_config)
        await server.start()

        # Reload skills
        stats = await server.reload_skills()

        assert "loaded" in stats
        assert "failed" in stats
        assert "total" in stats
        assert stats["loaded"] >= 1


class TestServerResources:
    """Tests for MCP resource handling."""

    @pytest.mark.asyncio
    async def test_list_resources(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test listing available resources."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        resources = await server._list_resources()

        # Should have catalog + skill resources
        assert len(resources) >= 2

        # Check catalog resource
        catalog_resource = resources[0]
        assert str(catalog_resource.uri) == "skill://catalog"
        assert "Catalog" in catalog_resource.name

        # Check skill resource
        skill_resources = [r for r in resources if str(r.uri).startswith("skill://test-")]
        assert len(skill_resources) >= 1

    @pytest.mark.asyncio
    async def test_read_catalog_resource(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test reading the skill catalog resource."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        catalog = await server._read_resource("skill://catalog")

        assert "total_skills" in catalog
        assert "skills_directory" in catalog
        assert "hot_reload_enabled" in catalog
        assert "skills" in catalog

    @pytest.mark.asyncio
    async def test_read_skill_resource(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test reading a specific skill resource."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        content = await server._read_resource("skill://test-skill")

        assert content == sample_skill.content

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self, mock_config: ServerConfig) -> None:
        """Test reading a non-existent resource raises error."""
        server = SkillsServer(mock_config)

        with pytest.raises(ValueError) as exc_info:
            await server._read_resource("skill://nonexistent")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_read_invalid_uri(self, mock_config: ServerConfig) -> None:
        """Test reading resource with invalid URI."""
        server = SkillsServer(mock_config)

        with pytest.raises(ValueError) as exc_info:
            await server._read_resource("invalid://uri")

        assert "unknown" in str(exc_info.value).lower()


class TestServerCatalog:
    """Tests for catalog generation."""

    @pytest.mark.asyncio
    async def test_get_catalog_structure(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test catalog structure."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        catalog_json = await server._get_catalog()

        # Parse JSON
        import json
        catalog = json.loads(catalog_json)

        assert catalog["total_skills"] == 1
        assert catalog["hot_reload_enabled"] is True
        assert "folder_structure" in catalog
        assert "categories" in catalog
        assert len(catalog["skills"]) == 1

        skill_data = catalog["skills"][0]
        assert skill_data["name"] == "test-skill"
        assert skill_data["folder"] == "test-skill"
        assert skill_data["uri"] == "skill://test-skill"


class TestServerTools:
    """Tests for MCP tool execution."""

    @pytest.mark.asyncio
    async def test_list_tools(self, mock_config: ServerConfig) -> None:
        """Test listing available tools."""
        server = SkillsServer(mock_config)

        tools = await server._list_tools()

        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "search_skills" in tool_names
        assert "reload_skills" in tool_names
        assert "get_skill_info" in tool_names
        assert "list_skill_folders" in tool_names

    @pytest.mark.asyncio
    async def test_search_skills_tool(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test search_skills tool."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        result = await server._tool_search_skills({"query": "test"})

        assert len(result) == 1
        import json
        data = json.loads(result[0].text)
        assert data["found"] == 1
        assert len(data["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_skills_by_category(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test searching by category."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        result = await server._tool_search_skills({"category": "testing"})

        import json
        data = json.loads(result[0].text)
        assert data["found"] == 1

    @pytest.mark.asyncio
    async def test_reload_skills_tool(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test reload_skills tool."""
        mock_config.skills_dir = valid_skill_folder.parent
        mock_config.hot_reload = False  # Disable to avoid threading issues in test

        server = SkillsServer(mock_config)
        await server.start()

        result = await server._tool_reload_skills()

        assert len(result) == 1
        assert "skills loaded" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_skill_info_tool(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test get_skill_info tool."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        result = await server._tool_get_skill_info({"name": "test-skill"})

        assert len(result) == 1
        import json
        data = json.loads(result[0].text)
        assert data["name"] == "test-skill"
        assert data["description"] == "Test skill"

    @pytest.mark.asyncio
    async def test_get_skill_info_nonexistent(
        self, mock_config: ServerConfig
    ) -> None:
        """Test get_skill_info for non-existent skill."""
        server = SkillsServer(mock_config)

        result = await server._tool_get_skill_info({"name": "nonexistent"})

        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_list_skill_folders_tool(
        self, mock_config: ServerConfig, valid_skill_folder: Path
    ) -> None:
        """Test list_skill_folders tool."""
        mock_config.skills_dir = valid_skill_folder.parent
        mock_config.hot_reload = False  # Disable to avoid threading issues in test

        server = SkillsServer(mock_config)

        result = await server._tool_list_skill_folders()

        assert len(result) == 1
        import json
        data = json.loads(result[0].text)
        assert "total_folders" in data
        assert "folders" in data

    @pytest.mark.asyncio
    async def test_call_tool_dispatcher(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test the tool call dispatcher."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        # Test search_skills
        result = await server._call_tool("search_skills", {"query": "test"})
        assert len(result) == 1

        # Test unknown tool
        with pytest.raises(ValueError) as exc_info:
            await server._call_tool("unknown_tool", {})
        assert "unknown tool" in str(exc_info.value).lower()


class TestServerHotReload:
    """Tests for hot-reload callback."""

    @pytest.mark.asyncio
    async def test_on_skill_change_updates_skill(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test that skill changes trigger updates."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        # Mock parser to return updated skill
        updated_skill = Skill(
            name="test-skill",
            description="Updated description",
            content="Updated content",
            path=sample_skill.path,
            folder_path=sample_skill.folder_path,
        )

        with patch.object(server.parser, "parse", return_value=updated_skill):
            await server._on_skill_change(sample_skill.path)

        # Verify skill was updated
        skill = server.repository.get("test-skill")
        assert skill is not None
        assert skill.description == "Updated description"

    @pytest.mark.asyncio
    async def test_on_skill_change_removes_invalid(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test that invalid skills are removed."""
        server = SkillsServer(mock_config)
        server.repository.add(sample_skill)

        # Mock parser to return None (parse failure)
        with patch.object(server.parser, "parse", return_value=None):
            await server._on_skill_change(sample_skill.path)

        # Skill should be removed
        skill = server.repository.get("test-skill")
        assert skill is None

    @pytest.mark.asyncio
    async def test_on_skill_change_handles_errors(
        self, mock_config: ServerConfig, sample_skill: Skill
    ) -> None:
        """Test that errors during reload are handled gracefully."""
        server = SkillsServer(mock_config)

        # Mock parser to raise exception
        with patch.object(server.parser, "parse", side_effect=Exception("Parse error")):
            # Should not raise, just log error
            await server._on_skill_change(sample_skill.path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
