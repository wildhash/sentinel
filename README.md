# EverMem Sentinel

> **DigitalOcean Gradient™ AI Hackathon submission** — autonomous multi-agent memory operations system.

EverMem Sentinel dynamically spawns specialist AI agents at runtime on **DigitalOcean Gradient AI**, routes each to a targeted mission (recall, contradiction detection, next-action planning, or summarization), and synthesizes their outputs into a final operator-ready intelligence brief — all without a static agent chain.

---

## Why this is different

Most multi-agent systems hardcode a fixed pipeline. Sentinel does not.

- **Runtime agent spawning**: every mission creates fresh specialist agents via DigitalOcean GenAI API — no static chain, no stale context.
- **Mission-type routing**: four specialist roles (recall, contradiction, next_action, synthesize) are selected and composed per query.
- **LLM-powered synthesis**: a fifth synthesis agent consolidates all specialist outputs into a structured operator brief using `deepseek-r1-distill-llama-70b` on DigitalOcean Gradient.
- **DigitalOcean-native**: built entirely on `POST /v2/gen-ai/agents` and agent chat completions — no third-party orchestration frameworks.
- **Mock fallback**: local development works offline; flip `SENTINEL_ENABLE_MOCK=false` for live execution.

---

## Architecture

```
CLI query
  └─▶ Orchestrator: plan four specialist tasks
        ├─▶ DO GenAI API: create sentinel-recall agent
        ├─▶ DO GenAI API: create sentinel-contradiction agent
        ├─▶ DO GenAI API: create sentinel-next-action agent
        ├─▶ DO GenAI API: create sentinel-summarize agent
        └─▶ DO GenAI API: create sentinel-synthesizer agent
              └─▶ Final operator brief (structured JSON or human-readable)
```

---

## Quick Start

### 1. Install

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e .[dev]
```

### 2. Configure

```bash
copy .env.example .env
```

Set in `.env`:

| Variable | Description |
|---|---|
| `DO_API_TOKEN` | Your DigitalOcean personal access token |
| `DO_AGENT_BASE_URL` | `https://api.digitalocean.com/v2/gen-ai` |
| `SENTINEL_ENABLE_MOCK` | `false` for live DO execution, `true` for offline dev |
| `SENTINEL_DEFAULT_MODEL` | `deepseek-r1-distill-llama-70b` (or any DO GenAI model slug) |

### 3. Run (mock mode — no credentials needed)

```bash
sentinel run "Find launch contradictions and propose next actions" \
  --context-file docs/sample-knowledge-base.md
```

### 4. Run (live DigitalOcean Gradient AI)

```bash
# Set SENTINEL_ENABLE_MOCK=false in .env first
sentinel run-json "Summarize memory risks and flag contradictions" \
  --context-file docs/sample-knowledge-base.md
```

---

## Demo: 3-Minute Walkthrough

1. Open `docs/sample-knowledge-base.md` — shows a realistic project doc with embedded contradictions (launch date April 1 vs April 15, budget conflicts).
2. Run `sentinel run "Find contradictions and propose next actions" --context-file docs/sample-knowledge-base.md`
3. Watch Sentinel spawn four specialist agents live on DigitalOcean Gradient AI.
4. The synthesis agent consolidates all findings into a final brief.
5. Switch to `run-json` to show structured output for downstream automation.


---

## DigitalOcean Gradient AI Integration

Sentinel uses DigitalOcean's GenAI Agent API directly:

```python
# Create a specialist agent at runtime
POST https://api.digitalocean.com/v2/gen-ai/agents
{
  "name": "sentinel-contradiction",
  "model": {"slug": "deepseek-r1-distill-llama-70b"},
  "instruction": "Detect timeline and budget contradictions...",
  "description": "consistency_auditor"
}

# Run it against mission context
POST https://api.digitalocean.com/v2/gen-ai/agents/{id}/chat/completions
{"messages": [{"role": "user", "content": "<mission prompt>"}]}
```

No wrapper libraries. No LangChain. Pure DigitalOcean Gradient.

---

## Evaluation

```bash
sentinel evaluate evaluations/test_set.csv
```

The eval set covers contradiction detection, next-action generation, and summary quality across realistic project memory scenarios.

---

## Project Layout

| Path | Purpose |
|---|---|
| `src/sentinel/config.py` | Env-driven settings |
| `src/sentinel/do_client.py` | DigitalOcean GenAI client + mock fallback |
| `src/sentinel/agent_factory.py` | Runtime specialist agent definitions |
| `src/sentinel/orchestrator.py` | Plan → spawn → execute → synthesize loop |
| `src/sentinel/cli.py` | `sentinel run` and `sentinel run-json` commands |
| `evaluations/test_set.csv` | Eval dataset |
| `docs/sample-knowledge-base.md` | Contradiction-rich demo context |

---

## Testing

```bash
pytest -q
```

All tests run against the mock client — no credentials needed.

## License

MIT
