"""Report model for responses."""
from typing import Any, Dict
from pydantic import BaseModel


class Report(BaseModel):
    studio_id: str
    insight: Dict[str, Any]
    risk: Dict[str, Any]
    recommendation: Dict[str, Any]
    strategy_framework: Dict[str, Any]
    explanation: Dict[str, Any]
