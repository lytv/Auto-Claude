# Graphiti Memory Integration Guide

## Overview
This document describes how Graphiti Memory is integrated into Auto-Claude and which features use it.

---

## Features Using Graphiti Memory

### 1. ✅ Build Agent (`agents/coder.py`)
**Type**: READ + WRITE

| Function | File | Line | Description |
|----------|------|------|-------------|
| Read Context | `coder.py` | 324-328 | `get_graphiti_context()` - Retrieves context from memory before each subtask |
| Save Session | `session.py` | 171-182 | `save_session_memory()` - Saves insights after each session with fallback |

**Flow**: When Build Agent runs a subtask → Fetches context from Graphiti → Appends to prompt → After session, saves discoveries back.

---

### 2. ✅ Insights Chat (`runners/insights_runner.py`)
**Type**: READ + WRITE (via MCP tools)

| Function | Line | Description |
|----------|------|-------------|
| MCP Tools | 222-226 | `mcp__graphiti-memory__search_nodes`, `search_facts`, `add_episode`, etc. |
| Auto-save | 316-332 | `save_session_insights()` - Auto-saves after each response |
| System Prompt | 109-128 | Instructions for AI to use memory tools |

**Flow**: User chats → AI can call `search_nodes` to find context → Response is auto-saved to Graphiti.

---

### 3. ✅ Roadmap Generator (`runners/roadmap/graph_integration.py`)
**Type**: READ ONLY

| Function | Line | Description |
|----------|------|-------------|
| Get Hints | 55-59 | `get_graph_hints()` - Retrieves insights from graph for roadmap generation |
| Cache | 32-41 | Results are cached in `graph_hints.json` |

**Flow**: When creating Roadmap → Queries Graphiti for "product roadmap features priorities" → Uses hints to generate better roadmap.

---

## Features NOT Using Graphiti

### ❌ Ideation Runner (`runners/ideation_runner.py`)
No references to `graphiti` in this file.

**Suggestion**: Could integrate to:
- Save brainstormed ideas
- Reference history of previous ideas

---

## Key Entry Points

| Module | Function | Purpose |
|--------|----------|---------|
| `integrations/graphiti/memory.py` | `get_graphiti_memory()` | Factory function for GraphitiMemory |
| `agents/memory_manager.py` | `get_graphiti_context()` | Get context for prompt |
| `agents/memory_manager.py` | `save_session_memory()` | Save session insights |
| `graphiti_providers.py` | `get_graph_hints()` | Query hints from graph |
| `graphiti_config.py` | `is_graphiti_enabled()` | Check enabled status |

---

## Configuration

### Required Environment Variables

```bash
# Enable Graphiti
GRAPHITI_ENABLED=true

# LLM & Embedder
GRAPHITI_LLM_PROVIDER=openai
GRAPHITI_EMBEDDER_PROVIDER=openai
OPENAI_API_KEY=sk-...

# FalkorDB Connection
GRAPHITI_FALKORDB_HOST=localhost
GRAPHITI_FALKORDB_PORT=6380
GRAPHITI_DATABASE=auto_claude_memory

# MCP Server URL (for Insights Chat)
GRAPHITI_MCP_URL=http://localhost:8000/sse
```

### UI Settings (for Insights Chat)
In Project Settings:
- Enable "Graphiti MCP"
- Set MCP URL to `http://localhost:8000/sse`

---

## Verification Commands

```bash
# Check if FalkorDB is running
docker ps | grep falkordb

# Count nodes in a graph
docker exec auto-claude-falkordb redis-cli GRAPH.QUERY <graph_name> "MATCH (n) RETURN count(n)"

# View entities
docker exec auto-claude-falkordb redis-cli GRAPH.QUERY <graph_name> "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 10"
```

---

## Troubleshooting

### Memory not saving
1. Check `GRAPHITI_ENABLED=true` in environment
2. Verify FalkorDB container is running
3. Check logs for connection errors

### Search returning empty
1. Verify fulltext index exists
2. Check for RediSearch syntax errors in logs
3. Try simpler search terms without special characters

### Insights Chat not using memory tools
1. Verify `GRAPHITI_MCP_URL` is set in UI Project Settings
2. Restart the application after changing settings
3. Check terminal logs for "Adding Graphiti tools" message
