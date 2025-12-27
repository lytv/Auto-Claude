"""
Auto-Claude MCP Tools
=====================

Tool implementations for the MCP server.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

# Add parent directory to path for imports
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))


def _get_project_dir(project_dir: Optional[str] = None) -> Path:
    """Get the project directory, defaulting to AUTO_CLAUDE_PROJECT_DIR or cwd."""
    if project_dir:
        return Path(project_dir)
    env_dir = os.environ.get("AUTO_CLAUDE_PROJECT_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.cwd()


def _get_specs_dir(project_dir: Path) -> Path:
    """Get the specs directory for a project."""
    return project_dir / ".auto-claude" / "specs"


def _find_spec(project_dir: Path, spec_id: str) -> Optional[Path]:
    """Find a spec directory by ID (e.g., '001' or '001-feature-name')."""
    specs_dir = _get_specs_dir(project_dir)
    if not specs_dir.exists():
        return None
    
    for spec_dir in specs_dir.iterdir():
        if spec_dir.is_dir():
            if spec_dir.name == spec_id or spec_dir.name.startswith(f"{spec_id}-"):
                return spec_dir
    return None


def _load_implementation_plan(spec_dir: Path) -> Optional[dict]:
    """Load the implementation plan JSON for a spec."""
    plan_file = spec_dir / "implementation_plan.json"
    if plan_file.exists():
        try:
            return json.loads(plan_file.read_text())
        except json.JSONDecodeError:
            return None
    return None


def _get_subtask_counts(plan: dict) -> dict:
    """Count subtasks by status from implementation plan."""
    counts = {"completed": 0, "in_progress": 0, "pending": 0, "stuck": 0, "total": 0}
    
    for phase in plan.get("phases", []):
        for subtask in phase.get("subtasks", []):
            status = subtask.get("status", "pending")
            counts["total"] += 1
            if status == "complete":
                counts["completed"] += 1
            elif status == "in_progress":
                counts["in_progress"] += 1
            elif status == "stuck":
                counts["stuck"] += 1
            else:
                counts["pending"] += 1
    
    return counts


def _get_spec_overall_status(spec_dir: Path, plan: Optional[dict]) -> str:
    """Determine overall status of a spec."""
    if plan is None:
        return "pending"
    
    counts = _get_subtask_counts(plan)
    
    if counts["total"] == 0:
        return "pending"
    if counts["completed"] == counts["total"]:
        # Check QA status
        qa_report = spec_dir / "qa_report.md"
        if qa_report.exists():
            return "qa_complete"
        return "complete"
    if counts["in_progress"] > 0:
        return "in_progress"
    if counts["stuck"] > 0:
        return "stuck"
    return "pending"


# ============================================================================
# QUERY TOOLS
# ============================================================================

def list_specs(project_dir: Optional[str] = None) -> dict:
    """
    List all specs and their status.
    
    Args:
        project_dir: Project directory path (optional, defaults to cwd)
    
    Returns:
        Dictionary with specs list and summary counts
    """
    proj_dir = _get_project_dir(project_dir)
    specs_dir = _get_specs_dir(proj_dir)
    
    result = {
        "specs": [],
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "complete": 0,
        "project_dir": str(proj_dir)
    }
    
    if not specs_dir.exists():
        return result
    
    for spec_dir in sorted(specs_dir.iterdir()):
        if not spec_dir.is_dir():
            continue
        
        plan = _load_implementation_plan(spec_dir)
        status = _get_spec_overall_status(spec_dir, plan)
        counts = _get_subtask_counts(plan) if plan else {"completed": 0, "total": 0}
        
        # Check for worktree
        worktree_dir = proj_dir / ".auto-claude-worktrees" / spec_dir.name
        has_worktree = worktree_dir.exists()
        
        spec_info = {
            "id": spec_dir.name,
            "status": status,
            "subtasks": {
                "completed": counts["completed"],
                "total": counts["total"]
            },
            "worktree": has_worktree
        }
        
        result["specs"].append(spec_info)
        result["total"] += 1
        
        if status == "in_progress":
            result["in_progress"] += 1
        elif status in ["complete", "qa_complete"]:
            result["complete"] += 1
        else:
            result["pending"] += 1
    
    return result


def get_spec_status(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Get detailed status of a spec including phases and subtasks.
    
    Args:
        spec_id: Spec ID (e.g., '001' or '001-feature-name')
        project_dir: Project directory path (optional)
    
    Returns:
        Detailed spec status dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "found": False}
    
    plan = _load_implementation_plan(spec_dir)
    status = _get_spec_overall_status(spec_dir, plan)
    
    # Load review state
    review_file = spec_dir / "review_state.json"
    approved = False
    approved_by = None
    if review_file.exists():
        try:
            review_state = json.loads(review_file.read_text())
            approved = review_state.get("approved", False)
            approved_by = review_state.get("approved_by")
        except json.JSONDecodeError:
            pass
    
    # Get phases info
    phases = []
    current_subtask = None
    
    if plan:
        for phase in plan.get("phases", []):
            phase_subtasks = phase.get("subtasks", [])
            phase_completed = sum(1 for s in phase_subtasks if s.get("status") == "complete")
            phase_status = "complete" if phase_completed == len(phase_subtasks) else "in_progress" if phase_completed > 0 else "pending"
            
            phases.append({
                "name": phase.get("name", "Unknown"),
                "status": phase_status,
                "subtasks": len(phase_subtasks),
                "completed": phase_completed
            })
            
            # Find current subtask
            for subtask in phase_subtasks:
                if subtask.get("status") == "in_progress":
                    current_subtask = {
                        "id": subtask.get("id"),
                        "description": subtask.get("description"),
                        "attempts": subtask.get("attempts", 1)
                    }
                    break
    
    counts = _get_subtask_counts(plan) if plan else {"completed": 0, "in_progress": 0, "pending": 0, "stuck": 0, "total": 0}
    
    # Check worktree
    worktree_dir = proj_dir / ".auto-claude-worktrees" / spec_dir.name
    
    return {
        "id": spec_dir.name,
        "found": True,
        "status": status,
        "approved": approved,
        "approved_by": approved_by,
        "phases": phases,
        "subtasks": counts,
        "current_subtask": current_subtask,
        "worktree_path": str(worktree_dir) if worktree_dir.exists() else None
    }


def get_qa_status(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Get QA validation status for a spec.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
    
    Returns:
        QA status dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "found": False}
    
    qa_report = spec_dir / "qa_report.md"
    qa_state = spec_dir / "qa_state.json"
    
    result = {
        "spec_id": spec_dir.name,
        "found": True,
        "qa_run": False,
        "passed": False,
        "issues": [],
        "last_run": None
    }
    
    if qa_state.exists():
        try:
            state = json.loads(qa_state.read_text())
            result["qa_run"] = True
            result["passed"] = state.get("passed", False)
            result["issues"] = state.get("issues", [])
            result["last_run"] = state.get("last_run")
        except json.JSONDecodeError:
            pass
    elif qa_report.exists():
        result["qa_run"] = True
        # Parse markdown for pass/fail indicators
        content = qa_report.read_text()
        result["passed"] = "✅" in content or "PASSED" in content.upper()
        result["last_run"] = datetime.fromtimestamp(qa_report.stat().st_mtime).isoformat()
    
    return result


def review_build(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Review what an existing build contains (files changed, commits).
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
    
    Returns:
        Build review dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "found": False}
    
    worktree_dir = proj_dir / ".auto-claude-worktrees" / spec_dir.name
    
    result = {
        "spec_id": spec_dir.name,
        "found": True,
        "has_worktree": worktree_dir.exists(),
        "files_changed": [],
        "commits": []
    }
    
    if not worktree_dir.exists():
        return result
    
    # Get changed files
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5..HEAD"],
            cwd=worktree_dir,
            capture_output=True,
            text=True
        )
        if diff_result.returncode == 0:
            result["files_changed"] = [f for f in diff_result.stdout.strip().split("\n") if f]
    except Exception:
        pass
    
    # Get recent commits
    try:
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=worktree_dir,
            capture_output=True,
            text=True
        )
        if log_result.returncode == 0:
            result["commits"] = [c for c in log_result.stdout.strip().split("\n") if c]
    except Exception:
        pass
    
    return result


def list_worktrees(project_dir: Optional[str] = None) -> dict:
    """
    List all spec worktrees and their status.
    
    Args:
        project_dir: Project directory path (optional)
    
    Returns:
        Worktrees list dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    worktrees_dir = proj_dir / ".auto-claude-worktrees"
    
    result = {
        "worktrees": [],
        "total": 0,
        "project_dir": str(proj_dir)
    }
    
    if not worktrees_dir.exists():
        return result
    
    for wt_dir in sorted(worktrees_dir.iterdir()):
        if not wt_dir.is_dir():
            continue
        
        # Get git branch
        branch = None
        try:
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=wt_dir,
                capture_output=True,
                text=True
            )
            if branch_result.returncode == 0:
                branch = branch_result.stdout.strip()
        except Exception:
            pass
        
        result["worktrees"].append({
            "spec_id": wt_dir.name,
            "path": str(wt_dir),
            "branch": branch
        })
        result["total"] += 1
    
    return result


