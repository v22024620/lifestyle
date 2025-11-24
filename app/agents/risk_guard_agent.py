"""Risk guard agent detecting anomalies and chargeback signals."""
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class RiskGuardAgent(BaseAgent):
    """Identify wellness risk signals from graph/vector context."""

    def _score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        signals: List[str] = []
        vectors: List[Dict[str, Any]] = context.get("vector", [])
        neo4j_hits: List[Dict[str, Any]] = context.get("neo4j", [])
        graph_hits: List[Dict[str, Any]] = context.get("graph", [])

        for doc in vectors:
            content = (doc.get("content") or "").lower()
            if any(word in content for word in ["chargeback", "refund", "dispute"]):
                signals.append("refund_pressure")
            if any(word in content for word in ["decline", "fraud", "blocked"]):
                signals.append("payment_decline")
            if "missed" in content or "injury" in content:
                signals.append("session_health_risk")
        if neo4j_hits:
            signals.append("graph_anomaly_suspected")
        # FIBO 기반 온톨로지는 기본적으로 triple 수가 많으므로 경고 한계를 완화한다.
        if len(graph_hits) > 120:
            signals.append("ontology_complex_relation")

        signals = sorted(set(signals))
        risk_score = min(1.0, 0.2 + 0.15 * len(signals)) if signals else 0.1
        return {"risk_score": round(risk_score, 2), "signals": signals or ["stable"], "details": context.get("meta", {})}

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        scored = self._score(context)
        narrative = self._llm_or_stub(
            "주요 위험 시그널과 완화 방안을 한국어로 설명하세요.",
            {**context, **scored},
        )
        return {**scored, "narrative": narrative}
