from __future__ import annotations

import time
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
        self._model_uuid_cache: dict[str, str] = {}

    def _agents_url(self) -> str:
        return f"{self.settings.do_agent_base_url.rstrip('/')}/agents"

    def _models_url(self) -> str:
        return f"{self.settings.do_agent_base_url.rstrip('/')}/models"

    def _resolve_model_uuid(self, model_id_or_slug: str) -> str:
        if model_id_or_slug in self._model_uuid_cache:
            return self._model_uuid_cache[model_id_or_slug]
        with httpx.Client(timeout=30) as client:
            response = client.get(self._models_url(), headers=self._headers)
            response.raise_for_status()
            models = response.json().get("models", [])
        for model in models:
            if model.get("id") == model_id_or_slug or model.get("inference_name") == model_id_or_slug:
                uuid = model.get("uuid", "")
                self._model_uuid_cache[model_id_or_slug] = uuid
                return uuid
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
            response = None
            for attempt in range(5):
                response = client.post(self._agents_url(), headers=self._headers, json=payload)
                if response.status_code != 429:
                    break
                time.sleep(min(2**attempt, 10))

            if response is not None and response.status_code == 429:
                reused = self._find_reusable_agent(spec.name)
                if reused:
                    return reused

            if response is None:
                raise RuntimeError("No response received from DigitalOcean create_agent call")

            response.raise_for_status()
            data = response.json()
            # Normalize: DO returns {"agent": {...}} with "uuid" as the id field
            agent = data.get("agent", data)
            agent["id"] = agent.get("uuid") or agent.get("id") or data.get("id", "")
            return agent

    def _find_reusable_agent(self, generated_name: str) -> dict[str, Any] | None:
        # Names are generated as sentinel-<role>-<suffix>; reuse the latest matching base role.
        base_name = "-".join(generated_name.split("-")[:-1])
        with httpx.Client(timeout=30) as client:
            response = client.get(self._agents_url(), headers=self._headers)
            response.raise_for_status()
            agents = response.json().get("agents", [])

        candidates = [a for a in agents if (a.get("name") or "").startswith(base_name)]
        if not candidates:
            return None

        # API list is typically newest-first; sort defensively by updated_at when present.
        candidates.sort(key=lambda a: a.get("updated_at", ""), reverse=True)
        agent = candidates[0]
        agent["id"] = agent.get("uuid") or agent.get("id")
        return agent

    def delete_agent(self, agent_id: str) -> None:
        with httpx.Client(timeout=15) as client:
            client.delete(f"{self._agents_url()}/{agent_id}", headers=self._headers)

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
            infer_response = None
            for attempt in range(5):
                infer_response = client.post(infer_url, headers=headers, json=payload)
                if infer_response.status_code != 429:
                    break
                time.sleep(min(2**attempt, 10))
            if infer_response is None:
                raise RuntimeError("No response from inference endpoint")
            infer_response.raise_for_status()
            data = infer_response.json()
            choices = data.get("choices") or []
            output_text = choices[0].get("message", {}).get("content") if choices else ""
            # Keep only minimal structured metadata; avoid relaying internal reasoning traces.
            return {
                "output_text": output_text or "",
                "model": data.get("model", self.settings.default_model),
                "usage": {
                    "prompt_tokens": (data.get("usage") or {}).get("prompt_tokens", 0),
                    "completion_tokens": (data.get("usage") or {}).get("completion_tokens", 0),
                    "total_tokens": (data.get("usage") or {}).get("total_tokens", 0),
                },
                "finish_reason": (choices[0].get("finish_reason") if choices else None),
            }


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
            "output_text": (
                f"[{agent['name']}] analyzed prompt. "
                f"Top-line answer: {prompt[:240]}"
            ),
            "model": self.settings.default_model,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "finish_reason": "stop",
        }

    def delete_agent(self, agent_id: str) -> None:
        self._created.pop(agent_id, None)
