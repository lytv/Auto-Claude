"""
Skill Loader Module
===================

Dynamically discovers and loads skills from .claude/skills/ directory.

Features:
- Dynamic discovery (auto-scan directory)
- Lazy loading (Tier 1 summary + Tier 2 on-demand)
- Ignores folders starting with '_' (_config, _core, etc.)
- No external dependencies (uses regex for YAML frontmatter parsing)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SkillSummary:
    """Tier 1: Lightweight skill info for prompt injection."""

    id: str
    name: str
    description: str
    allowed_tools: list[str]
    path: Path


@dataclass
class SkillDetail:
    """Tier 2: Full skill content for on-demand loading."""

    id: str
    name: str
    description: str
    allowed_tools: list[str]
    content: str  # Full SKILL.md content
    triggers: dict  # Auto-invoke patterns
    path: Path


def _parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content using regex.
    
    This is a simple parser that extracts essential fields without
    requiring PyYAML as a dependency.

    Returns:
        (metadata_dict, remaining_content)
    """
    # Match YAML frontmatter between --- markers
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    frontmatter = match.group(1)
    remaining = match.group(2)
    
    metadata = {}
    
    # Parse name: value
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    if name_match:
        metadata["name"] = name_match.group(1).strip().strip('"\'')
    
    # Parse description: value
    desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if desc_match:
        metadata["description"] = desc_match.group(1).strip().strip('"\'')
    
    # Parse allowed-tools: [list] or multi-line list
    tools_match = re.search(r"^allowed-tools:\s*\[([^\]]+)\]", frontmatter, re.MULTILINE)
    if tools_match:
        # Inline list format: ["Read", "Write"]
        tools_str = tools_match.group(1)
        tools = [t.strip().strip('"\'') for t in tools_str.split(",")]
        metadata["allowed-tools"] = [t for t in tools if t]
    else:
        # Multi-line list format:
        # allowed-tools:
        #   - Read
        #   - Write
        tools_section = re.search(r"^allowed-tools:\s*\n((?:\s+-\s+.+\n?)+)", frontmatter, re.MULTILINE)
        if tools_section:
            tools = re.findall(r"^\s+-\s+[\"']?([^\"'\n]+)[\"']?", tools_section.group(1), re.MULTILINE)
            metadata["allowed-tools"] = [t.strip() for t in tools]
    
    return metadata, remaining


def discover_skills(project_dir: Path) -> list[SkillSummary]:
    """
    Scan .claude/skills/ and return available skills.

    - Ignores folders starting with '_' (_config, _core, etc.)
    - Only includes folders with SKILL.md
    - Returns empty list if no skills found

    Args:
        project_dir: Project root directory

    Returns:
        List of SkillSummary objects
    """
    skills_dir = project_dir / ".claude" / "skills"

    if not skills_dir.exists():
        return []

    skills = []

    for folder in skills_dir.iterdir():
        # Skip non-directories
        if not folder.is_dir():
            continue

        # Skip folders starting with '_'
        if folder.name.startswith("_"):
            continue

        # Check for SKILL.md
        skill_file = folder / "SKILL.md"
        if not skill_file.exists():
            continue

        # Parse skill metadata
        try:
            content = skill_file.read_text(encoding="utf-8")
            metadata, _ = _parse_yaml_frontmatter(content)

            skill = SkillSummary(
                id=folder.name,
                name=metadata.get("name", folder.name),
                description=metadata.get("description", "No description"),
                allowed_tools=metadata.get("allowed-tools", []),
                path=folder,
            )
            skills.append(skill)
        except Exception:
            # Skip skills that can't be parsed
            continue

    # Sort by name for consistent ordering
    return sorted(skills, key=lambda s: s.name)


def get_skill_content(skill_id: str, project_dir: Path) -> Optional[str]:
    """
    Load full SKILL.md content for Tier 2 on-demand loading.

    Args:
        skill_id: Skill ID (folder name)
        project_dir: Project root directory

    Returns:
        Full SKILL.md content, or None if not found
    """
    skill_file = project_dir / ".claude" / "skills" / skill_id / "SKILL.md"

    if not skill_file.exists():
        return None

    try:
        return skill_file.read_text(encoding="utf-8")
    except Exception:
        return None


def get_skill_detail(skill_id: str, project_dir: Path) -> Optional[SkillDetail]:
    """
    Load full skill details including parsed metadata.

    Args:
        skill_id: Skill ID (folder name)
        project_dir: Project root directory

    Returns:
        SkillDetail object, or None if not found
    """
    skill_folder = project_dir / ".claude" / "skills" / skill_id
    skill_file = skill_folder / "SKILL.md"

    if not skill_file.exists():
        return None

    try:
        content = skill_file.read_text(encoding="utf-8")
        metadata, remaining = _parse_yaml_frontmatter(content)

        return SkillDetail(
            id=skill_id,
            name=metadata.get("name", skill_id),
            description=metadata.get("description", "No description"),
            allowed_tools=metadata.get("allowed-tools", []),
            content=content,
            triggers=metadata.get("metadata", {}).get("triggers", {}),
            path=skill_folder,
        )
    except Exception:
        return None


def build_skill_inventory_prompt(skills: list[SkillSummary]) -> str:
    """
    Build Tier 1 skill inventory for system prompt injection.

    Args:
        skills: List of discovered skills

    Returns:
        Formatted string for system prompt (~500 tokens)
    """
    if not skills:
        return ""

    lines = [
        "\n# Available Skills",
        "You have access to the following skills. Use the `get_skill_details` tool to load full instructions when needed.\n",
    ]

    for skill in skills:
        lines.append(f"- **{skill.id}**: {skill.description}")

    lines.append(
        "\nTo use a skill, call: `get_skill_details(skill_id=\"<skill-id>\")`"
    )

    return "\n".join(lines)
