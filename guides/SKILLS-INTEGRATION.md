# Skills Integration for Autonomous Agents

Enable Auto-Claude autonomous agents to dynamically discover and use skills from `.claude/skills/`.

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Discovery | **Dynamic (scan directory)** | Auto-adapts when skills added/removed |
| Loading | **Lazy (Two-Tier)** | Saves ~47k tokens per session |
| Execution | **Prompt Injection** | Simpler, leverages existing tools |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Session                         │
├─────────────────────────────────────────────────────────┤
│  System Prompt                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Tier 1: Skill Inventory (~500 tokens)           │    │
│  │ - skill-a: Description A                        │    │
│  │ - skill-b: Description B                        │    │
│  │ Use get_skill_details(id) to load full content  │    │
│  └─────────────────────────────────────────────────┘    │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ MCP Tool: get_skill_details(skill_id)           │    │
│  │ → Returns full SKILL.md content (~3k tokens)    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Proposed Changes

### Component: Skill Discovery

#### [NEW] [skill_loader.py](file:///Users/mac/tools/Auto-Claude/auto-claude/skills/skill_loader.py)

```python
def discover_skills(project_dir: Path) -> list[SkillSummary]:
    """
    Scan .claude/skills/ and return available skills.
    
    - Ignores folders starting with '_' (_config, _core, etc.)
    - Only includes folders with SKILL.md
    - Returns empty list if no skills found
    """
    
def get_skill_content(skill_id: str, project_dir: Path) -> str:
    """Read full SKILL.md content for Tier 2 loading."""
```

**Dynamic behavior:**
- 1 skill → returns `[SkillSummary(id="my-skill", ...)]`
- 16 skills → returns all 16
- 0 skills → returns `[]`

---

### Component: MCP Tool for Lazy Loading

#### [NEW] [skill_tool.py](file:///Users/mac/tools/Auto-Claude/auto-claude/skills/skill_tool.py)

```python
@mcp_tool(name="get_skill_details")
def get_skill_details(skill_id: str) -> str:
    """
    Load full skill instructions on demand.
    
    Args:
        skill_id: ID of the skill (folder name)
    
    Returns:
        Full SKILL.md content with instructions
    """
```

---

### Component: Client Integration

#### [MODIFY] [client.py](file:///Users/mac/tools/Auto-Claude/auto-claude/core/client.py)

Changes:
1. Call `discover_skills()` at startup
2. Build Tier 1 summary for system prompt
3. Register `get_skill_details` MCP tool

---

## Token Comparison

| Scenario | Old (Load All) | New (Lazy) | Savings |
|----------|----------------|------------|---------|
| 16 skills, use 0 | 48,000 | 500 | 99% |
| 16 skills, use 1 | 48,000 | 3,500 | 93% |
| 1 skill, use 1 | 3,000 | 3,500 | -17%* |

*Tiny overhead acceptable for flexibility

---

## Verification Plan

### Automated Tests

```bash
cd /Users/mac/tools/Auto-Claude
auto-claude/.venv/bin/pytest tests/test_skill_loader.py -v
```

**Test cases:**
- `test_discover_finds_single_skill` - 1 skill scenario
- `test_discover_finds_multiple_skills` - 16 skills scenario  
- `test_discover_returns_empty_when_no_skills` - 0 skills scenario
- `test_ignores_underscore_folders` - `_config` ignored
- `test_get_skill_content_returns_full_md` - Tier 2 loading

### Manual Verification

1. Remove all skills except one → verify only that skill appears
2. Add new skill folder → verify auto-discovered
3. Run agent → verify `get_skill_details` tool available
