"""Fee plan simulation service combining analytics + revenue architect agent."""
from typing import Any, Dict, List, Optional

from app.agents.revenue_architect_agent import RevenueArchitectAgent
from app.config import Settings
from app.services.studio_analytics import StudioAnalytics, get_studio_analytics
from app.utils.llm_client import LLMClient


class RecommendationSimulator:
    """Simulate fee-plan impacts leveraging historical metrics and the revenue agent."""

    def __init__(self, settings: Settings, analytics: Optional[StudioAnalytics] = None):
        self.settings = settings
        self.llm = LLMClient(settings.llm_endpoint, api_key=settings.openai_api_key)
        self.agent = RevenueArchitectAgent(self.llm)
        self.analytics = analytics or get_studio_analytics()

    @staticmethod
    def _normalize_payload(payload: Any) -> Dict[str, Any]:
        if hasattr(payload, "dict"):
            return payload.dict()
        return dict(payload)

    def simulate(self, payload: Any) -> Dict[str, Any]:
        """Combine KPI baselines, plan projections, and agent guidance."""
        normalized = self._normalize_payload(payload)
        studio_id = normalized.get("studio_id")
        window = self.analytics.derive_window(normalized.get("period"))
        baseline = self.analytics.compute_kpis(studio_id, window) if studio_id else {}
        current_plan = normalized.get("current_plan")
        candidate_plans: List[str] = normalized.get("candidate_plans") or []

        current_projection = None
        if studio_id and current_plan:
            current_projection = self.analytics.simulate_plan(studio_id, current_plan, window, baseline)

        candidate_projections = []
        for plan in candidate_plans:
            if not studio_id:
                continue
            candidate_projections.append(
                self.analytics.simulate_plan(studio_id, plan, window, baseline)
            )

        narrative_context = {
            "meta": {"studio_id": studio_id, "period": window.as_dict()},
            "baseline": baseline,
            "current_plan": current_projection,
            "candidates": candidate_projections,
        }
        narrative = self.agent.run(narrative_context)

        simulation_payload = {
            "studio_id": studio_id,
            "period": window.as_dict(),
            "baseline": baseline,
            "current_plan": current_projection,
            "candidates": candidate_projections,
            "agent_summary": narrative,
        }
        return {"simulation": simulation_payload, "input": normalized}
