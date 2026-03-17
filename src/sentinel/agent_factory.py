from __future__ import annotations

from sentinel.config import Settings
from sentinel.models import AgentSpec, TaskType


class AgentFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(self, task: TaskType, objective: str) -> AgentSpec:
        base = {
            "model": self.settings.default_model,
            "tags": ["sentinel", task.value, self.settings.workspace],
        }

        if task is TaskType.recall:
            return AgentSpec(
                name="sentinel-recall",
                role="memory_recall_specialist",
                system_prompt=(
                    "You are a high-precision memory retrieval agent. "
                    "Find factual memory artifacts and cite contradictions. "
                    f"Objective: {objective}"
                ),
                **base,
            )

        if task is TaskType.contradiction:
            return AgentSpec(
                name="sentinel-contradiction",
                role="consistency_auditor",
                system_prompt=(
                    "You detect timeline, budget, and ownership contradictions. "
                    "Return a conflict list with confidence and source snippets. "
                    f"Objective: {objective}"
                ),
                **base,
            )

        if task is TaskType.next_action:
            return AgentSpec(
                name="sentinel-next-action",
                role="operations_planner",
                system_prompt=(
                    "You transform findings into a pragmatic, risk-aware action plan "
                    "with immediate next steps. "
                    f"Objective: {objective}"
                ),
                **base,
            )

        return AgentSpec(
            name="sentinel-summarize",
            role="executive_summarizer",
            system_prompt=(
                "You produce concise executive summaries with explicit uncertainty. "
                f"Objective: {objective}"
            ),
            **base,
        )
