"""Base agent abstraction."""
from typing import Any, Dict

from app.utils.llm_client import LLMClient


class BaseAgent:
    """Base class for all agents; provides LLM handle and common run signature."""

    def __init__(self, llm: LLMClient, response_language: str = "ko"):
        self.llm = llm
        self.response_language = response_language

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent against context. Child classes should override."""
        raise NotImplementedError

    def _llm_or_stub(self, prompt: str, context: Dict[str, Any]) -> str:
        """Helper to call LLM when available, else return deterministic stub."""
        localized_prompt = (
            f"{prompt}\n\n응답은 반드시 자연스러운 한국어로 작성하고, 필요한 경우 도메인 용어는 그대로 유지하세요."
        )
        try:
            return self.llm.generate(localized_prompt, context=context)
        except Exception:
            studio = context.get('meta', {}).get('studio_id', 'unknown')
            return f"[LLM 스텁 응답: 요청을 처리했으며 대상 스튜디오={studio}]"
