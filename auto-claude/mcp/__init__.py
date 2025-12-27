"""
Auto-Claude MCP Package
=======================

MCP server tools for Auto-Claude integration with Clawdis.
"""

from .tools import (
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

__all__ = [
    "list_specs",
    "get_spec_status",
    "get_qa_status",
    "review_build",
    "list_worktrees",
    "merge_preview",
    "run_build",
    "run_qa",
    "run_followup",
    "merge_build",
    "discard_build",
    "cleanup_worktrees",
]
