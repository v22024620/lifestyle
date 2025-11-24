"""Agent unit tests."""
from app.config import get_settings
from app.services.agent_orchestrator import AgentOrchestrator


def _orchestrator():
    return AgentOrchestrator(settings=get_settings())


def test_agents_return_shapes():
    orch = _orchestrator()
    ctx = orch.graphrag.build_context(user_query="test", studio_id="STUDIO_TEST")
    ins = orch.insight_agent.run(ctx)
    risk = orch.risk_agent.run(ctx)
    reco = orch.reco_agent.run(ctx)
    strat = orch.strategy_agent.run({**ctx, "insight": ins, "risk": risk, "recommendation": reco})
    expl = orch.explainer_agent.run({"insight": ins, "risk": risk, "recommendation": reco, "strategy": strat})
    assert ins["kpis"]["documents_indexed"] >= 0
    assert risk["risk_score"] >= 0
    assert reco["items"]
    assert strat["frameworks"]
    assert "message" in expl
