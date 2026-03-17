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


@app.command()
def ls() -> None:
    """List all Sentinel agents currently deployed in DigitalOcean."""
    settings = get_settings()
    if settings.enable_mock or not settings.do_api_token:
        print("[yellow]Mock mode — no live agents.[/yellow]")
        return
    client = DigitalOceanAgentClient(settings)
    import httpx
    with httpx.Client(timeout=15) as http:
        r = http.get(
            f"{settings.do_agent_base_url.rstrip('/')}/agents",
            headers={"Authorization": f"Bearer {settings.do_api_token}"},
        )
        r.raise_for_status()
    agents = r.json().get("agents", [])
    sentinel_agents = [a for a in agents if (a.get("name") or "").startswith("sentinel-")]
    print(f"[bold]{len(sentinel_agents)}[/bold] Sentinel agents on DigitalOcean:")
    for a in sentinel_agents:
        dep = a.get("deployment", {})
        print(f"  {a.get('name'):40s}  {a.get('uuid', '')}  status={dep.get('status', '?')}")


@app.command()
def cleanup() -> None:
    """Delete all ephemeral Sentinel agents from DigitalOcean."""
    settings = get_settings()
    if settings.enable_mock or not settings.do_api_token:
        print("[yellow]Mock mode — nothing to clean.[/yellow]")
        return
    import httpx
    with httpx.Client(timeout=15) as http:
        r = http.get(
            f"{settings.do_agent_base_url.rstrip('/')}/agents",
            headers={"Authorization": f"Bearer {settings.do_api_token}"},
        )
        r.raise_for_status()
    agents = r.json().get("agents", [])
    targets = [a for a in agents if (a.get("name") or "").startswith("sentinel-")]
    print(f"Deleting {len(targets)} Sentinel agents...")
    client = DigitalOceanAgentClient(settings)
    ok, fail = 0, 0
    for a in targets:
        try:
            client.delete_agent(a["uuid"])
            print(f"  [green]deleted[/green] {a.get('name')}")
            ok += 1
        except Exception as exc:
            print(f"  [red]failed[/red] {a.get('name')}: {exc}")
            fail += 1
    print(f"Done — {ok} deleted, {fail} failed.")
