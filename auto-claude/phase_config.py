"""
Phase Configuration Module
===========================

Handles model and thinking level configuration for different execution phases.
Reads configuration from task_metadata.json and provides resolved model IDs.
"""

import json
from pathlib import Path
from typing import Literal, TypedDict

import os
from dotenv import load_dotenv

# Load .env file from auto-claude root directory
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Default model IDs for shorthands
DEFAULT_MODEL_IDS: dict[str, str] = {
    "opus": "claude-opus-4-5-20251101",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
}

def get_model_id_map() -> dict[str, str]:
    """Get the model ID map, respecting environment overrides."""
    primary_model = os.environ.get("AUTO_BUILD_MODEL") or os.environ.get("ANTHROPIC_MODEL")
    fast_model = os.environ.get("ANTHROPIC_SMALL_FAST_MODEL") or primary_model
    
    mapping = DEFAULT_MODEL_IDS.copy()
    
    # Catch-all for common Claude IDs to redirect to Kimi/Gemini
    common_ids = [
        "claude-3-5-sonnet-latest", "claude-3-5-sonnet-20241022", "claude-sonnet-4-5-latest", "claude-sonnet-4-5-20250929",
        "claude-3-5-haiku-latest", "claude-3-5-haiku-20241022", "claude-haiku-4-5-latest", "claude-haiku-4-5-20251001",
        "claude-3-opus-latest", "claude-3-opus-20240229", "claude-opus-4-5-latest", "claude-opus-4-5-20251101",
        "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    ]
    
    if primary_model:
        mapping["sonnet"] = primary_model
        mapping["opus"] = primary_model
        for cid in common_ids:
            if "haiku" not in cid:
                mapping[cid] = primary_model
                
    if fast_model:
        mapping["haiku"] = fast_model
        for cid in common_ids:
            if "haiku" in cid:
                mapping[cid] = fast_model
                
    return mapping

# For backward compatibility with modules that import MODEL_ID_MAP directly
MODEL_ID_MAP = get_model_id_map()

# Thinking level to budget tokens mapping (None = no extended thinking)
# Values must match auto-claude-ui/src/shared/constants/models.ts THINKING_BUDGET_MAP
THINKING_BUDGET_MAP: dict[str, int | None] = {
    "none": None,
    "low": 1024,
    "medium": 4096,  # Moderate analysis
    "high": 16384,  # Deep thinking for QA review
    "ultrathink": 65536,  # Maximum reasoning depth
}

# Spec runner phase-specific thinking levels
# Heavy phases use ultrathink for deep analysis
# Light phases use medium after compaction
SPEC_PHASE_THINKING_LEVELS: dict[str, str] = {
    # Heavy phases - ultrathink (discovery, spec creation, self-critique)
    "discovery": "ultrathink",
    "spec_writing": "ultrathink",
    "self_critique": "ultrathink",
    # Light phases - medium (after first invocation with compaction)
    "requirements": "medium",
    "research": "medium",
    "context": "medium",
    "planning": "medium",
    "validation": "medium",
    "quick_spec": "medium",
    "historical_context": "medium",
    "complexity_assessment": "medium",
}

# Default phase configuration (matches UI defaults)
DEFAULT_PHASE_MODELS: dict[str, str] = {
    "spec": "sonnet",
    "planning": "opus",
    "coding": "sonnet",
    "qa": "sonnet",
}

DEFAULT_PHASE_THINKING: dict[str, str] = {
    "spec": "medium",
    "planning": "high",
    "coding": "medium",
    "qa": "high",
}


class PhaseModelConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class PhaseThinkingConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class TaskMetadataConfig(TypedDict, total=False):
    """Structure of model-related fields in task_metadata.json"""

    isAutoProfile: bool
    phaseModels: PhaseModelConfig
    phaseThinking: PhaseThinkingConfig
    model: str
    thinkingLevel: str


Phase = Literal["spec", "planning", "coding", "qa"]


def resolve_model_id(model_id: str) -> str:
    """Resolve a model ID or shorthand to the preferred model."""
    if not model_id:
        return ""
        
    # Always refresh mapping from environment
    mapping = get_model_id_map()
    
    # Check if this ID or shorthand should be redirected
    resolved = model_id
    if model_id.lower() in mapping:
        resolved = mapping[model_id.lower()]
    elif "/" not in model_id:
        # It's a shorthand not in our mapping, try to use it as is or default
        resolved = model_id

    # Debug: log every resolution to stderr to catch leaks
    if resolved != model_id:
        import sys
        print(f" [DEBUG] Redirected model: {model_id} -> {resolved}", file=sys.stderr)
        
    return resolved


def get_thinking_budget(thinking_level: str) -> int | None:
    """
    Get the thinking budget for a thinking level.

    Args:
        thinking_level: Thinking level (none, low, medium, high, ultrathink)

    Returns:
        Token budget or None for no extended thinking
    """
    import logging

    if thinking_level not in THINKING_BUDGET_MAP:
        valid_levels = ", ".join(THINKING_BUDGET_MAP.keys())
        logging.warning(
            f"Invalid thinking_level '{thinking_level}'. Valid values: {valid_levels}. "
            f"Defaulting to 'medium'."
        )
        return THINKING_BUDGET_MAP["medium"]

    return THINKING_BUDGET_MAP[thinking_level]


def load_task_metadata(spec_dir: Path) -> TaskMetadataConfig | None:
    """
    Load task_metadata.json from the spec directory.

    Args:
        spec_dir: Path to the spec directory

    Returns:
        Parsed task metadata or None if not found
    """
    metadata_path = spec_dir / "task_metadata.json"
    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_phase_model(
    spec_dir: Path,
    phase: Phase,
    cli_model: str | None = None,
) -> str:
    """
    Get the resolved model ID for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. Phase-specific config from task_metadata.json (if auto profile)
    3. Single model from task_metadata.json (if not auto profile)
    4. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_model: Model from CLI argument (optional)

    Returns:
        Resolved full model ID
    """
    # PRE-EMPTIVE ENV OVERRIDE (Thorough / Triet de fix)
    # This ensures that if the environment says to use Kimi, we use Kimi,
    # regardless of what the UI or CLI requested.
    import os
    env_model = os.environ.get("AUTO_BUILD_MODEL") or os.environ.get("ANTHROPIC_MODEL")
    if env_model:
        return resolve_model_id(env_model)

    # CLI argument takes precedence if no global env override
    if cli_model:
        return resolve_model_id(cli_model)

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseModels"):
            phase_models = metadata["phaseModels"]
            model = phase_models.get(phase, DEFAULT_PHASE_MODELS[phase])
            return resolve_model_id(model)

        # Non-auto profile: use single model
        if metadata.get("model"):
            return resolve_model_id(metadata["model"])

    # Fall back to default phase configuration
    return resolve_model_id(DEFAULT_PHASE_MODELS[phase])


def get_phase_thinking(
    spec_dir: Path,
    phase: Phase,
    cli_thinking: str | None = None,
) -> str:
    """
    Get the thinking level for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. Phase-specific config from task_metadata.json (if auto profile)
    3. Single thinking level from task_metadata.json (if not auto profile)
    4. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Thinking level string
    """
    # CLI argument takes precedence
    if cli_thinking:
        return cli_thinking

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseThinking"):
            phase_thinking = metadata["phaseThinking"]
            return phase_thinking.get(phase, DEFAULT_PHASE_THINKING[phase])

        # Non-auto profile: use single thinking level
        if metadata.get("thinkingLevel"):
            return metadata["thinkingLevel"]

    # Fall back to default phase configuration
    return DEFAULT_PHASE_THINKING[phase]


def get_phase_thinking_budget(
    spec_dir: Path,
    phase: Phase,
    cli_thinking: str | None = None,
) -> int | None:
    """
    Get the thinking budget tokens for a specific execution phase.

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Token budget or None for no extended thinking
    """
    thinking_level = get_phase_thinking(spec_dir, phase, cli_thinking)
    return get_thinking_budget(thinking_level)


def get_phase_config(
    spec_dir: Path,
    phase: Phase,
    cli_model: str | None = None,
    cli_thinking: str | None = None,
) -> tuple[str, str, int | None]:
    """
    Get the full configuration for a specific execution phase.

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_model: Model from CLI argument (optional)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Tuple of (model_id, thinking_level, thinking_budget)
    """
    model_id = get_phase_model(spec_dir, phase, cli_model)
    thinking_level = get_phase_thinking(spec_dir, phase, cli_thinking)
    thinking_budget = get_thinking_budget(thinking_level)

    return model_id, thinking_level, thinking_budget


def get_spec_phase_thinking_budget(phase_name: str) -> int | None:
    """
    Get the thinking budget for a specific spec runner phase.

    This maps granular spec phases (discovery, spec_writing, etc.) to their
    appropriate thinking budgets based on SPEC_PHASE_THINKING_LEVELS.

    Args:
        phase_name: Name of the spec phase (e.g., 'discovery', 'spec_writing')

    Returns:
        Token budget for extended thinking, or None for no extended thinking
    """
    thinking_level = SPEC_PHASE_THINKING_LEVELS.get(phase_name, "medium")
    return get_thinking_budget(thinking_level)
