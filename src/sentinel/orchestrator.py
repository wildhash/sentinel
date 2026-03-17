from __future__ import annotations

from typing import Protocol

from sentinel.agent_factory import AgentFactory
from sentinel.config import Settings
from sentinel.models import AgentRunResult, MissionInput, SentinelResult, TaskPlan, TaskType


class AgentClient(Protocol):
    def create_agent(self, spec): ...

    def run_agent(self, agent_id: str, prompt: str): ...


class SentinelOrchestrator:
    def __init__(self, settings: Settings, client: AgentClient) -> None:
        self.settings = settings
        self.client = client
        self.factory = AgentFactory(settings)

    def plan(self, mission: MissionInput) -> list[TaskPlan]:
        objective = mission.user_query
        tasks = [TaskType.recall, TaskType.contradiction, TaskType.next_action, TaskType.summarize]
        return [
            TaskPlan(task_type=task, objective=objective, agent_spec=self.factory.build(task, objective))
            for task in tasks
        ]

    def execute(self, mission: MissionInput) -> SentinelResult:
        plans = self.plan(mission)
        runs: list[AgentRunResult] = []
        spawned_ids: list[str] = []

        for plan in plans:
            created = self.client.create_agent(plan.agent_spec)
            agent_id = created.get("id", "unknown")
            prompt = self._compose_prompt(mission, plan)
            response = self.client.run_agent(agent_id, prompt)
            runs.append(
                AgentRunResult(
                    agent_name=plan.agent_spec.name,
                    task_type=plan.task_type,
                    output=response.get("output_text", ""),
                    metadata={
                        "agent_id": agent_id,
                        "model": response.get("model", ""),
                        "usage": response.get("usage", {}),
                        "finish_reason": response.get("finish_reason"),
                    },
                )
            )
            spawned_ids.append(agent_id)

        final_answer = self._synthesize(runs, spawned_ids)
        return SentinelResult(mission=mission, plans=plans, runs=runs, final_answer=final_answer)

    def _compose_prompt(self, mission: MissionInput, plan: TaskPlan) -> str:
        return (
            f"Workspace: {mission.workspace}\n"
            f"User query: {mission.user_query}\n"
            f"Additional context: {mission.context}\n"
            f"Task: {plan.task_type.value}\n"
            "Return actionable output and highlight uncertainty."
        )

    def _synthesize(self, runs: list[AgentRunResult], spawned_ids: list[str]) -> str:
        import uuid as _uuid
        specialist_outputs = "\n\n".join(
            [f"[{r.task_type.value.upper()}]\n{r.output}" for r in runs]
        )
        synthesis_system = (
            "You are an executive intelligence synthesizer. "
            "Given outputs from four specialist agents (recall, contradiction, next_action, summarize), "
            "produce a concise operator-ready brief with: "
            "1) KEY FINDINGS — what was discovered, "
            "2) CRITICAL CONTRADICTIONS — conflicts requiring resolution, "
            "3) IMMEDIATE NEXT ACTIONS — prioritised, risk-aware steps. "
            "Be specific. Flag uncertainty explicitly."
        )
        from sentinel.models import AgentSpec
        suffix = _uuid.uuid4().hex[:8]
        synthesis_spec = AgentSpec(
            name=f"sentinel-synthesizer-{suffix}",
            role="executive_synthesizer",
            system_prompt=synthesis_system,
            model=self.settings.default_model,
            tags=["sentinel", "synthesize", self.settings.workspace],
        )
        synth_id: str | None = None
        try:
            created = self.client.create_agent(synthesis_spec)
            synth_id = created.get("id")
            prompt = (
                f"Specialist outputs to synthesize:\n\n{specialist_outputs}\n\n"
                "Produce the final operator brief now."
            )
            response = self.client.run_agent(synth_id, prompt)
            result = response.get("output_text", specialist_outputs)
        except Exception:
            result = specialist_outputs
        finally:
            # Best-effort cleanup of all ephemeral agents spawned for this mission.
            all_ids = spawned_ids + ([synth_id] if synth_id else [])
            for aid in all_ids:
                try:
                    self.client.delete_agent(aid)  # type: ignore[attr-defined]
                except Exception:
                    pass
        return result
