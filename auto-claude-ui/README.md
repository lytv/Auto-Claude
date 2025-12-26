# Auto Claude UI

A desktop application for managing AI-driven development tasks using the Auto Claude autonomous coding framework.

## Quick Start

```bash
# 1. Clone the repo (if you haven't already)
git clone https://github.com/AndyMik90/Auto-Claude.git
cd Auto-Claude/auto-claude-ui

# 2. Install dependencies
npm install

# 3. Build the desktop app
npm run package:win    # Windows
npm run package:mac    # macOS
npm run package:linux  # Linux

# 4. Run the app
# Windows: .\dist\win-unpacked\Auto Claude.exe
# macOS:   open dist/mac-arm64/Auto\ Claude.app
# Linux:   ./dist/linux-unpacked/auto-claude
```

## Prerequisites

- Node.js 18+
- npm or pnpm
- Python 3.10+ (for auto-claude backend)
- **Windows only**: Visual Studio Build Tools 2022 with "Desktop development with C++" workload
- **Windows only**: Developer Mode enabled (Settings → System → For developers)

## Configuration & Environment Variables

Auto Claude UI manages a local `.env` file in your project's `auto-claude` directory. You can configure these variables through the UI (Settings > Integrations) or manually edits the `.env` file.

### Core Configuration
- `CLAUDE_CODE_OAUTH_TOKEN`: (Required) OAuth token for Claude Code SDK.
- `AUTO_BUILD_MODEL`: Override the default model (e.g., `claude-opus-4-5-20251101`).

### Provider Configuration (Graphiti & Memory)
Auto Claude supports multiple AI providers for its memory and knowledge graph subsystem (Graphiti).

**OpenAI**
- `OPENAI_API_KEY`: Your OpenAI API Key.
- `OPENAI_MODEL`: Model to use (default: `gpt-4o-mini`).
- `OPENAI_EMBEDDING_MODEL`: Embedding model (default: `text-embedding-3-small`).

**Anthropic**
- `ANTHROPIC_API_KEY`: Your Anthropic API Key.
- `GRAPHITI_ANTHROPIC_MODEL`: Model to use (default: `claude-sonnet-4-5-latest`).

**Azure OpenAI**
- `AZURE_OPENAI_API_KEY`: Azure API Key.
- `AZURE_OPENAI_BASE_URL`: Endpoint URL.
- `AZURE_OPENAI_LLM_DEPLOYMENT`: Deployment name for LLM.
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Deployment name for embeddings.

**Google / Gemini**
- `GOOGLE_API_KEY`: Google AI API Key.
- `GOOGLE_LLM_MODEL`: Model (default: `gemini-2.0-flash`).
- `GOOGLE_EMBEDDING_MODEL`: Embedding model (default: `text-embedding-004`).

**Ollama (Local)**
- `OLLAMA_BASE_URL`: URL for Ollama server (default: `http://localhost:11434`).
- `OLLAMA_LLM_MODEL`: API model name.
- `OLLAMA_EMBEDDING_MODEL`: Embedding model name.
- `OLLAMA_EMBEDDING_DIM`: Embedding dimensions (default: `768`).

**Voyage AI**
- `VOYAGE_API_KEY`: API Key for Voyage embeddings.
- `VOYAGE_EMBEDDING_MODEL`: Model (default: `voyage-3`).

### Integrations

**Linear**
- `LINEAR_API_KEY`: API key for Linear sync.
- `LINEAR_TEAM_ID`: (Optional) Filter by team.
- `LINEAR_PROJECT_ID`: (Optional) Filter by project.
- `LINEAR_REALTIME_SYNC`: `true`/`false` to enable real-time webhook sync.

**GitHub**
- `GITHUB_TOKEN`: Personal Access Token (PAT) with `repo` scope.
- `GITHUB_REPO`: Repository identifier (e.g., `owner/repo`).
- `GITHUB_AUTO_SYNC`: `true`/`false` to auto-fetch issues.

**Git / Worktrees**
- `DEFAULT_BRANCH`: Base branch for creating task worktrees (default: `main`).

---

## using y-router and Proxies

Auto Claude supports routing AI traffic through proxies like **y-router** for enhanced control, rate limiting optimization, and caching.

To configure `y-router` or any compatible proxy:

1.  **Deploy your router**: Ensure `y-router` is running (e.g., at `http://localhost:8080`).
2.  **Configure Base URLs**: Set the `BASE_URL` environment variables to point to your router.
    *   For **OpenAI-compatible** routing: Set `OPENAI_BASE_URL` (if supported by your provider config) or use `AZURE_OPENAI_BASE_URL` / `OLLAMA_BASE_URL` depending on the protocol.
    *   The Agent process inherits your system environment variables, so you can also set `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` globally before launching the app.
3.  **Model Mapping**: `y-router` typically handles model mapping. Ensure your `AUTO_BUILD_MODEL` or provider model names match what `y-router` expects or map them in the router config.

## Development

```bash
# Run in development mode with hot reload
npm run dev

# Run tests
npm run test

# Run ESLint
npm run lint
```

## Features

- **Project Management**: Add, configure, and switch between multiple projects
- **Kanban Board**: Visual task board with columns for Backlog, In Progress, AI Review, Human Review, and Done
- **Task Creation Wizard**: Form-based interface for creating new tasks
- **Real-Time Progress**: Live updates during agent execution
- **Human Review Workflow**: Review QA results and provide feedback
- **Theme Support**: Light and dark mode
- **Auto Updates**: Automatic update notifications
- **Multi-Provider AI**: Support for OpenAI, Anthropic, Google, Azure, and Ollama backends.

## License

AGPL-3.0
