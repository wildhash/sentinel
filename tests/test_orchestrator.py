from sentinel.config import Settings
from sentinel.do_client import MockDigitalOceanAgentClient
from sentinel.models import MissionInput
from sentinel.orchestrator import SentinelOrchestrator



def test_orchestrator_runs_full_plan() -> None:
    settings = Settings(
        do_api_token="",
        do_agent_base_url="https://api.digitalocean.com/v2/gen-ai",
        do_genai_api_version="v2",
        do_project_id="",
        do_region="tor1",
        do_model_access_key="",
        default_model="deepseek-r1-distill-llama-70b",
        workspace="evermem",
        enable_mock=True,
        log_level="INFO",
    )
    orchestrator = SentinelOrchestrator(settings, MockDigitalOceanAgentClient(settings))
    mission = MissionInput(user_query="Find contradictions in roadmap and summarize")

    result = orchestrator.execute(mission)

    assert len(result.plans) == 4
    assert len(result.runs) == 4
    assert "contradiction" in result.final_answer.lower()
