"""Simple policy-based evaluator for the risk guard agent."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


class PolicyEngine:
    """Evaluates predefined guardrail policies using aggregated state."""

    def __init__(self, policies: List[Dict[str, Any]] | None = None):
        self.policies = policies or self._default_policies()

    def evaluate(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return triggered policy hits with supporting evidence."""
        hits: List[Dict[str, Any]] = []
        for policy in self.policies:
            triggered, rationale, evidence = policy["check"](state)
            if triggered:
                hits.append(
                    {
                        "id": policy["id"],
                        "title": policy["title"],
                        "severity": policy["severity"],
                        "rationale": rationale,
                        "evidence": evidence,
                    }
                )
        return hits

    def _default_policies(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "policy_refund_pressure",
                "title": "환불·차지백 급증",
                "severity": "high",
                "check": self._check_refund_pressure,
            },
            {
                "id": "policy_payment_decline",
                "title": "결제 거절/사기 징후",
                "severity": "medium",
                "check": self._check_payment_decline,
            },
            {
                "id": "policy_graph_density",
                "title": "비정상 그래프 연관도",
                "severity": "medium",
                "check": self._check_graph_density,
            },
            {
                "id": "policy_engagement_drop",
                "title": "출석률/세션 참여 저하",
                "severity": "medium",
                "check": self._check_engagement_drop,
            },
            {
                "id": "policy_payout_delay",
                "title": "정산 지연 리스크",
                "severity": "low",
                "check": self._check_payout_delay,
            },
        ]

    def _check_refund_pressure(self, state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        ratio = state.get("refund_ratio", 0.0) or 0.0
        keywords = state.get("keyword_counts", {})
        refund_mentions = keywords.get("refund", 0) + keywords.get("chargeback", 0)
        triggered = ratio > 0.12 or refund_mentions >= 2
        rationale = f"환불비율 {ratio:.2%}, 키워드 감지 {refund_mentions}건"
        evidence = {"refund_ratio": ratio, "refund_mentions": refund_mentions}
        return triggered, rationale, evidence

    def _check_payment_decline(self, state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        keywords = state.get("keyword_counts", {})
        decline_hits = keywords.get("decline", 0) + keywords.get("fraud", 0)
        neo4j_rel = state.get("neo4j_hits", 0)
        triggered = decline_hits >= 1 or neo4j_rel > 0
        rationale = f"결제 경고 키워드 {decline_hits}건, Neo4j 연관 {neo4j_rel}건"
        evidence = {"decline_keywords": decline_hits, "neo4j_relations": neo4j_rel}
        return triggered, rationale, evidence

    def _check_graph_density(self, state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        graph_hits = state.get("graph_hits", 0)
        triggered = graph_hits > 120
        rationale = f"그래프 triple {graph_hits}건"
        evidence = {"graph_hits": graph_hits}
        return triggered, rationale, evidence

    def _check_engagement_drop(self, state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        attendance = state.get("attendance_rate")
        avg_sessions = state.get("avg_sessions_per_member")
        triggered = attendance is not None and attendance < 0.7
        triggered = triggered or (avg_sessions is not None and avg_sessions < 1.0)
        rationale = f"출석률 {attendance}, 1인당 세션 {avg_sessions}"
        evidence = {"attendance_rate": attendance, "avg_sessions_per_member": avg_sessions}
        return triggered, rationale, evidence

    def _check_payout_delay(self, state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        payout_lag = state.get("avg_payout_lag_days")
        triggered = payout_lag is not None and payout_lag > 10
        rationale = f"평균 정산 지연 {payout_lag}일"
        evidence = {"avg_payout_lag_days": payout_lag}
        return triggered, rationale, evidence
