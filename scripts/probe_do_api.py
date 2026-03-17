"""
Quick probe script — discovers live DO GenAI API shape.
Run: python scripts/probe_do_api.py
Never commit this file with real output.
"""
from __future__ import annotations

import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DO_API_TOKEN", "")
base = os.getenv("DO_AGENT_BASE_URL", "https://api.digitalocean.com/v2/gen-ai")

if not token:
    print("DO_API_TOKEN not set — aborting probe")
    sys.exit(1)

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def probe(label: str, method: str, path: str, body: dict | None = None) -> None:
    url = f"{base.rstrip('/')}/{path.lstrip('/')}"
    print(f"\n{'='*60}")
    print(f"{method} {url}")
    with httpx.Client(timeout=20) as client:
        fn = getattr(client, method.lower())
        kwargs: dict = {"headers": headers}
        if body is not None:
            kwargs["json"] = body
        try:
            resp = fn(url, **kwargs)
            print(f"Status: {resp.status_code}")
            try:
                data = resp.json()
                print(json.dumps(data, indent=2)[:2000])
            except Exception:
                print(resp.text[:2000])
        except Exception as exc:
            print(f"Error: {exc}")

model_slug = os.getenv("SENTINEL_DEFAULT_MODEL", "openai-gpt-oss-120b")

probe("List agents", "GET", "agents")
probe("List models", "GET", "models")
probe("Create test agent", "POST", "agents", {
    "name": "sentinel-probe-delete-me",
    "model": {"slug": model_slug},
    "instruction": "You are a test probe agent. Answer briefly.",
    "description": "probe",
})
