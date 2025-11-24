"""Explainer agent produces user-facing narrative."""
from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class ConsumerExplainerAgent(BaseAgent):
    """Generate concise explanation blending all agent outputs."""

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        summary = self._llm_or_stub(
            "인사이트·리스크·추천을 회원도 이해할 수 있는 자연스러운 한국어로 요약하세요.",
            context,
        )
        return {"message": summary}
