"""FastAPI web server wrapping the Sentinel multi-agent orchestrator.

Two execution modes:
  live   — real DO GenAI agents when DO_API_TOKEN + DO_MODEL_ACCESS_KEY are set
  demo   — high-fidelity representative responses for quick demos / CI
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Sentinel", description="Autonomous multi-agent memory ops", version="0.1.0")

_FRONTEND_DIR = Path(__file__).parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    context: str = Field(default="", max_length=4000)
    workspace: str = Field(default="evermem", max_length=64)


class AgentRunSummary(BaseModel):
    agent_name: str
    task_type: str
    output: str


class QueryResponse(BaseModel):
    final_answer: str
    agents_spawned: int
    runs: list[AgentRunSummary]
    mode: str  # "live" or "demo"


# ---------------------------------------------------------------------------
# Demo-mode responses (representative of real pipeline output)
# ---------------------------------------------------------------------------

_DEMO_RUNS: dict[str, str] = {
    "recall": textwrap.dedent("""\
        MEMORY RECALL — deepseek-r1-distill-llama-70b

        Retrieved 3 relevant memory artifacts:
        • artifact-0041: Launch date recorded as April 1 in Q1 planning doc (confidence 0.97)
        • artifact-0078: Launch date recorded as April 15 in engineering sprint plan (confidence 0.94)
        • artifact-0103: Budget ceiling $420k noted in exec brief; $380k noted in ops ledger

        Uncertainty: no canonical source-of-truth document found for launch date.
    """),
    "contradiction": textwrap.dedent("""\
        CONTRADICTION AUDIT — deepseek-r1-distill-llama-70b

        Conflicts detected (2):

        1. LAUNCH DATE [HIGH]
           Source A: "April 1" (Q1 planning doc, artifact-0041)
           Source B: "April 15" (Engineering sprint plan, artifact-0078)
           Delta: 14 days. Owner unclear. Resolution required before sprint freeze.

        2. BUDGET CEILING [MEDIUM]
           Source A: $420,000 (exec brief, artifact-0103)
           Source B: $380,000 (ops ledger, artifact-0103)
           Delta: $40,000. Likely reflects approved vs. allocated; confirm with Finance.
    """),
    "next_action": textwrap.dedent("""\
        OPERATIONS PLAN — deepseek-r1-distill-llama-70b

        Immediate next actions (risk-ordered):

        1. [CRITICAL] Schedule launch-date sync between Product & Engineering today.
           Risk: misaligned sprints, missed external commitments.

        2. [HIGH] Finance to confirm budget figure for ops ledger by EOD.
           Risk: over-spend or blocked procurement if ceiling is $380k not $420k.

        3. [MEDIUM] Establish a canonical planning doc as single source of truth.
           Recommend: product-wiki/launch-v2.md with mandatory PR review.
    """),
    "summarize": textwrap.dedent("""\
        EXECUTIVE SUMMARY — deepseek-r1-distill-llama-70b

        5 agents spawned on DO Gradient (runtime via DO GenAI API).
        2 critical contradictions found in workspace memory.
        Action plan generated with 3 prioritised steps.

        Bottom line: launch date and budget ceiling are unresolved. Both must be
        locked before the next sprint planning session to avoid downstream
        execution risk.
    """),
}

_DEMO_FINAL = textwrap.dedent("""\
    ## KEY FINDINGS
    Sentinel detected 2 contradictions in workspace memory: a 14-day launch date
    discrepancy (April 1 vs April 15) and a $40k budget ceiling mismatch ($420k
    vs $380k). These were surfaced by runtime agents spawned against
    deepseek-r1-distill-llama-70b via the DigitalOcean GenAI API.

    ## CRITICAL CONTRADICTIONS
    1. **Launch date** — Q1 planning doc says April 1; engineering sprint plan says
       April 15. Neither is marked authoritative.
    2. **Budget ceiling** — exec brief cites $420,000; ops ledger cites $380,000.

    ## IMMEDIATE NEXT ACTIONS
    1. Product × Engineering launch-date sync — today.
    2. Finance confirmation of canonical budget figure — EOD.
    3. Establish single-source-of-truth planning document with PR-gated updates.

    *Confidence: HIGH on contradiction detection | MEDIUM on resolution path*
""")


def _run_demo(query: str) -> QueryResponse:
    runs = [
        AgentRunSummary(
            agent_name=f"sentinel-{task}-demo",
            task_type=task,
            output=_DEMO_RUNS[task],
        )
        for task in ("recall", "contradiction", "next_action", "summarize")
    ]
    return QueryResponse(
        final_answer=_DEMO_FINAL,
        agents_spawned=5,
        runs=runs,
        mode="demo",
    )


# ---------------------------------------------------------------------------
# Live orchestration (imported lazily so demo mode works without the package)
# ---------------------------------------------------------------------------

def _run_live(query: str, context: str, workspace: str) -> QueryResponse:
    from sentinel.config import get_settings
    from sentinel.do_client import DigitalOceanAgentClient, MockDigitalOceanAgentClient
    from sentinel.models import MissionInput
    from sentinel.orchestrator import SentinelOrchestrator

    settings = get_settings()
    client: Union[DigitalOceanAgentClient, MockDigitalOceanAgentClient] = (
        MockDigitalOceanAgentClient(settings)
        if settings.enable_mock
        else DigitalOceanAgentClient(settings)
    )
    orchestrator = SentinelOrchestrator(settings, client)
    mission = MissionInput(user_query=query, context=context, workspace=workspace)
    result = orchestrator.execute(mission)

    runs = [
        AgentRunSummary(
            agent_name=r.agent_name,
            task_type=r.task_type.value,
            output=r.output,
        )
        for r in result.runs
    ]
    return QueryResponse(
        final_answer=result.final_answer,
        agents_spawned=len(result.runs) + 1,  # specialists + synthesizer
        runs=runs,
        mode="mock" if settings.enable_mock else "live",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(str(_FRONTEND_DIR / "index.html"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "sentinel"}


@app.post("/query", response_model=QueryResponse)
async def query_sentinel(request: QueryRequest) -> QueryResponse:
    use_demo = os.getenv("SENTINEL_DEMO_MODE", "").lower() in ("1", "true", "yes")

    if use_demo:
        return _run_demo(request.query)

    try:
        return _run_live(request.query, request.context, request.workspace)
    except ImportError:
        # Sentinel package not installed; fall back to demo.
        return _run_demo(request.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
