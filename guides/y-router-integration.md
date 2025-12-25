# Y-Router Integration Guide: Using OpenRouter with Auto-Claude

This document details how Auto-Claude agents use y-router as a proxy to route requests through OpenRouter, enabling the use of alternative AI models.

---

## 📖 Overview

**y-router** is a translation layer (Cloudflare Worker) that sits between **Claude Code SDK** and **OpenRouter**. It allows Auto-Claude's agents, which communicate using **Anthropic's API format**, to seamlessly use any model available on OpenRouter (e.g., GPT-4, Gemini, Mistral, DeepSeek, etc.).

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Auto-Claude UI                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     Agent Process Manager                       │    │
│  │  - Sets environment variables (ANTHROPIC_BASE_URL, etc.)       │    │
│  │  - Spawns Python runners (spec_runner.py, run.py)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────│────────────────────────────────────────┘
                                 │
                                 ▼  (HTTP Request: Anthropic Format)
                                 │   POST /v1/messages
                                 │   Model: claude-sonnet-4-20250514
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                             y-router                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  1. Receives Anthropic-format request                           │   │
│  │  2. Maps model name (e.g., "sonnet" → "google/gemini-2.5-flash") │   │
│  │  3. Converts message format (Anthropic → OpenAI Chat)           │   │
│  │  4. Forwards to OpenRouter API                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────│────────────────────────────────────────┘
                                 │
                                 ▼  (HTTP Request: OpenAI Format)
                                 │   POST /v1/chat/completions
                                 │   Model: google/gemini-2.5-flash
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                           OpenRouter.ai                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - Routes to the actual LLM provider (Google, OpenAI, etc.)     │   │
│  │  - Returns OpenAI-format response                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────│────────────────────────────────────────┘
                                 │
                                 ▼  (HTTP Response: OpenAI Format)
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                             y-router                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  5. Receives OpenAI-format response                             │   │
│  │  6. Converts to Anthropic format                                │   │
│  │  7. Streams back to Auto-Claude agent                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────│────────────────────────────────────────┘
                                 │
                                 ▼  (HTTP Response: Anthropic Format)
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                          Auto-Claude Agent                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  - Claude Code SDK receives familiar Anthropic response         │   │
│  │  - Agent continues task execution as normal                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 How It Works

### 1. Environment Variable Setup

When Auto-Claude spawns an agent process, the `AgentProcessManager` injects environment variables that redirect traffic:

**Key Environment Variables:**
| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `ANTHROPIC_BASE_URL` | Redirects Claude SDK to y-router instead of Anthropic API | `http://localhost:8787` |
| `ANTHROPIC_API_KEY` | Your OpenRouter API key (passed as auth) | `sk-or-v1-xxxxx` |

**Source:** `auto-claude-ui/src/main/agent/agent-process.ts`

### 2. Model Mapping

Y-router maps Claude model names to OpenRouter-compatible model IDs.

**Mapping Logic (from `formatRequest.ts`):**
```typescript
// If request asks for a model containing "haiku"
if (modelLower.includes('haiku')) {
  return config?.haiku || 'anthropic/claude-3.5-haiku';
} else if (modelLower.includes('sonnet')) {
  return config?.sonnet || 'anthropic/claude-sonnet-4';
} else if (modelLower.includes('opus')) {
  return config?.opus || 'anthropic/claude-opus-4';
}
```

**Default Mappings (if no config is set):**
| Claude Model | OpenRouter Default |
|--------------|-------------------|
| `claude-opus-*` | `anthropic/claude-opus-4` |
| `claude-sonnet-*` | `anthropic/claude-sonnet-4` |
| `claude-haiku-*` | `anthropic/claude-3.5-haiku` |

**Source:** `y-router/formatRequest.ts`

### 3. Request/Response Translation

The y-router translates:
1. **Anthropic Request** (tool_use, tool_result blocks) → **OpenAI Request** (tool_calls, tool role messages)
2. **OpenAI Response** (choices, messages) → **Anthropic Response** (content blocks, stop_reason)

This translation is critical because Claude Code SDK expects Anthropic's API format, but OpenRouter provides an OpenAI-compatible interface.

---

## 🚀 Setting Up Y-Router

### Option A: Use the Public Instance (Quick Start)

Set these environment variables in your `auto-claude/.env`:

```bash
ANTHROPIC_BASE_URL="https://cc.yovy.app"
ANTHROPIC_API_KEY="your-openrouter-api-key"
```

### Option B: Run Y-Router Locally (Recommended for Development)

1. **Clone and start y-router:**
   ```bash
   cd /Users/mac/tools/y-router
   docker-compose up -d
   ```

2. **Configure Auto-Claude:**
   Add to `auto-claude/.env`:
   ```bash
   ANTHROPIC_BASE_URL="http://localhost:8787"
   ANTHROPIC_API_KEY="your-openrouter-api-key"
   
   # Optional: Override model mappings
   MODEL_MAP_OPUS="google/gemini-2.5-pro"
   MODEL_MAP_SONNET="moonshotai/kimi-k2"
   MODEL_MAP_HAIKU="google/gemini-2.5-flash"
   ```

3. **Restart the y-router with new config:**
   ```bash
   docker-compose down && docker-compose up -d
   ```

---

## ⚙️ Configuration Options

### Model Mapping Environment Variables

Set these in y-router's `.env` file to override default mappings:

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_MAP_OPUS` | Replace Opus requests | `deepseek/deepseek-r1` |
| `MODEL_MAP_SONNET` | Replace Sonnet requests | `moonshotai/kimi-k2` |
| `MODEL_MAP_HAIKU` | Replace Haiku requests | `google/gemini-2.5-flash` |

### Available Models on OpenRouter

Browse all available models at: [openrouter.ai/models](https://openrouter.ai/models)

Popular alternatives include:
- `google/gemini-2.5-pro` - Google's latest flagship
- `moonshotai/kimi-k2` - Moonshot's powerful model
- `deepseek/deepseek-r1` - DeepSeek's reasoning model
- `openai/gpt-4o` - OpenAI's multimodal model

---

## 🔍 Debugging

### Check if Y-Router is Running

```bash
curl http://localhost:8787/
# Should return HTML welcome page
```

### View Y-Router Logs

```bash
cd /Users/mac/tools/y-router
docker-compose logs -f
```

### Test a Request Manually

```bash
curl -X POST http://localhost:8787/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-openrouter-key" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

---

## ⚠️ Important Notes

1. **Tool Support:** Y-router translates Anthropic's `tool_use`/`tool_result` blocks to OpenAI's `tool_calls`/`tool` format. This means MCP tools and other agent features work correctly.

2. **Streaming:** Both streaming and non-streaming responses are supported.

3. **Cost Considerations:** Using OpenRouter incurs costs based on your selected model. Check pricing at [openrouter.ai/models](https://openrouter.ai/models).

4. **Rate Limits:** OpenRouter has its own rate limits. If you hit them, Auto-Claude's rate limit detection will trigger.

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `y-router/index.ts` | Main proxy server |
| `y-router/formatRequest.ts` | Anthropic → OpenAI translation |
| `y-router/formatResponse.ts` | OpenAI → Anthropic translation |
| `auto-claude/.env` | Agent environment config |
