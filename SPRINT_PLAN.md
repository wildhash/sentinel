# Sentinel Sprint Plan

## Objective
Ship a demo-ready autonomous multi-agent memory system on DigitalOcean in one sprint.

## Hour 1: Environment and keys
- Prepare DigitalOcean API token.
- Confirm GenAI agent endpoint availability.
- Set `.env` values and run in mock mode first.

## Hour 2: Core behavior
- Validate dynamic agent spawning for all four specialist tasks.
- Test contradiction detection using sample knowledge base.
- Confirm JSON output for integration.

## Hour 3: Live DigitalOcean execution
- Switch `SENTINEL_ENABLE_MOCK=false`.
- Run one full mission against live agent endpoints.
- Capture output snippets for README and demo script.

## Hour 4: Demo and quality polish
- Run `pytest` and fix issues.
- Rehearse 3-minute walkthrough.
- Ensure README reflects exact commands used.

## Risks and fallbacks
- Endpoint mismatch: patch `do_client.py` request format.
- Token scope issue: validate API token permissions.
- Rate limits: run fewer specialists or queue missions.

## Deliverables
- Working codebase.
- Contradiction demo with sample docs.
- README with reproducible setup and run steps.
