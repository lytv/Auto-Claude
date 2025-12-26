#!/usr/bin/env python3
"""
Tests for Skill Loader Module
=============================

Verifies dynamic skill discovery and lazy loading functionality.
"""

import sys
from pathlib import Path

import pytest

# Add auto-claude directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "auto-claude"))

from skills import (
    TOOL_GET_SKILL_DETAILS,
    SkillSummary,
    build_skill_inventory_prompt,
    create_skill_tools,
    discover_skills,
    get_skill_content,
)


class TestSkillDiscovery:
    """Tests for dynamic skill discovery from .claude/skills/."""

    def test_discover_finds_skills_in_auto_claude_project(self):
        """Skills are discovered in Auto-Claude project with .claude/skills/."""
        project_dir = Path(__file__).parent.parent
        skills = discover_skills(project_dir)

        # Auto-Claude project has skills
        assert len(skills) >= 1, "Expected at least 1 skill in Auto-Claude project"

    def test_discover_returns_skill_summary_objects(self):
        """Discovered skills are SkillSummary objects."""
        project_dir = Path(__file__).parent.parent
        skills = discover_skills(project_dir)

        if skills:
            skill = skills[0]
            assert isinstance(skill, SkillSummary)
            assert hasattr(skill, "id")
            assert hasattr(skill, "name")
            assert hasattr(skill, "description")
            assert hasattr(skill, "allowed_tools")
            assert hasattr(skill, "path")

    def test_discover_ignores_underscore_folders(self):
        """Folders starting with '_' are ignored (e.g., _config, _core)."""
        project_dir = Path(__file__).parent.parent
        skills = discover_skills(project_dir)

        # Check no skill IDs start with underscore
        for skill in skills:
            assert not skill.id.startswith("_"), (
                f"Skill {skill.id} should be ignored (starts with _)"
            )

    def test_discover_returns_empty_for_project_without_skills(self, tmp_path):
        """Empty list returned when no .claude/skills/ exists."""
        skills = discover_skills(tmp_path)
        assert skills == []

    def test_discover_returns_empty_for_empty_skills_dir(self, tmp_path):
        """Empty list returned when .claude/skills/ has no valid skills."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        skills = discover_skills(tmp_path)
        assert skills == []

    def test_discover_requires_skill_md_file(self, tmp_path):
        """Skill folder without SKILL.md is ignored."""
        skills_dir = tmp_path / ".claude" / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        # No SKILL.md file

        skills = discover_skills(tmp_path)
        assert skills == []


class TestSkillContent:
    """Tests for Tier 2 on-demand skill content loading."""

    def test_get_skill_content_returns_full_md(self):
        """get_skill_content returns full SKILL.md content."""
        project_dir = Path(__file__).parent.parent
        skills = discover_skills(project_dir)

        if skills:
            content = get_skill_content(skills[0].id, project_dir)
            assert content is not None
            assert len(content) > 100  # Should have substantive content
            assert "---" in content  # Should have YAML frontmatter

    def test_get_skill_content_returns_none_for_missing_skill(self, tmp_path):
        """get_skill_content returns None for non-existent skill."""
        content = get_skill_content("nonexistent-skill", tmp_path)
        assert content is None


class TestSkillInventoryPrompt:
    """Tests for Tier 1 inventory prompt generation."""

    def test_build_inventory_prompt_empty_for_no_skills(self):
        """Empty string returned when no skills available."""
        prompt = build_skill_inventory_prompt([])
        assert prompt == ""

    def test_build_inventory_prompt_contains_skill_ids(self):
        """Inventory prompt contains skill IDs."""
        skills = [
            SkillSummary(
                id="test-skill",
                name="Test Skill",
                description="A test skill for testing",
                allowed_tools=["Read"],
                path=Path("/fake/path"),
            )
        ]
        prompt = build_skill_inventory_prompt(skills)

        assert "test-skill" in prompt
        assert "A test skill for testing" in prompt

    def test_build_inventory_prompt_mentions_get_skill_details(self):
        """Inventory prompt tells agent how to load full content."""
        skills = [
            SkillSummary(
                id="test-skill",
                name="Test Skill",
                description="Test",
                allowed_tools=[],
                path=Path("/fake"),
            )
        ]
        prompt = build_skill_inventory_prompt(skills)

        assert "get_skill_details" in prompt.lower()


class TestSkillTools:
    """Tests for MCP tool creation."""

    def test_tool_name_constant(self):
        """TOOL_GET_SKILL_DETAILS has correct format."""
        assert TOOL_GET_SKILL_DETAILS == "mcp__auto-claude__get_skill_details"

    def test_create_skill_tools_returns_list(self):
        """create_skill_tools returns a list of tool functions."""
        project_dir = Path(__file__).parent.parent
        tools = create_skill_tools(project_dir)

        assert isinstance(tools, list)
        assert len(tools) >= 1

    def test_skill_tool_is_callable(self):
        """Created skill tool is callable."""
        project_dir = Path(__file__).parent.parent
        tools = create_skill_tools(project_dir)

        if tools:
            tool = tools[0]
            assert callable(tool)


class TestYAMLParsing:
    """Tests for YAML frontmatter parsing."""

    def test_parses_valid_yaml_frontmatter(self, tmp_path):
        """Valid YAML frontmatter is parsed correctly."""
        skill_dir = tmp_path / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
allowed-tools:
  - Read
  - Write
---

# Test Skill Content
""")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].id == "test-skill"
        assert skills[0].name == "test-skill"
        assert skills[0].description == "A test skill"
        assert "Read" in skills[0].allowed_tools
        assert "Write" in skills[0].allowed_tools


def run_tests():
    """Run all tests when executed directly."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
