"""
Tests for the main CLI entry point.

These tests use mocking to test the main() and run() functions
without requiring actual server execution or MCP connections.

Tests cover:
- Configuration loading
- Logging setup
- Server initialization
- Signal handling
- MCP server execution
- Error handling
- Shutdown process
"""

import asyncio
import signal
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

from mcp_skills.__main__ import main, run
from mcp_skills.config import ServerConfig


class TestMainFunction:
    """Tests for the main() async function."""

    @pytest.mark.asyncio
    async def test_main_loads_config(self) -> None:
        """Test that main() loads configuration."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server context manager
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify config was loaded
            mock_config_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_configures_logging(self) -> None:
        """Test that main() configures logging."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify logging was configured
            mock_config.configure_logging.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_creates_server(self) -> None:
        """Test that main() creates SkillsServer instance."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify server was created
            mock_server_class.assert_called_once_with(mock_config)

    @pytest.mark.asyncio
    async def test_main_starts_server(self) -> None:
        """Test that main() starts the server."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify server was started
            mock_server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_runs_mcp_server(self) -> None:
        """Test that main() runs the MCP stdio server."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (AsyncMock(), AsyncMock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify MCP server was run
            mock_server.mcp_server.run.assert_called_once()
            call_args = mock_server.mcp_server.run.call_args[0]
            assert call_args[0] == mock_streams[0]  # read_stream
            assert call_args[1] == mock_streams[1]  # write_stream

    @pytest.mark.asyncio
    async def test_main_registers_signal_handlers(self) -> None:
        """Test that main() registers SIGINT and SIGTERM handlers."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ) as mock_signal:
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify signal handlers were registered
            assert mock_signal.call_count >= 2
            signal_calls = [call[0][0] for call in mock_signal.call_args_list]
            assert signal.SIGINT in signal_calls
            assert signal.SIGTERM in signal_calls

    @pytest.mark.asyncio
    async def test_main_stops_server_on_cleanup(self) -> None:
        """Test that main() stops server during cleanup."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify server was stopped
            mock_server.stop.assert_called_once()


class TestMainErrorHandling:
    """Tests for error handling in main()."""

    @pytest.mark.asyncio
    async def test_main_exits_on_config_error(self) -> None:
        """Test that main() exits on configuration error."""
        with patch(
            "mcp_skills.__main__.ServerConfig"
        ) as mock_config_class, pytest.raises(SystemExit):
            mock_config_class.side_effect = Exception("Config error")

            # Should exit with code 1
            await main()

    @pytest.mark.asyncio
    async def test_main_exits_on_server_creation_error(self) -> None:
        """Test that main() exits on server creation error."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, pytest.raises(SystemExit):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server_class.side_effect = Exception("Server creation error")

            # Should exit with code 1
            await main()

    @pytest.mark.asyncio
    async def test_main_exits_on_server_error(self) -> None:
        """Test that main() exits on server runtime error."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ), pytest.raises(
            SystemExit
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock(
                side_effect=Exception("Server runtime error")
            )
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Should exit with code 1
            await main()

    @pytest.mark.asyncio
    async def test_main_handles_keyboard_interrupt(self) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ):
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock(side_effect=KeyboardInterrupt())
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Should not raise, but still cleanup
            await main()

            # Verify server was still stopped
            mock_server.stop.assert_called_once()


class TestRunFunction:
    """Tests for the run() synchronous wrapper."""

    def test_run_executes_main(self) -> None:
        """Test that run() executes main()."""
        with patch("mcp_skills.__main__.asyncio.run") as mock_asyncio_run:
            run()

            # Verify asyncio.run was called once
            mock_asyncio_run.assert_called_once()
            # The argument should be a coroutine from main()
            args = mock_asyncio_run.call_args[0]
            assert len(args) == 1

    def test_run_handles_keyboard_interrupt(self) -> None:
        """Test that run() handles KeyboardInterrupt gracefully."""
        with patch(
            "mcp_skills.__main__.asyncio.run"
        ) as mock_asyncio_run, patch.object(sys, "exit") as mock_exit:
            mock_asyncio_run.side_effect = KeyboardInterrupt()

            # Should not raise or exit
            run()

            # Should not call sys.exit for keyboard interrupt
            mock_exit.assert_not_called()

    def test_run_exits_on_fatal_error(self) -> None:
        """Test that run() exits on fatal error."""
        with patch("mcp_skills.__main__.asyncio.run") as mock_asyncio_run, patch.object(
            sys, "exit"
        ) as mock_exit:
            mock_asyncio_run.side_effect = Exception("Fatal error")

            run()

            # Should exit with code 1
            mock_exit.assert_called_once_with(1)


class TestLoggingOutput:
    """Tests for logging output and banners."""

    @pytest.mark.asyncio
    async def test_main_displays_startup_banner(self) -> None:
        """Test that main() displays startup banner with folder structure."""
        with patch("mcp_skills.__main__.ServerConfig") as mock_config_class, patch(
            "mcp_skills.__main__.SkillsServer"
        ) as mock_server_class, patch(
            "mcp_skills.__main__.stdio_server"
        ) as mock_stdio, patch(
            "signal.signal"
        ), patch(
            "mcp_skills.__main__.logger"
        ) as mock_logger:
            # Setup mocks
            mock_config = Mock(spec=ServerConfig)
            mock_config.skills_dir = Path("/skills")
            mock_config.configure_logging = Mock()
            mock_config_class.return_value = mock_config

            mock_server = Mock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_server.mcp_server = Mock()
            mock_server.mcp_server.run = AsyncMock()
            mock_server.mcp_server.create_initialization_options = Mock(
                return_value={}
            )
            mock_server_class.return_value = mock_server

            # Mock stdio_server
            mock_streams = (Mock(), Mock())
            mock_stdio.return_value.__aenter__ = AsyncMock(return_value=mock_streams)
            mock_stdio.return_value.__aexit__ = AsyncMock(return_value=None)

            # Run main
            await main()

            # Verify startup banner was logged
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            banner_logged = any(
                "MCP Skills Server" in str(call) for call in info_calls
            )
            folder_structure_logged = any("SKILL.md" in str(call) for call in info_calls)

            assert banner_logged
            assert folder_structure_logged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
