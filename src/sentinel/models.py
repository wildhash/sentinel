from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    recall = "recall"
    contradiction = "contradiction"
    next_action = "next_action"
    summarize = "summarize"


class MissionInput(BaseModel):
    user_query: str = Field(min_length=1)
    context: str = ""
    workspace: str = "evermem"


class AgentSpec(BaseModel):
    name: str
    role: str
    system_prompt: str
    model: str
    tags: list[str] = Field(default_factory=list)


class TaskPlan(BaseModel):
    task_type: TaskType
    objective: str
    agent_spec: AgentSpec


class AgentRunResult(BaseModel):
    agent_name: str
    task_type: TaskType
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SentinelResult(BaseModel):
    mission: MissionInput
    plans: list[TaskPlan]
    runs: list[AgentRunResult]
    final_answer: str
