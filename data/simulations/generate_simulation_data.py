#!/usr/bin/env python
"""Generate upgraded LOP simulation data aligned with the rebuilt ontology."""
from __future__ import annotations

import csv
import datetime as dt
import random
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR.parent / "samples"
OUTPUT_PROVIDER = BASE_DIR / "provider_metrics.csv"
OUTPUT_OPERATOR = BASE_DIR / "operator_dashboard.csv"
OUTPUT_CUSTOMER = BASE_DIR / "customer_insights.csv"
OUTPUT_TTL = BASE_DIR.parent / "ontology" / "datasets" / "provider_metrics.ttl"

RNG = random.Random(20251202)
PROVIDER_WEEKS = 12
OPERATOR_WEEKS = 12
CUSTOMERS_PER_STUDIO = 20

ANOMALY_TAGS = ["OptInDrop", "WatchDrift", "SettlementDelay", "DeviceOutage", "ProgramChurn"]
REMEDIATIONS = ["DeployFieldTrainer", "HealthKitCampaign", "CreditAdjustment", "AuditEngagementFlow", "RefreshCreative"]
CUSTOMER_ACTIONS = ["UpgradeOffer", "RetentionCall", "IssueCredit", "SurveyPush"]
SEGMENTS = ["Athlete", "Rehab", "Sleeper", "BusyPro"]
INDICATORS = ["ENG-MAU", "ENG-RET", "HK-OPT", "KPI-ADH"]


def load_studios() -> List[Dict[str, str]]:
    path = SAMPLES_DIR / "studios.csv"
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: List[Dict[str, str]] = []
        for row in reader:
            normalized = {key.lstrip("\ufeff"): value for key, value in row.items()}
            rows.append(normalized)
        return rows


