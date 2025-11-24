"""LLM client abstraction with OpenAI support and stub fallback."""
import json
import logging
from typing import Any, Dict, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Abstracts LLM interactions to allow stubbing or OpenAI-backed calls."""

    def __init__(self, endpoint: str | None = None, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self._client = None
        try:
            from openai import OpenAI  # type: ignore

            if self.api_key:
                self._client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
        except ImportError:
            logger.warning("openai package not installed; using stubbed LLM responses")

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate completion; falls back to stubbed string when OpenAI unavailable."""
        if self._client and self.api_key:
            try:
                user_content = prompt
                if context:
                    ctxt = json.dumps(context, ensure_ascii=False)
                    user_content = f"{prompt}\n\nContext:\n{ctxt}"
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an analytics copilot for lifestyle commerce partners. Always answer in Korean."},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.2,
                )
                return resp.choices[0].message.content or ""
            except Exception as err:  # pragma: no cover - network/keys/runtime dependent
                logger.warning("LLM call failed, falling back to stub: %s", err)
        context_info = f" context={context}" if context else ""
        return f"[LLM 스텁 응답] 요청을 처리했고 한국어 응답을 생성했습니다. prompt='{prompt[:50]}...' {context_info}"
