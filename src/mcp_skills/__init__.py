"""
MCP Skills Server - Dynamic Claude skill loading with hot-reload support.

This package provides a production-ready MCP server that dynamically loads
and exposes Claude skills from a mounted volume with hot-reloading capabilities.

**CRITICAL**: Each skill MUST be in its own dedicated folder within the skills directory.
The server will ONLY recognize skills that follow this structure:

    /skills/
    ├── skill-name-1/
    │   └── SKILL.md          ← Required
    ├── skill-name-2/
    │   ├── SKILL.md          ← Required
    │   └── examples/         ← Optional
    └── skill-name-3/
        └── SKILL.md

Invalid structures (will be ignored):
- SKILL.md files in the root directory
- Hidden folders (starting with '.')
- System folders (__pycache__, node_modules, .git, etc.)
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from mcp_skills.models.skill import Skill
from mcp_skills.storage.repository import SkillRepository

__all__ = ["Skill", "SkillRepository", "__version__"]
