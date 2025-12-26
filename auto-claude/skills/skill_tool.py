"""
Skill MCP Tool
==============

MCP tool for on-demand skill loading (Tier 2).
Allows agents to load full skill instructions when needed.
"""

from pathlib import Path
from typing import Any

try:
    from claude_agent_sdk import tool

    SDK_TOOLS_AVAILABLE = True
except ImportError:
    SDK_TOOLS_AVAILABLE = False
    tool = None

from .skill_loader import get_skill_content

# Tool name constant
TOOL_GET_SKILL_DETAILS = "mcp__auto-claude__get_skill_details"


def create_skill_tool(project_dir: Path):
    """
    Create the get_skill_details MCP tool function.

    Args:
        project_dir: Project root directory

    Returns:
        Tool function for MCP server registration
    """
    if not SDK_TOOLS_AVAILABLE:
        return None

    @tool(
        "get_skill_details",
        "Load full skill instructions on demand. Use this when you need detailed instructions for a specific skill from your skill inventory.",
        {
            "skill_id": {
                "type": "string",
                "description": "ID of the skill (folder name in .claude/skills/)",
                "required": True,
            }
        },
    )
    async def get_skill_details(args: dict[str, Any]) -> dict[str, Any]:
        """Load full skill instructions on demand."""
        skill_id = args.get("skill_id", "")
        
        if not skill_id:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: skill_id is required. Check available skills in your inventory.",
                    }
                ]
            }

        content = get_skill_content(skill_id, project_dir)

        if content is None:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Skill '{skill_id}' not found. Check available skills in your inventory.",
                    }
                ]
            }

        return {"content": [{"type": "text", "text": content}]}

    return get_skill_details


def create_skill_tools(project_dir: Path) -> list:
    """
    Create all skill-related MCP tools.

    Args:
        project_dir: Project root directory

    Returns:
        List of tool functions for MCP server registration
    """
    if not SDK_TOOLS_AVAILABLE:
        return []

    tools = []
    skill_tool = create_skill_tool(project_dir)
    if skill_tool:
        tools.append(skill_tool)
    
    return tools
