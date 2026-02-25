# Agent Workspace

A **proactive, autonomous AI agent** built with [Agno](https://agno.com) and
[Perplexity](https://perplexity.ai), designed to integrate with this WhatsApp
repository.

## Features

- **Task Decomposition** — PlannerAgent converts high-level objectives into atomic subtasks (DAG/sequential)
- **Heartbeat Loop** — OpenClaw-style `while` loop runs autonomously every N seconds
- **Perplexity Search** — Real-time grounded intelligence via `PerplexitySearch` tool
- **Short-Term Memory** — Agno `ShortTermMemory` maintains state across heartbeat ticks
- **Self-Correction** — Agent evaluates its own output and retries failed subtasks (max 2 retries)
- **Proactivity** — After all tasks complete, agent suggests and queues the next steps automatically

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your PERPLEXITY_API_KEY

# 3. Run the workspace
python agent_workspace.py
```

## File Structure

```
agent_workspace/
├── agent_workspace.py   # Core autonomous agent logic
├── config.py            # Environment + settings loader
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `PERPLEXITY_API_KEY` | ✅ | — | Your Perplexity API key |
| `OPENAI_API_KEY` | ❌ | — | Fallback LLM key |
| `PGVECTOR_DB_URL` | ❌ | localhost | Persistent memory DB |
| `HEARTBEAT_INTERVAL` | ❌ | 30 | Seconds between ticks |

## Extending

- Add WhatsApp-specific tools in `agent_workspace.py` under `tools=[...]`
- Swap `ShortTermMemory` for `PgVector` knowledge base for persistent long-term memory
- Deploy via `AgentOS` / FastAPI for a production webhook endpoint
