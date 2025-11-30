"""Risk guard agent detecting anomalies and chargeback signals."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.agents.base_agent import BaseAgent
from app.services.policy_engine import PolicyEngine
from app.services.studio_analytics import StudioAnalytics, get_studio_analytics

_SUSPICIOUS_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "refund": ("refund", "chargeback", "dispute"),
    "decline": ("decline", "fraud", "blocked", "failed"),
    "safety": ("injury", "incident", "hazard"),
}


class RiskGuardAgent(BaseAgent):
    """Identify wellness risk signals from graph/vector context."""

    def __init__(
        self,
        llm,
        *,
        policy_engine: PolicyEngine | None = None,
        analytics_service: StudioAnalytics | None = None,
        response_language: str = "ko",
    ):
        super().__init__(llm, response_language=response_language)
        self.policy_engine = policy_engine or PolicyEngine()
        self.analytics = analytics_service or get_studio_analytics()

    def _extract_keyword_flags(self, vectors: List[Dict[str, Any]]) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        counts = {key: 0 for key in _SUSPICIOUS_KEYWORDS}
        flagged_docs: List[Dict[str, Any]] = []
        for doc in vectors:
            content = (doc.get("content") or "").lower()
            hits = []
            for label, keywords in _SUSPICIOUS_KEYWORDS.items():
                if any(word in content for word in keywords):
                    counts[label] += 1
                    hits.extend([word for word in keywords if word in content])
            if hits:
                flagged_docs.append(
                    {
                        "id": doc.get("id"),
                        "content": (doc.get("content") or "")[:200],
                        "score": doc.get("score"),
                        "metadata": doc.get("metadata", {}),
                        "hits": sorted(set(hits)),
                    }
                )
        return counts, flagged_docs[:3]

    def _analytics_snapshot(self, studio_id: str | None) -> Dict[str, Any]:
        if not studio_id:
            return {}
        try:
            return self.analytics.compute_kpis(studio_id)
        except Exception as err:  # pragma: no cover - analytics guardrail
            return {"error": str(err)}

    def _score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        vectors: List[Dict[str, Any]] = context.get("vector", [])
        graph_hits: List[Dict[str, Any]] = context.get("graph", [])
        neo4j_hits: List[Dict[str, Any]] = context.get("neo4j", [])
        keyword_counts, flagged_docs = self._extract_keyword_flags(vectors)
        studio_id = context.get("meta", {}).get("studio_id")
        analytics_snapshot = self._analytics_snapshot(studio_id)
        knowledge_refs = context.get("knowledge") or []
        financials = analytics_snapshot.get("financials", {}) if isinstance(analytics_snapshot, dict) else {}
        gross = financials.get("gross_revenue") or 0.0
        refund_ratio = 0.0
        if gross:
            refund_ratio = (financials.get("refunds") or 0.0) / gross
        attendance = analytics_snapshot.get("attendance", {}) if isinstance(analytics_snapshot, dict) else {}
        settlements = analytics_snapshot.get("settlements", {}) if isinstance(analytics_snapshot, dict) else {}
        state = {
            "refund_ratio": refund_ratio,
            "keyword_counts": keyword_counts,
            "graph_hits": len(graph_hits),
            "neo4j_hits": len(neo4j_hits),
            "attendance_rate": attendance.get("attendance_rate"),
            "avg_sessions_per_member": attendance.get("avg_sessions_per_member"),
            "avg_payout_lag_days": settlements.get("avg_payout_lag_days"),
        }
        policy_hits = self.policy_engine.evaluate(state)
        signals = [hit["id"] for hit in policy_hits]
        # fallback to legacy heuristics if no policy triggered
        if not signals:
            if keyword_counts.get("refund"):
                signals.append("refund_pressure")
            if len(graph_hits) > 120:
                signals.append("ontology_complex_relation")
        risk_score = 0.15 + 0.15 * len(signals)
        if keyword_counts.get("decline"):
            risk_score += 0.1
        risk_score = min(1.0, round(risk_score, 2)) if signals else 0.1
        evidence = {
            "keyword_counts": keyword_counts,
            "vector_flags": flagged_docs,
            "graph_hits": len(graph_hits),
            "neo4j_hits": len(neo4j_hits),
            "analytics": analytics_snapshot,
            "knowledge_refs": knowledge_refs[:3],
        }
        details = {**context.get("meta", {}), "policy_count": len(policy_hits)}
        return {
            "risk_score": risk_score,
            "signals": signals or ["stable"],
            "details": details,
            "policies": policy_hits,
            "evidence": evidence,
            "knowledge_refs": knowledge_refs[:3],
        }

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        scored = self._score(context)
        narrative = self._llm_or_stub(
            "�ֿ� ���� �ñ׳ΰ� ��ȭ ����� �ѱ���� �����ϼ���.",
            {**context, **scored},
        )
        return {**scored, "narrative": narrative}
