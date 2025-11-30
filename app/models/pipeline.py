"""Dataclasses describing orchestrator outputs."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PipelineResult:
    """Structured wrapper around multi-agent outputs for a studio."""

    trace_id: str
    insight: Dict[str, Any]
    risk: Dict[str, Any]
    recommendation: Dict[str, Any]
    strategy_framework: Dict[str, Any]
    explanation: Dict[str, Any]
    cached: bool = False
    trace_log: Optional[List[Dict[str, Any]]] = None
    knowledge: Optional[List[Dict[str, Any]]] = None
    workflow: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result into a JSON-serializable dict."""
        return {
            "trace_id": self.trace_id,
            "insight": self.insight,
            "risk": self.risk,
            "recommendation": self.recommendation,
            "strategy_framework": self.strategy_framework,
            "explanation": self.explanation,
            "cached": self.cached,
            "trace_log": self.trace_log,
            "knowledge": self.knowledge,
            "workflow": self.workflow,
        }

    def refresh(self, *, mark_cached: bool) -> "PipelineResult":
        """Return a new instance with a fresh trace id and updated cached flag."""
        return PipelineResult(
            trace_id=str(uuid.uuid4()),
            insight=self.insight,
            risk=self.risk,
            recommendation=self.recommendation,
            strategy_framework=self.strategy_framework,
            explanation=self.explanation,
            cached=mark_cached,
            trace_log=self.trace_log,
            knowledge=self.knowledge,
            workflow=self.workflow,
        )
