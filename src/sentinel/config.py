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
    default_model: str
    workspace: str
    enable_mock: bool
    log_level: str



def get_settings() -> Settings:
    token = os.getenv("DO_API_TOKEN", "")
    return Settings(
        do_api_token=token,
        do_agent_base_url=os.getenv("DO_AGENT_BASE_URL", "https://api.digitalocean.com"),
        do_genai_api_version=os.getenv("DO_GENAI_API_VERSION", "v1"),
        default_model=os.getenv("SENTINEL_DEFAULT_MODEL", "gpt-4.1-mini"),
        workspace=os.getenv("SENTINEL_WORKSPACE", "evermem"),
        enable_mock=os.getenv("SENTINEL_ENABLE_MOCK", "true").lower() == "true",
        log_level=os.getenv("SENTINEL_LOG_LEVEL", "INFO"),
    )
