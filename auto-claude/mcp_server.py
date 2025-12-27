#!/usr/bin/env python3
"""
Auto-Claude MCP Server
======================

MCP server for Auto-Claude integration with Clawdis via mcporter.

Usage:
    python mcp_server.py

Or via mcporter:
    mcporter list auto-claude --schema
    mcporter call auto-claude.list_specs
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
_PARENT_DIR = Path(__file__).parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

from mcp.tools import (
    list_specs,
    get_spec_status,
    get_qa_status,
    review_build,
    list_worktrees,
    merge_preview,
    run_build,
    run_qa,
    run_followup,
    merge_build,
    discard_build,
    cleanup_worktrees,
)

import json

# Create server instance
server = Server("auto-claude")


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

TOOLS = [
    Tool(
        name="list_specs",
        description="List all specs and their status",
        inputSchema={
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Project directory path (optional)"
                }
            }
        }
    ),
    Tool(
        name="get_spec_status",
        description="Get detailed status of a spec including phases and subtasks",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {
                    "type": "string",
                    "description": "Spec ID (e.g., '001' or '001-feature-name')"
                },
                "project_dir": {
                    "type": "string",
                    "description": "Project directory path (optional)"
                }
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="get_qa_status",
        description="Get QA validation status for a spec",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="review_build",
        description="Review what an existing build contains (files changed, commits)",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="list_worktrees",
        description="List all spec worktrees and their status",
        inputSchema={
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            }
        }
    ),
    Tool(
        name="merge_preview",
        description="Preview merge conflicts without actually merging",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="run_build",
        description="Start building a spec. Runs in background.",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID to build"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
                "model": {"type": "string", "description": "Model to use (optional)"},
                "max_iterations": {"type": "integer", "description": "Max iterations (optional)"},
                "mode": {"type": "string", "enum": ["isolated", "direct"], "description": "Workspace mode"},
                "auto_continue": {"type": "boolean", "description": "Auto-continue builds"},
                "skip_qa": {"type": "boolean", "description": "Skip QA after build"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="run_qa",
        description="Run QA validation loop on a spec",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="run_followup",
        description="Add follow-up tasks to a completed spec",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="merge_build",
        description="Merge completed build into project",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
                "no_commit": {"type": "boolean", "description": "Stage changes but don't commit"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="discard_build",
        description="Discard a build. Requires confirm=True for safety.",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "Spec ID"},
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
                "confirm": {"type": "boolean", "description": "Must be True to actually discard"}
            },
            "required": ["spec_id"]
        }
    ),
    Tool(
        name="cleanup_worktrees",
        description="Remove all spec worktrees and their branches",
        inputSchema={
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory (optional)"},
                "confirm": {"type": "boolean", "description": "Must be True to actually cleanup"}
            }
        }
    ),
]


@server.list_tools()
async def handle_list_tools():
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    
    # Map tool names to functions
    tool_map = {
        "list_specs": list_specs,
        "get_spec_status": get_spec_status,
        "get_qa_status": get_qa_status,
        "review_build": review_build,
        "list_worktrees": list_worktrees,
        "merge_preview": merge_preview,
        "run_build": run_build,
        "run_qa": run_qa,
        "run_followup": run_followup,
        "merge_build": merge_build,
        "discard_build": discard_build,
        "cleanup_worktrees": cleanup_worktrees,
    }
    
    if name not in tool_map:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    try:
        result = tool_map[name](**arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
