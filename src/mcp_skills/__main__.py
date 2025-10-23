"""
CLI entry point for MCP Skills Server.

This module provides the main entry point for running the MCP server.
It handles:
- Configuration loading from environment
- Logging setup with folder context
- Server initialization and lifecycle
- Graceful shutdown on signals
- MCP stdio server execution
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from mcp.server.stdio import stdio_server

from mcp_skills.config import ServerConfig
from mcp_skills.server import SkillsServer

logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main entry point for the MCP Skills Server.

    This function:
    1. Loads configuration from environment variables
    2. Sets up logging with folder structure context
    3. Creates and starts the skills server
    4. Handles graceful shutdown on SIGINT/SIGTERM
    5. Runs the MCP stdio server

    The server expects skills to be organized in folders:
        /skills/
        ├── skill-one/
        │   └── SKILL.md
        ├── skill-two/
        │   └── SKILL.md
        └── skill-three/
            └── SKILL.md

    Environment Variables:
        MCP_SKILLS_DIR: Skills directory path (default: /skills)
        MCP_SKILLS_HOT_RELOAD: Enable hot-reload (default: true)
        MCP_SKILLS_LOG_LEVEL: Log level (default: INFO)
        MCP_SKILLS_DEBOUNCE_DELAY: Debounce delay (default: 0.5)
    """
    # Load configuration
    try:
        config = ServerConfig()
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Configure logging
    config.configure_logging()

    # Display startup banner
    logger.info("=" * 70)
    logger.info("MCP Skills Server - Dynamic Claude Skill Loading")
    logger.info("=" * 70)
    logger.info("")
    logger.info("IMPORTANT: Each skill MUST be in its own dedicated folder:")
    logger.info("")
    logger.info(f"  {config.skills_dir}/")
    logger.info("  ├── skill-one/")
    logger.info("  │   └── SKILL.md      ← Required")
    logger.info("  ├── skill-two/")
    logger.info("  │   ├── SKILL.md      ← Required")
    logger.info("  │   └── examples/     ← Optional")
    logger.info("  └── skill-three/")
    logger.info("      └── SKILL.md")
    logger.info("")
    logger.info("Invalid structures (will be ignored):")
    logger.info("  ✗ SKILL.md in root directory")
    logger.info("  ✗ Hidden folders (starting with '.')")
    logger.info("  ✗ System folders (__pycache__, node_modules, etc.)")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")

    # Create server instance
    try:
        server = SkillsServer(config)
    except Exception as e:
        logger.error(f"Failed to create server: {e}")
        sys.exit(1)

    # Setup shutdown handler
    shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame: any) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start the server
        await server.start()

        # Run the MCP stdio server
        logger.info("Starting MCP stdio server...")
        logger.info("Server is ready to accept connections")

        async with stdio_server() as (read_stream, write_stream):
            await server.mcp_server.run(
                read_stream,
                write_stream,
                server.mcp_server.create_initialization_options(),
            )

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("Shutting down server...")
        try:
            await server.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        logger.info("Server stopped")
        logger.info("=" * 70)


def run() -> None:
    """
    Synchronous entry point for the CLI.

    This is the function called by the 'mcp-skills' command.

    Example:
        $ mcp-skills
        $ MCP_SKILLS_DIR=/my/skills mcp-skills
        $ MCP_SKILLS_LOG_LEVEL=DEBUG mcp-skills
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