def merge_preview(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Preview merge conflicts without actually merging.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
    
    Returns:
        Merge preview dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "found": False}
    
    worktree_dir = proj_dir / ".auto-claude-worktrees" / spec_dir.name
    
    if not worktree_dir.exists():
        return {
            "spec_id": spec_dir.name,
            "found": True,
            "has_worktree": False,
            "can_merge": False,
            "message": "No worktree found for this spec"
        }
    
    # Try a dry-run merge
    result = {
        "spec_id": spec_dir.name,
        "found": True,
        "has_worktree": True,
        "can_merge": True,
        "conflicts": [],
        "files_to_merge": []
    }
    
    try:
        # Get the branch name
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=worktree_dir,
            capture_output=True,
            text=True
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
        
        if branch:
            # Check for merge conflicts
            merge_result = subprocess.run(
                ["git", "merge", "--no-commit", "--no-ff", "main", "--dry-run"],
                cwd=worktree_dir,
                capture_output=True,
                text=True
            )
            
            if merge_result.returncode != 0:
                result["can_merge"] = False
                result["conflicts"] = merge_result.stderr.strip().split("\n")
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ============================================================================
# ACTION TOOLS
# ============================================================================

def run_build(
    spec_id: str,
    project_dir: Optional[str] = None,
    model: Optional[str] = None,
    max_iterations: Optional[int] = None,
    mode: str = "isolated",
    auto_continue: bool = True,
    skip_qa: bool = False
) -> dict:
    """
    Start building a spec. Runs in background.
    
    Args:
        spec_id: Spec ID to build
        project_dir: Project directory path (optional)
        model: Model to use (optional)
        max_iterations: Max iterations (optional)
        mode: 'isolated' or 'direct'
        auto_continue: Auto-continue builds
        skip_qa: Skip QA after build
    
    Returns:
        Build start status dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "status": "error"}
    
    # Build command
    cmd = [
        sys.executable,
        str(_PARENT_DIR / "run.py"),
        "--spec", spec_dir.name,
        "--project-dir", str(proj_dir),
        "--auto-continue" if auto_continue else "",
    ]
    
    if mode == "isolated":
        cmd.append("--isolated")
    elif mode == "direct":
        cmd.append("--direct")
    
    if model:
        cmd.extend(["--model", model])
    
    if max_iterations:
        cmd.extend(["--max-iterations", str(max_iterations)])
    
    if skip_qa:
        cmd.append("--skip-qa")
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    try:
        # Start in background
        process = subprocess.Popen(
            cmd,
            cwd=proj_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return {
            "status": "started",
            "spec_id": spec_dir.name,
            "pid": process.pid,
            "mode": mode,
            "message": f"Build started for {spec_dir.name}. Use get_spec_status to monitor."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def run_qa(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Run QA validation loop on a spec.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
    
    Returns:
        QA start status dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "status": "error"}
    
    cmd = [
        sys.executable,
        str(_PARENT_DIR / "run.py"),
        "--spec", spec_dir.name,
        "--project-dir", str(proj_dir),
        "--qa"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=proj_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return {
            "status": "started",
            "spec_id": spec_dir.name,
            "pid": process.pid,
            "message": f"QA validation started for {spec_dir.name}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def run_followup(spec_id: str, project_dir: Optional[str] = None) -> dict:
    """
    Add follow-up tasks to a completed spec.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
    
    Returns:
        Followup start status dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "status": "error"}
    
    cmd = [
        sys.executable,
        str(_PARENT_DIR / "run.py"),
        "--spec", spec_dir.name,
        "--project-dir", str(proj_dir),
        "--followup"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=proj_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return {
            "status": "started",
            "spec_id": spec_dir.name,
            "pid": process.pid,
            "message": f"Followup planner started for {spec_dir.name}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def merge_build(
    spec_id: str,
    project_dir: Optional[str] = None,
    no_commit: bool = False
) -> dict:
    """
    Merge completed build into project.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
        no_commit: Stage changes but don't commit
    
    Returns:
        Merge result dictionary
    """
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "status": "error"}
    
    cmd = [
        sys.executable,
        str(_PARENT_DIR / "run.py"),
        "--spec", spec_dir.name,
        "--project-dir", str(proj_dir),
        "--merge"
    ]
    
    if no_commit:
        cmd.append("--no-commit")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=proj_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "spec_id": spec_dir.name,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Merge timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def discard_build(
    spec_id: str,
    project_dir: Optional[str] = None,
    confirm: bool = False
) -> dict:
    """
    Discard a build. Requires confirm=True for safety.
    
    Args:
        spec_id: Spec ID
        project_dir: Project directory path (optional)
        confirm: Must be True to actually discard
    
    Returns:
        Discard result dictionary
    """
    if not confirm:
        return {
            "status": "blocked",
            "message": "Set confirm=True to actually discard the build. This action is irreversible."
        }
    
    proj_dir = _get_project_dir(project_dir)
    spec_dir = _find_spec(proj_dir, spec_id)
    
    if not spec_dir:
        return {"error": f"Spec '{spec_id}' not found", "status": "error"}
    
    worktree_dir = proj_dir / ".auto-claude-worktrees" / spec_dir.name
    
    if not worktree_dir.exists():
        return {
            "status": "error",
            "message": "No worktree found to discard"
        }
    
    try:
        # Remove worktree
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_dir)],
            cwd=proj_dir,
            capture_output=True
        )
        
        # Delete branch
        branch_name = f"auto-claude/{spec_dir.name}"
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            cwd=proj_dir,
            capture_output=True
        )
        
        return {
            "status": "success",
            "spec_id": spec_dir.name,
            "message": f"Build for {spec_dir.name} has been discarded"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def cleanup_worktrees(project_dir: Optional[str] = None, confirm: bool = False) -> dict:
    """
    Remove all spec worktrees and their branches.
    
    Args:
        project_dir: Project directory path (optional)
        confirm: Must be True to actually cleanup
    
    Returns:
        Cleanup result dictionary
    """
    if not confirm:
        return {
            "status": "blocked",
            "message": "Set confirm=True to cleanup all worktrees. This action is irreversible."
        }
    
    proj_dir = _get_project_dir(project_dir)
    worktrees_dir = proj_dir / ".auto-claude-worktrees"
    
    if not worktrees_dir.exists():
        return {"status": "success", "message": "No worktrees to cleanup", "removed": 0}
    
    removed = []
    errors = []
    
    for wt_dir in worktrees_dir.iterdir():
        if not wt_dir.is_dir():
            continue
        
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_dir)],
                cwd=proj_dir,
                capture_output=True
            )
            removed.append(wt_dir.name)
        except Exception as e:
            errors.append({"worktree": wt_dir.name, "error": str(e)})
    
    return {
        "status": "success" if not errors else "partial",
        "removed": removed,
        "removed_count": len(removed),
        "errors": errors if errors else None
    }
