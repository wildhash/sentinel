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
        return f"{self.settings.do_agent_base_url.rstrip('/')}/agents"

    def _models_url(self) -> str:
        return f"{self.settings.do_agent_base_url.rstrip('/')}/models"

    def _resolve_model_uuid(self, model_id_or_slug: str) -> str:
        with httpx.Client(timeout=30) as client:
            response = client.get(self._models_url(), headers=self._headers)
            response.raise_for_status()
            models = response.json().get("models", [])
        for model in models:
            if model.get("id") == model_id_or_slug or model.get("inference_name") == model_id_or_slug:
                return model.get("uuid", "")
        raise ValueError(f"Could not resolve model UUID for '{model_id_or_slug}'")

    def create_agent(self, spec: AgentSpec) -> dict[str, Any]:
        model_uuid = self._resolve_model_uuid(spec.model)
        payload = {
            "name": spec.name,
            "model_uuid": model_uuid,
            "instruction": spec.system_prompt,
            "description": spec.role,
            "project_id": self.settings.do_project_id,
            "region": self.settings.do_region,
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self._agents_url(), headers=self._headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Normalize: DO returns {"agent": {...}} with "uuid" as the id field
            agent = data.get("agent", data)
            agent["id"] = agent.get("uuid") or agent.get("id") or data.get("id", "")
            return agent

    def run_agent(self, agent_id: str, prompt: str) -> dict[str, Any]:
        # DigitalOcean separates management (agent CRUD) and inference (model access key).
        # If no model access key is configured yet, return a deterministic instruction.
        if not self.settings.do_model_access_key:
            return {
                "output_text": (
                    "Agent created successfully, but DO_MODEL_ACCESS_KEY is missing. "
                    "Create a Model Access Key in DigitalOcean and set it in .env to enable live inference."
                ),
                "metadata": {"agent_id": agent_id, "requires_model_access_key": True},
            }

        infer_url = "https://inference.do-ai.run/v1/chat/completions"
        payload = {
            "model": self.settings.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.do_model_access_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=90) as client:
            response = client.post(infer_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            output_text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            return {"output_text": output_text, **data}


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
