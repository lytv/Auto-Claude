# Auto-Claude Integration Guide

This guide explains how to integrate Clawdis with [Auto-Claude](https://github.com/AndyMik90/Auto-Claude), an autonomous multi-agent coding framework.

## Overview

Clawdis can communicate with Auto-Claude through multiple methods:

| Method | Direction | Complexity | Best For |
|--------|-----------|------------|----------|
| CLI Skill | Clawdis → Auto-Claude | Low | Running builds via chat |
| Webhook | Auto-Claude → Clawdis | Medium | Progress notifications |
| MCP Bridge | Bidirectional | High | Deep integration |

## Method 1: CLI Skill (Built-in)

Clawdis includes a pre-built skill for Auto-Claude at `~/.claude/skills/auto-claude-cli/SKILL.md`.

### Usage

Send commands via WhatsApp/Telegram:

```
"Create a spec for adding dark mode"
"Run the build for spec 001"
"Merge spec 001 into main"
```

The Pi Agent will invoke the corresponding Auto-Claude commands.

### Supported Commands

| Chat Message | Auto-Claude Command |
|--------------|---------------------|
| Create spec | `python spec_runner.py --task "..."` |
| Run build | `python run.py --spec 001` |
| Check status | `python run.py --list` |
| Merge changes | `python run.py --spec 001 --merge` |

## Method 2: Webhook Notifications

Enable Auto-Claude to send progress updates back to Clawdis.

### Clawdis Configuration

Add to `~/.clawdis/clawdis.json`:

```json5
{
  hooks: {
    enabled: true,
    basePath: "/hooks",
    token: "your-secret-token",
    mappings: [
      {
        id: "auto-claude",
        match: { source: "auto-claude" },
        action: "agent",
        messageTemplate: "🤖 Auto-Claude: {{status}}\n{{message}}",
        deliver: true,
        channel: "whatsapp"  // or "telegram", "discord"
      }
    ]
  }
}
```

### Sending Notifications from Auto-Claude

```python
import requests

def notify_clawdis(status, message, spec_id=None):
    requests.post(
        "http://127.0.0.1:18789/hooks/auto-claude",
        json={
            "source": "auto-claude",
            "status": status,
            "message": message,
            "spec": spec_id
        },
        headers={"Authorization": "Bearer your-secret-token"}
    )

# Example usage
notify_clawdis("Build Complete", "Spec 001 ready for review", "001")
```

### Running Auto-Claude with Notifications

**Option 1: CLI Argument**
```bash
python auto-claude/run.py --spec 001 \
  --notify-webhook http://127.0.0.1:18789/hooks/auto-claude
```

**Option 2: Environment Variable**
```bash
export CLAWDIS_WEBHOOK_URL="http://127.0.0.1:18789/hooks/auto-claude"
export CLAWDIS_WEBHOOK_TOKEN="your-secret-token"  # optional, default: auto-claude-secret-token
python auto-claude/run.py --spec 001
```

### Testing the Webhook

```bash
curl -X POST http://127.0.0.1:18789/hooks/auto-claude \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"source":"auto-claude","status":"Test","message":"Hello from Auto-Claude"}'
```

## Method 3: MCP Bridge (Advanced)

For deep integration, expose Auto-Claude as an MCP server.

### Architecture

```
Clawdis Gateway
    │
    ├─ Pi Agent (RPC)
    │     │
    │     └─ MCP Client ──────► Auto-Claude MCP Server
    │                              │
    │                              ├─ create_spec tool
    │                              ├─ run_build tool
    │                              └─ check_status tool
```

### Implementation Requirements

1. Create an MCP server in Auto-Claude using `@modelcontextprotocol/sdk`
2. Define tools: `create_spec`, `run_build`, `list_specs`, `merge_spec`
3. Configure Clawdis to connect to the MCP server

This method requires significant development effort but provides the most seamless integration.

## Recommended Setup

For most users, we recommend combining **Method 1 + Method 2**:

1. Use the CLI Skill to trigger Auto-Claude builds from chat
2. Configure webhooks to receive progress notifications

This provides bidirectional communication with minimal code changes.

## Related Documentation

- [Clawdis Hooks](webhook.md)
- [Agent Configuration](agent.md)
- [Gateway Protocol](gateway.md)
