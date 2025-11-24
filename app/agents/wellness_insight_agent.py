"""Wellness insight agent backed by LLM or deterministic heuristic."""
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class WellnessInsightAgent(BaseAgent):
    """Summarizes studio performance patterns and KPIs."""

    def _extract_kpis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        vectors: List[Dict[str, Any]] = context.get("vector", [])
        total = len(vectors)
        modalities = {doc.get("metadata", {}).get("category") for doc in vectors if doc.get("metadata")}
        avg_amount = 0.0
        amounts = []
        for doc in vectors:
            meta = doc.get("metadata", {})
            try:
                amounts.append(float(meta.get("amount", 0)))
            except Exception:
                continue
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
        return {
            "documents_indexed": total,
            "modalities": sorted([m for m in modalities if m]),
            "avg_amount": round(avg_amount, 2) if amounts else None,
        }

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        kpis = self._extract_kpis(context)
        summary = self._llm_or_stub(
            "웰니스 스튜디오의 운영 지표와 패턴을 간결한 실행 포인트로 정리하세요.",
            {**context, "kpis": kpis},
        )
        return {"summary": summary, "kpis": kpis}
