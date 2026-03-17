# Sentinel Demo Script — 3 Minutes

## 0:00 — Hook (15 sec)
"Most multi-agent systems use fixed pipelines. Sentinel doesn't.
Every mission spawns fresh specialist agents at runtime on DigitalOcean Gradient AI,
routes them to targeted tasks, and synthesizes their output into a single operator brief."

## 0:15 — Show the problem (30 sec)
Open `docs/sample-knowledge-base.md` in the terminal or editor.
Point out:
- Launch date appears TWICE: April 1 (investor update) and April 15 (roadmap)
- Cloud costs flagged as overrun vs hiring plan still active
- Ownership of Q2 deliverable is ambiguous

"This is a realistic memory corpus — the kind of thing that builds up in any fast-moving team.
Sentinel's job is to find the contradictions humans miss."

## 0:45 — Run it (60 sec)
```bash
sentinel run "Find launch contradictions and propose next actions" \
  --context-file docs/sample-knowledge-base.md
```

Narrate while it runs:
- "Orchestrator is now planning four specialist tasks..."
- "Creating sentinel-recall agent on DigitalOcean Gradient AI..."
- "Creating sentinel-contradiction agent..."
- "Creating sentinel-next-action agent..."
- "Creating sentinel-summarize agent..."
- "Now the synthesis agent consolidates everything into a final brief."

Point out the output sections: KEY FINDINGS / CRITICAL CONTRADICTIONS / IMMEDIATE NEXT ACTIONS.

## 1:45 — Show JSON mode (20 sec)
```bash
sentinel run-json "Summarize memory risks" \
  --context-file docs/sample-knowledge-base.md
```
"Structured JSON output — ready to pipe into any automation pipeline,
dashboard, or downstream agent."

## 2:05 — Architecture callout (30 sec)
Show `src/sentinel/orchestrator.py` briefly.
"No LangChain. No wrapper libraries. Pure DigitalOcean GenAI API —
POST to /v2/gen-ai/agents, run via chat/completions.
Five agents per mission: four specialists plus a synthesis agent.
All using deepseek-r1-distill-llama-70b on DigitalOcean Gradient."

## 2:35 — Eval + close (25 sec)
```bash
sentinel evaluate evaluations/test_set.csv
```
"Ten eval cases covering contradiction detection, next-action planning,
and executive summarization. All testable locally via mock mode —
no credentials needed to develop."

Close: "EverMem Sentinel — autonomous memory operations on DigitalOcean Gradient AI.
Built for teams that can't afford to miss what their own data is telling them."
