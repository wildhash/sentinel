from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from sentinel.config import get_settings
from sentinel.do_client import DigitalOceanAgentClient, MockDigitalOceanAgentClient
from sentinel.models import MissionInput
from sentinel.orchestrator import SentinelOrchestrator

app = typer.Typer(help="EverMem Sentinel CLI")



def _build_orchestrator() -> SentinelOrchestrator:
    settings = get_settings()
    if settings.enable_mock or not settings.do_api_token:
        client = MockDigitalOceanAgentClient(settings)
    else:
        client = DigitalOceanAgentClient(settings)
    return SentinelOrchestrator(settings, client)


@app.command()
def run(
    query: str = typer.Argument(..., help="Mission query"),
    context_file: Path | None = typer.Option(None, help="Optional context file"),
    workspace: str | None = typer.Option(None, help="Workspace slug override"),
) -> None:
    """Run full autonomous Sentinel mission."""
    context = context_file.read_text(encoding="utf-8") if context_file else ""
    settings = get_settings()
    mission = MissionInput(
        user_query=query,
        context=context,
        workspace=workspace or settings.workspace,
    )
    orchestrator = _build_orchestrator()
    result = orchestrator.execute(mission)

    print("[bold green]Sentinel mission complete[/bold green]")
    print(result.final_answer)


@app.command()
def run_json(
    query: str = typer.Argument(..., help="Mission query"),
    context_file: Path | None = typer.Option(None, help="Optional context file"),
) -> None:
    """Run and print structured JSON output for automation."""
    context = context_file.read_text(encoding="utf-8") if context_file else ""
    settings = get_settings()
    mission = MissionInput(user_query=query, context=context, workspace=settings.workspace)
    orchestrator = _build_orchestrator()
    result = orchestrator.execute(mission)
    print(json.dumps(result.model_dump(), indent=2))


@app.command()
def evaluate(dataset: Path = typer.Argument(..., exists=True, readable=True)) -> None:
    """Basic local evaluator over CSV with question and expected columns."""
    rows = [r for r in dataset.read_text(encoding="utf-8").splitlines() if r.strip()]
    header, *body = rows
    print(f"Loaded {len(body)} eval rows from {dataset}")
    print("Use DigitalOcean native eval tooling for leaderboard-grade results.")
