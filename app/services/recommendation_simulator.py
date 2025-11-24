"""Fee plan simulation service using revenue architect agent (stub)."""
from typing import Any, Dict

from app.config import Settings
from app.agents.revenue_architect_agent import RevenueArchitectAgent
from app.utils.llm_client import LLMClient


class RecommendationSimulator:
    """Simulate fee plan impacts using the revenue architect agent."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMClient(settings.llm_endpoint, api_key=settings.openai_api_key)
        self.agent = RevenueArchitectAgent(self.llm)

    def simulate(self, payload: Any) -> Dict[str, Any]:
        """Return stubbed simulation using agent insights."""
        normalized = payload.dict() if hasattr(payload, "dict") else payload
        agent_output = self.agent.run({"payload": normalized})
        return {"simulation": agent_output, "input": normalized}
