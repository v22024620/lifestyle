"""Pipeline-level tests for orchestrator and services."""
from app.config import get_settings
from app.services.agent_orchestrator import AgentOrchestrator


def test_pipeline_runs_and_caches() -> None:
    settings = get_settings()
    orchestrator = AgentOrchestrator(settings=settings)

    result1 = orchestrator.run_full_pipeline(user_query="test", studio_id="SGANG01")
    assert result1.insight["kpis"]["documents_indexed"] >= 0
    assert result1.risk["risk_score"] >= 0
    assert result1.strategy_framework["frameworks"]

    result2 = orchestrator.run_full_pipeline(user_query="test", studio_id="SGANG01")
    assert result2.cached is True
