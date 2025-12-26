"""
Skills Module
=============

Dynamically discovers and loads skills from .claude/skills/ directory.

Two-Tier Loading System:
- Tier 1: Skill inventory (ID + description) injected into system prompt
- Tier 2: Full skill content loaded on-demand via MCP tool

Usage:
    from skills import discover_skills, build_skill_inventory_prompt
    from skills import create_skill_tools, TOOL_GET_SKILL_DETAILS

    # Tier 1: Build inventory for system prompt
    skills = discover_skills(project_dir)
    inventory_prompt = build_skill_inventory_prompt(skills)

    # Tier 2: Create MCP tools for on-demand loading
    skill_tools = create_skill_tools(project_dir)
"""

from .skill_loader import (
    SkillDetail,
    SkillSummary,
    build_skill_inventory_prompt,
    discover_skills,
    get_skill_content,
    get_skill_detail,
)
from .skill_tool import (
    TOOL_GET_SKILL_DETAILS,
    create_skill_tool,
    create_skill_tools,
)

__all__ = [
    # Data classes
    "SkillSummary",
    "SkillDetail",
    # Discovery functions
    "discover_skills",
    "get_skill_content",
    "get_skill_detail",
    "build_skill_inventory_prompt",
    # MCP tools
    "TOOL_GET_SKILL_DETAILS",
    "create_skill_tool",
    "create_skill_tools",
]
