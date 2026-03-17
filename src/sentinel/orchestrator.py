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

        for plan in plans:
            created = self.client.create_agent(plan.agent_spec)
            prompt = self._compose_prompt(mission, plan)
            response = self.client.run_agent(created["id"], prompt)
            runs.append(
                AgentRunResult(
                    agent_name=plan.agent_spec.name,
                    task_type=plan.task_type,
                    output=response.get("output_text", ""),
                    metadata={
                        "agent_id": created.get("id", "unknown"),
                        "raw": response,
                    },
                )
            )

        final_answer = self._synthesize(runs)
        return SentinelResult(mission=mission, plans=plans, runs=runs, final_answer=final_answer)

    def _compose_prompt(self, mission: MissionInput, plan: TaskPlan) -> str:
        return (
            f"Workspace: {mission.workspace}\n"
            f"User query: {mission.user_query}\n"
            f"Additional context: {mission.context}\n"
            f"Task: {plan.task_type.value}\n"
            "Return actionable output and highlight uncertainty."
        )

    def _synthesize(self, runs: list[AgentRunResult]) -> str:
        chunks = [f"[{r.task_type.value}] {r.output}" for r in runs]
        return "\n\n".join(chunks)
