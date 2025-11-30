"""Skill registry that tracks agent metadata and execution traces."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillDefinition:
    name: str
    description: str
    owner: str = "system"
    inputs: Optional[List[str]] = None
    outputs: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SkillRegistry:
    """In-memory registry that records skill definitions and run events."""

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._events: List[Dict[str, Any]] = []
        self._run_index: Dict[str, int] = {}
        self._counter = 0

    def register(self, definition: SkillDefinition) -> None:
        self._skills[definition.name] = definition

    def start_run(self, skill_name: str, payload: Optional[Dict[str, Any]] = None) -> str:
        self._counter += 1
        run_id = f"{skill_name}-{self._counter}"
        event = {
            "run_id": run_id,
            "skill": skill_name,
            "status": "started",
            "started_at": self._now(),
            "input": self._summarize(payload),
        }
        self._events.append(event)
        self._run_index[run_id] = len(self._events) - 1
        return run_id

    def end_run(
        self,
        run_id: str,
        *,
        status: str = "completed",
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        latency_s: Optional[float] = None,
    ) -> None:
        idx = self._run_index.get(run_id)
        if idx is None:
            return
        event = self._events[idx]
        event.update(
            {
                "status": status,
                "ended_at": self._now(),
                "output": self._summarize(output),
                "error": error,
            }
        )
        if latency_s is not None:
            event["latency_s"] = round(latency_s, 3)

    def export_trace(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @staticmethod
    def _summarize(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not payload or not isinstance(payload, dict):
            return payload
        summary: Dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                summary[key] = None
                continue
            if isinstance(value, (str, int, float, bool)):
                summary[key] = value if not isinstance(value, str) else value[:160]
            elif isinstance(value, dict):
                summary[key] = {k: value[k] for k in list(value.keys())[:3]}
            elif isinstance(value, list):
                summary[key] = value[:3]
            else:
                summary[key] = str(value)[:120]
        return summary

    @staticmethod
    def _now() -> float:
        return round(time.time(), 3)


__all__ = ["SkillRegistry", "SkillDefinition"]
