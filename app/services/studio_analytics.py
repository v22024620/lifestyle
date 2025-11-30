"""Utility helpers to compute studio KPI snapshots and fee-plan simulations."""
from __future__ import annotations

import csv
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "samples"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d/%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value.split("/")[0], fmt)
                return parsed
            except ValueError:
                continue
    return None


@dataclass(frozen=True)
class PeriodWindow:
    """Normalized time window used across KPIs/simulations."""

    start: Optional[datetime]
    end: Optional[datetime]
    raw: Dict[str, Any]

    def contains(self, value: Optional[datetime]) -> bool:
        if value is None:
            return True
        if self.start and value < self.start:
            return False
        if self.end and value > self.end:
            return False
        return True

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
        }


class StudioAnalytics:
    """Loads sample datasets and derives studio-level analytics."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or DEFAULT_DATA_DIR)
        if not self.data_dir.is_absolute():
            self.data_dir = PROJECT_ROOT / self.data_dir
        self.transactions = self._load_csv("transactions.csv")
        self.sessions = self._load_csv("sessions.csv")
        self.settlements = self._load_csv("settlements.csv")
        self.studios = {row.get("studio_id"): row for row in self._load_csv("studios.csv")}
        self.plan_stats = self._build_plan_stats()
        self.global_defaults = self.plan_stats.get("__global__", {
            "avg_ticket": 0.0,
            "refund_rate": 0.05,
            "engagement_lift": 1.0,
            "data_points": 0,
        })

    def _load_csv(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / filename
        if not path.exists():
            logger.warning("Sample file %s not found", path)
            return []
        with path.open(encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]

    def derive_window(self, period: Optional[Dict[str, Any]]) -> PeriodWindow:
        period = period or {}
        start = _parse_iso(period.get("from") or period.get("from_") or period.get("start"))
        end = _parse_iso(period.get("to") or period.get("end"))
        return PeriodWindow(start=start, end=end, raw=period)

    def compute_kpis(self, studio_id: str, window: Optional[PeriodWindow] = None) -> Dict[str, Any]:
        window = window or PeriodWindow(start=None, end=None, raw={})
        tx_rows = self._filter_rows(self.transactions, studio_id, "timestamp", window)
        session_rows = self._filter_rows(self.sessions, studio_id, "session_date", window)
        settlement_rows = self._filter_rows(self.settlements, studio_id, "payout_date", window)
        return {
            "studio_id": studio_id,
            "window": window.as_dict(),
            "financials": self._summarize_transactions(tx_rows),
            "attendance": self._summarize_sessions(session_rows, tx_rows),
            "settlements": self._summarize_settlements(settlement_rows),
        }

    def simulate_plan(
        self,
        studio_id: str,
        target_plan: str,
        window: Optional[PeriodWindow] = None,
        baseline: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        window = window or PeriodWindow(start=None, end=None, raw={})
        baseline = baseline or self.compute_kpis(studio_id, window)
        members = baseline.get("financials", {}).get("active_members", 0) or baseline.get("attendance", {}).get("unique_members", 0)
        members = max(members, 1)
        plan_stats = self.plan_stats.get(target_plan) or self.global_defaults
        gross = members * plan_stats["avg_ticket"]
        net = gross * (1 - plan_stats["refund_rate"])
        base_sessions = baseline.get("attendance", {}).get("avg_sessions_per_member") or 0.0
        projected_sessions = base_sessions * plan_stats.get("engagement_lift", 1.0) * members
        payout_days = baseline.get("settlements", {}).get("avg_payout_lag_days")
        comparison_net = baseline.get("financials", {}).get("net_revenue", 0.0)
        delta = net - comparison_net
        return {
            "plan": target_plan,
            "projected_gross_revenue": round(gross, 2),
            "projected_net_revenue": round(net, 2),
            "projected_sessions": round(projected_sessions, 1),
            "assumptions": {
                "members": members,
                "base_sessions_per_member": round(base_sessions, 2),
                "engagement_lift": round(plan_stats.get("engagement_lift", 1.0), 2),
                "refund_rate": round(plan_stats.get("refund_rate", self.global_defaults.get("refund_rate", 0.05)), 3),
                "data_points": plan_stats.get("data_points", 0),
                "avg_ticket": round(plan_stats.get("avg_ticket", 0.0), 2),
                "payout_lag_days": payout_days,
            },
            "delta_vs_baseline": round(delta, 2),
        }

    def _filter_rows(
        self,
        rows: Iterable[Dict[str, Any]],
        studio_id: str,
        date_field: str,
        window: PeriodWindow,
    ) -> List[Dict[str, Any]]:
        filtered: List[Dict[str, Any]] = []
        for row in rows:
            row_studio = row.get("studio_id") or row.get("merchant_id")
            if studio_id and row_studio != studio_id:
                continue
            if window.start or window.end:
                dt = _parse_iso(row.get(date_field) or row.get("period"))
                if not window.contains(dt):
                    continue
            filtered.append(row)
        return filtered

    def _summarize_transactions(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {
                "gross_revenue": 0.0,
                "net_revenue": 0.0,
                "refunds": 0.0,
                "active_members": 0,
                "plan_mix": [],
                "arppu": 0.0,
            }
        positive = 0.0
        refunds = 0.0
        members: Dict[str, int] = defaultdict(int)
        plan_revenue: Counter[str] = Counter()
        first_date: Optional[datetime] = None
        last_date: Optional[datetime] = None
        for row in rows:
            amt = _safe_float(row.get("amount"))
            row_type = (row.get("type") or "").lower()
            plan = (row.get("payment_plan") or "unknown").strip() or "unknown"
            member = row.get("member_id") or ""
            dt = _parse_iso(row.get("timestamp"))
            if dt:
                first_date = min(first_date or dt, dt)
                last_date = max(last_date or dt, dt)
            if amt >= 0:
                positive += amt
                plan_revenue[plan] += amt
            if amt < 0 or row_type in {"refund", "chargeback", "dispute"}:
                refunds += abs(amt)
            if member:
                members[member] += 1
        net = max(positive - refunds, 0.0)
        active_members = len(members) or 1
        repeat_members = len([cnt for cnt in members.values() if cnt > 1])
        plan_mix = [
            {
                "plan": plan,
                "share": round(rev / positive, 3) if positive else 0.0,
                "revenue": round(rev, 2),
            }
            for plan, rev in plan_revenue.most_common(5)
        ]
        return {
            "gross_revenue": round(positive, 2),
            "net_revenue": round(net, 2),
            "refunds": round(refunds, 2),
            "active_members": len(members),
            "repeat_rate": round(repeat_members / active_members, 3) if active_members else 0.0,
            "plan_mix": plan_mix,
            "arppu": round(net / active_members, 2) if active_members else 0.0,
            "period_start": first_date.isoformat() if first_date else None,
            "period_end": last_date.isoformat() if last_date else None,
        }

    def _summarize_sessions(self, sessions: List[Dict[str, Any]], tx_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not sessions:
            active_members = {row.get("member_id") for row in tx_rows if row.get("member_id")}
            return {
                "total": 0,
                "attendance_rate": 0.0,
                "avg_sessions_per_member": 0.0,
                "unique_members": len(active_members),
            }
        total = len(sessions)
        attended = sum(1 for row in sessions if (row.get("attendance_status") or "").lower() == "attended")
        missed = sum(1 for row in sessions if (row.get("attendance_status") or "").lower() == "missed")
        members = {row.get("member_id") for row in sessions if row.get("member_id")}
        avg_sessions = total / max(len(members) or len(tx_rows) or 1, 1)
        return {
            "total": total,
            "attended": attended,
            "missed": missed,
            "attendance_rate": round(attended / total, 3) if total else 0.0,
            "avg_sessions_per_member": round(avg_sessions, 2),
            "unique_members": len(members),
        }

    def _summarize_settlements(self, settlements: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not settlements:
            return {
                "total_payout": 0.0,
                "avg_fee_ratio": 0.0,
                "avg_payout_lag_days": None,
            }
        total_amount = 0.0
        fee_ratios = []
        lags = []
        for row in settlements:
            total_amount += _safe_float(row.get("amount"))
            fee_ratios.append(_safe_float(row.get("fee_ratio")))
            period_field = row.get("period") or ""
            _, _, period_end = period_field.partition("/")
            period_end_dt = _parse_iso(period_end)
            payout_dt = _parse_iso(row.get("payout_date"))
            if period_end_dt and payout_dt:
                lags.append((payout_dt - period_end_dt).days)
        avg_fee = sum(fee_ratios) / len(fee_ratios)
        avg_lag = sum(lags) / len(lags) if lags else None
        return {
            "total_payout": round(total_amount, 2),
            "avg_fee_ratio": round(avg_fee, 3) if fee_ratios else 0.0,
            "avg_payout_lag_days": round(avg_lag, 1) if avg_lag is not None else None,
        }

    def _build_plan_stats(self) -> Dict[str, Dict[str, Any]]:
        aggregates: Dict[str, Dict[str, float]] = defaultdict(lambda: {"positive": 0.0, "refund": 0.0, "count": 0})
        for row in self.transactions:
            plan = (row.get("payment_plan") or "unknown").strip() or "unknown"
            amt = _safe_float(row.get("amount"))
            bucket = aggregates[plan]
            if amt >= 0:
                bucket["positive"] += amt
                bucket["count"] += 1
            else:
                bucket["refund"] += abs(amt)
        totals = sum(bucket["positive"] for bucket in aggregates.values())
        global_count = sum(bucket["count"] for bucket in aggregates.values()) or 1
        stats: Dict[str, Dict[str, Any]] = {}
        for plan, bucket in aggregates.items():
            avg_ticket = bucket["positive"] / bucket["count"] if bucket["count"] else totals / global_count
            refund_rate = bucket["refund"] / bucket["positive"] if bucket["positive"] else 0.05
            engagement_lift = self._engagement_hint(plan)
            stats[plan] = {
                "avg_ticket": avg_ticket,
                "refund_rate": min(max(refund_rate, 0.0), 0.4),
                "engagement_lift": engagement_lift,
                "data_points": int(bucket["count"]),
            }
        stats["__global__"] = {
            "avg_ticket": totals / global_count if global_count else 0.0,
            "refund_rate": sum(bucket["refund"] for bucket in aggregates.values()) / totals if totals else 0.05,
            "engagement_lift": 1.0,
            "data_points": global_count,
        }
        return stats

    @staticmethod
    def _engagement_hint(plan: str) -> float:
        upper = plan.upper()
        if "PREMIUM" in upper or "SIGNATURE" in upper:
            return 1.15
        if "PLUS" in upper or "PRO" in upper:
            return 1.08
        if "BASIC" in upper or "LITE" in upper:
            return 0.92
        return 1.0


@lru_cache(maxsize=1)
def get_studio_analytics() -> StudioAnalytics:
    """Return singleton analytics accessor to avoid repeated file I/O."""
    return StudioAnalytics()
