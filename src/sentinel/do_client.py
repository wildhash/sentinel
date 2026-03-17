from __future__ import annotations

from typing import Any

import httpx

from sentinel.config import Settings
from sentinel.models import AgentSpec


class DigitalOceanAgentClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._headers = {
            "Authorization": f"Bearer {settings.do_api_token}",
            "Content-Type": "application/json",
        }

    def _agents_url(self) -> str:
        return (
            f"{self.settings.do_agent_base_url.rstrip('/')}/"
            f"{self.settings.do_genai_api_version}/gen-ai/agents"
        )

    def create_agent(self, spec: AgentSpec) -> dict[str, Any]:
        payload = {
            "name": spec.name,
            "model": spec.model,
            "instructions": spec.system_prompt,
            "metadata": {
                "role": spec.role,
                "tags": spec.tags,
                "workspace": self.settings.workspace,
            },
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self._agents_url(), headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()

    def run_agent(self, agent_id: str, prompt: str) -> dict[str, Any]:
        run_url = f"{self._agents_url().rstrip('/')}/{agent_id}/responses"
        payload = {"input": prompt}
        with httpx.Client(timeout=60) as client:
            response = client.post(run_url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()


class MockDigitalOceanAgentClient:
    """Offline fallback that behaves like DigitalOcean agent endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._created: dict[str, dict[str, Any]] = {}

    def create_agent(self, spec: AgentSpec) -> dict[str, Any]:
        agent_id = f"mock-{len(self._created) + 1}"
        data = {
            "id": agent_id,
            "name": spec.name,
            "model": spec.model,
            "instructions": spec.system_prompt,
            "metadata": {"role": spec.role, "tags": spec.tags},
        }
        self._created[agent_id] = data
        return data

    def run_agent(self, agent_id: str, prompt: str) -> dict[str, Any]:
        agent = self._created.get(agent_id, {"name": "unknown"})
        return {
            "id": f"resp-{agent_id}",
            "output_text": (
                f"[{agent['name']}] analyzed prompt. "
                f"Top-line answer: {prompt[:240]}"
            ),
            "metadata": {"mock": True},
        }
