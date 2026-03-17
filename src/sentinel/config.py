from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    do_api_token: str
    do_agent_base_url: str
    do_genai_api_version: str
    do_project_id: str
    do_region: str
    do_model_access_key: str
    default_model: str
    workspace: str
    enable_mock: bool
    log_level: str



def get_settings() -> Settings:
    token = os.getenv("DO_API_TOKEN", "")
    return Settings(
        do_api_token=token,
        do_agent_base_url=os.getenv("DO_AGENT_BASE_URL", "https://api.digitalocean.com/v2/gen-ai"),
        do_genai_api_version=os.getenv("DO_GENAI_API_VERSION", "v2"),
        do_project_id=os.getenv("DO_PROJECT_ID", ""),
        do_region=os.getenv("DO_REGION", "tor1"),
        do_model_access_key=os.getenv("DO_MODEL_ACCESS_KEY", ""),
        default_model=os.getenv("SENTINEL_DEFAULT_MODEL", "deepseek-r1-distill-llama-70b"),
        workspace=os.getenv("SENTINEL_WORKSPACE", "evermem"),
        enable_mock=os.getenv("SENTINEL_ENABLE_MOCK", "true").lower() == "true",
        log_level=os.getenv("SENTINEL_LOG_LEVEL", "INFO"),
    )