def simulate_provider_metrics(studios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    base_week = dt.date(2025, 11, 17)
    for studio in studios:
        studio_id = studio["studio_id"]
        program_id = studio["program_id"]
        agreement_id = studio["agreement_id"]
        for week in range(PROVIDER_WEEKS):
            week_start = base_week - dt.timedelta(days=7 * week)
            avg_sessions = RNG.randint(70, 160)
            new_members = RNG.randint(6, 25)
            revenue = RNG.randint(60_000_000, 210_000_000)
            healthkit = round(RNG.uniform(0.65, 0.97), 3)
            goal_completion = round(RNG.uniform(0.55, 0.95), 3)
            engagement = round(RNG.uniform(0.6, 0.95), 3)
            rows.append(
                {
                    "week_start": week_start.isoformat(),
                    "studio_id": studio_id,
                    "program_id": program_id,
                    "agreement_id": agreement_id,
                    "avg_daily_sessions": str(avg_sessions),
                    "new_members": str(new_members),
                    "weekly_revenue_krw": str(revenue),
                    "healthkit_opt_in": f"{healthkit:.3f}",
                    "goal_completion": f"{goal_completion:.3f}",
                    "engagement_score": f"{engagement:.3f}",
                    "risk_events": str(RNG.randint(0, 4)),
                    "indicator_code": RNG.choice(INDICATORS),
                    "anomaly_tag": RNG.choice(ANOMALY_TAGS),
                    "recommended_action": RNG.choice(REMEDIATIONS),
                }
            )
    return rows


def simulate_operator_dashboard() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    base_week = dt.date(2025, 11, 17)
    for week in range(OPERATOR_WEEKS):
        week_start = base_week - dt.timedelta(days=7 * week)
        rows.append(
            {
                "week_start": week_start.isoformat(),
                "activation_rate": f"{RNG.uniform(0.75, 0.96):.3f}",
                "settlement_success_rate": f"{RNG.uniform(0.91, 0.99):.3f}",
                "healthkit_opt_in_rate": f"{RNG.uniform(0.68, 0.95):.3f}",
                "loan_balance_krw": str(RNG.randint(55_000_000, 210_000_000)),
                "open_investigations": str(RNG.randint(0, 5)),
                "policy_focus": RNG.choice(["Engagement", "Compliance", "Risk", "Growth"]),
                "new_program_launches": str(RNG.randint(0, 4)),
            }
        )
    return rows


def simulate_customer_insights(studios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for studio in studios:
        studio_id = studio["studio_id"]
        program_id = studio["program_id"]
        for idx in range(CUSTOMERS_PER_STUDIO):
            member_id = f"MEM-{studio_id}-{idx+1:02d}"
            rows.append(
                {
                    "member_id": member_id,
                    "studio_id": studio_id,
                    "program_id": program_id,
                    "segment": RNG.choice(SEGMENTS),
                    "engagement_score": f"{RNG.uniform(0.55, 0.97):.2f}",
                    "attendance_ratio": f"{RNG.uniform(0.5, 0.95):.2f}",
                    "healthkit_opt_in": RNG.choice(["true", "false"]),
                    "goal_completion": f"{RNG.uniform(0.45, 0.95):.2f}",
                    "average_bpm": str(RNG.randint(60, 115)),
                    "recommended_offer": RNG.choice(CUSTOMER_ACTIONS),
                }
            )
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_ttl(rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    lines = [
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix lop: <https://lop.apple.com/ontology/lifestyle/core/> .",
        "@prefix lopsim: <https://lop.apple.com/ontology/lifestyle/sim/> .",
        "",
        "lopsim:ProviderMetric a owl:Class .",
        "lopsim:studio a owl:ObjectProperty .",
        "lopsim:program a owl:ObjectProperty .",
        "lopsim:agreement a owl:ObjectProperty .",
        "lopsim:weekStart a owl:DatatypeProperty .",
        "lopsim:avgDailySessions a owl:DatatypeProperty .",
        "lopsim:newMembers a owl:DatatypeProperty .",
        "lopsim:weeklyRevenueKRW a owl:DatatypeProperty .",
        "lopsim:healthkitOptIn a owl:DatatypeProperty .",
        "lopsim:goalCompletion a owl:DatatypeProperty .",
        "lopsim:engagementScore a owl:DatatypeProperty .",
        "lopsim:riskEvents a owl:DatatypeProperty .",
        "lopsim:indicatorCode a owl:DatatypeProperty .",
        "lopsim:anomalyTag a owl:DatatypeProperty .",
        "lopsim:recommendedAction a owl:DatatypeProperty .",
        "",
    ]
    for row in rows:
        identifier = f"lopsim:Metric-{row['studio_id']}-{row['week_start']}"
        lines.extend(
            [
                f"{identifier} a lopsim:ProviderMetric ;",
                f"    lopsim:studio lop:{row['studio_id']} ;",
                f"    lopsim:program lop:{row['program_id']} ;",
                f"    lopsim:agreement lop:{row['agreement_id']} ;",
                f"    lopsim:weekStart \"{row['week_start']}\"^^xsd:date ;",
                f"    lopsim:avgDailySessions \"{row['avg_daily_sessions']}\"^^xsd:integer ;",
                f"    lopsim:newMembers \"{row['new_members']}\"^^xsd:integer ;",
                f"    lopsim:weeklyRevenueKRW \"{row['weekly_revenue_krw']}\"^^xsd:integer ;",
                f"    lopsim:healthkitOptIn \"{row['healthkit_opt_in']}\"^^xsd:decimal ;",
                f"    lopsim:goalCompletion \"{row['goal_completion']}\"^^xsd:decimal ;",
                f"    lopsim:engagementScore \"{row['engagement_score']}\"^^xsd:decimal ;",
                f"    lopsim:riskEvents \"{row['risk_events']}\"^^xsd:integer ;",
                f"    lopsim:indicatorCode \"{row['indicator_code']}\" ;",
                f"    lopsim:anomalyTag \"{row['anomaly_tag']}\" ;",
                f"    lopsim:recommendedAction \"{row['recommended_action']}\" .",
                "",
            ]
        )
    OUTPUT_TTL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TTL.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    studios = load_studios()
    provider_rows = simulate_provider_metrics(studios)
    operator_rows = simulate_operator_dashboard()
    customer_rows = simulate_customer_insights(studios)

    write_csv(OUTPUT_PROVIDER, provider_rows)
    write_csv(OUTPUT_OPERATOR, operator_rows)
    write_csv(OUTPUT_CUSTOMER, customer_rows)
    write_ttl(provider_rows)

    print(f"Provider rows: {len(provider_rows)}")
    print(f"Operator rows: {len(operator_rows)}")
    print(f"Customer rows: {len(customer_rows)}")
    print(f"TTL written to {OUTPUT_TTL}")


if __name__ == "__main__":
    main()
