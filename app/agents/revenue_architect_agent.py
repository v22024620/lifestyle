"""Revenue architect agent proposing growth and fee plan actions."""
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class RevenueArchitectAgent(BaseAgent):
    """Generate prioritized recommendations for wellness studios."""

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        studio_id = context.get("meta", {}).get("studio_id")
        recs: List[Dict[str, Any]] = []
        vectors = context.get("vector", [])
        if vectors:
            for doc in vectors[:3]:
                recs.append({
                    "title": "세션 구성 최적화",
                    "action": f"최근 신호: {doc.get('content','')[:120]} · 세션/패키지 구성을 재배열하세요.",
                    "confidence": 0.62,
                })
        if not recs:
            recs.append({
                "title": "크로스 프로모션",
                "action": "회복/컨디셔닝 패키지를 묶어 ARPPU를 높이세요.",
                "confidence": 0.55,
            })
        recs.append({
            "title": "리스크 연동 수수료",
            "action": "환불·부상 시그널 상승 시 예치금/보험 옵션을 제안하세요.",
            "confidence": 0.58,
        })
        narrative = self._llm_or_stub("웰니스 스튜디오의 다음 액션을 제안하세요.", context)
        return {"studio_id": studio_id, "items": recs, "narrative": narrative}
