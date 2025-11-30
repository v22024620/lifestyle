"""Wellness insight agent backed by LLM or deterministic heuristic."""
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.services.studio_analytics import StudioAnalytics, get_studio_analytics


class WellnessInsightAgent(BaseAgent):
    """Summarizes studio performance patterns and KPIs."""

    def __init__(
        self,
        llm,
        *,
        analytics_service: Optional[StudioAnalytics] = None,
        response_language: str = "ko",
    ):
        super().__init__(llm, response_language=response_language)
        self.analytics = analytics_service or get_studio_analytics()

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
        studio_id = context.get("meta", {}).get("studio_id")
        studio_kpis: Dict[str, Any] = {}
        if studio_id:
            try:
                studio_kpis = self.analytics.compute_kpis(studio_id)
            except Exception as err:  # pragma: no cover - defensive guardrail
                studio_kpis = {"error": str(err)}
        vector_snapshot = {
            "documents_indexed": total,
            "modalities": sorted([m for m in modalities if m]),
            "avg_amount": round(avg_amount, 2) if amounts else None,
        }
        kpis = {**vector_snapshot, "studio": studio_kpis, "vector_snapshot": vector_snapshot}
        return kpis

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        kpis = self._extract_kpis(context)
        summary = self._llm_or_stub(
            "���Ͻ� ��Ʃ����� � ��ǥ�� ������ ������ ���� ����Ʈ�� �����ϼ���.",
            {**context, "kpis": kpis},
        )
        return {"summary": summary, "kpis": kpis}
