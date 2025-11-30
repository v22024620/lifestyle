"""Strategy framework agent combining multiple lenses."""
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class StrategyFrameworkAgent(BaseAgent):
    """Provide PESTEL and 5-forces style framing based on context."""

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        studio_id = context.get("meta", {}).get("studio_id")
        knowledge_refs: List[Dict[str, Any]] = context.get("knowledge") or []
        frameworks = {
            "pestel": {
                "economic": "Optimize fee mix to protect margin amid spending volatility",
                "technological": "Adopt graph+vector driven personalization to lift conversion",
                "legal": "Monitor chargeback trends for compliance readiness",
            },
            "porter5": {
                "threat_of_substitutes": "High: digital wallets proliferating",
                "buyer_power": "Medium: lifestyle cohorts price-sensitive",
                "rivalry": "Rising: new entrants in vertical BNPL",
            },
        }
        key_actions = [
            "Deploy graph+vector context in onboarding and risk rules",
            "Prioritize segments with stable signals before fee plan experiments",
            "Instrument dashboards for ARPPU/decline-rate/chargeback",
        ]
        dynamic_actions = []
        for ref in knowledge_refs[:3]:
            title = ref.get("title") or "Agentic Insight"
            snippet = (ref.get("snippet") or "").strip()
            dynamic_actions.append(f"{title}: {snippet[:90]}...")
        if dynamic_actions:
            key_actions = dynamic_actions + key_actions
        narrative = self._llm_or_stub(
            "Summarize PESTEL and 5-forces plus 3 key actions using knowledge references.",
            {"frameworks": frameworks, "knowledge": knowledge_refs, **context},
        )
        return {
            "studio_id": studio_id,
            "frameworks": frameworks,
            "key_actions": key_actions,
            "narrative": narrative,
            "knowledge_refs": knowledge_refs[:5],
        }
