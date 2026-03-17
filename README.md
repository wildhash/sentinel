# Sentinel

Sentinel is an autonomous multi-agent memory operations system designed for DigitalOcean GenAI. It dynamically creates specialist agents per mission, runs them as a coordinated swarm, then merges outputs into a final operator-ready response.

## Why this is different

- Agent spawning at runtime: no fixed static chain.
- Specialist routing by mission type: recall, contradiction, next-action, summarize.
- DigitalOcean-native execution path with local mock fallback.
- Structured outputs for automation and future eval pipelines.

## Architecture

1. CLI receives mission query and optional context.
2. Orchestrator plans specialist tasks.
3. Agent factory generates targeted prompts and metadata.
4. DigitalOcean client creates and executes each agent.
5. Sentinel synthesizes all outputs into a final brief.

## Quick Start

### 1) Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

### 2) Configure

```bash
copy .env.example .env
```

Set your values in `.env`:
- `DO_API_TOKEN`
- `DO_AGENT_BASE_URL`
- `DO_GENAI_API_VERSION`
- `DO_PROJECT_ID`
- `DO_REGION`
- `DO_MODEL_ACCESS_KEY` (required for live inference at `inference.do-ai.run`)
- `SENTINEL_ENABLE_MOCK=false` to use live DigitalOcean APIs

DigitalOcean flow:
- Agent management: `DO_API_TOKEN` against `api.digitalocean.com/v2/gen-ai`
- Inference: `DO_MODEL_ACCESS_KEY` against `inference.do-ai.run`

### 3) Run

```bash
sentinel run "Find launch contradictions and propose next actions" --context-file docs/sample-knowledge-base.md
```

JSON mode:

```bash
sentinel run-json "Summarize the memory risks" --context-file docs/sample-knowledge-base.md
```

## Project Layout

- `src/sentinel/config.py`: env-driven settings.
- `src/sentinel/do_client.py`: DigitalOcean and mock clients.
- `src/sentinel/agent_factory.py`: dynamic specialist definitions.
- `src/sentinel/orchestrator.py`: plan, spawn, execute, synthesize loop.
- `src/sentinel/cli.py`: operator commands.
- `evaluations/test_set.csv`: starter eval dataset.
- `docs/sample-knowledge-base.md`: contradiction-rich demo data.

## Demo Flow (3 minutes)

1. Show sample knowledge base conflict (April 1 vs April 15 launch).
2. Run Sentinel mission from CLI.
3. Highlight contradiction specialist output.
4. Show next-action plan with risk-aware recommendations.
5. Mention live mode by switching `SENTINEL_ENABLE_MOCK=false`.

## Notes on DigitalOcean Integration

The code uses DigitalOcean GenAI v2 management + inference split:
- `POST /v2/gen-ai/agents` for dynamic agent creation
- `POST https://inference.do-ai.run/v1/chat/completions` for model inference

If your account uses different payload requirements, adjust only `src/sentinel/do_client.py`.

## Testing

```bash
pytest -q
```

## License

MIT
