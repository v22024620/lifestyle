#!/usr/bin/env python
"""Generate enriched LOP simulation data for provider/operator/customer roles."""
from __future__ import annotations

import csv
import datetime as dt
import math
import random
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = BASE_DIR.parent / "samples"
OUTPUT_PROVIDER = BASE_DIR / "provider_metrics.csv"
OUTPUT_OPERATOR = BASE_DIR / "operator_dashboard.csv"
OUTPUT_CUSTOMER = BASE_DIR / "customer_insights.csv"
OUTPUT_TTL = BASE_DIR.parent / "ontology" / "datasets" / "provider_metrics.ttl"
RNG = random.Random(20251122)

PROVIDER_WEEKS = 20
OPERATOR_WEEKS = 12
CUSTOMERS_PER_STUDIO = 25

MODALITY_CONFIG: Dict[str, Dict[str, float]] = {
    "PersonalTraining": {"session": 1.1, "revenue": 1.2, "risk": 0.8},
    "Rehab&Stretch": {"session": 0.9, "revenue": 1.1, "risk": 1.1},
    "Pilates": {"session": 1.0, "revenue": 1.0, "risk": 0.7},
    "Boxing/Conditioning": {"session": 1.2, "revenue": 1.0, "risk": 1.0},
    "PhysicalTherapy": {"session": 0.95, "revenue": 1.15, "risk": 1.2},
    "HIIT": {"session": 1.3, "revenue": 1.05, "risk": 1.1},
    "Yoga": {"session": 1.0, "revenue": 0.9, "risk": 0.6},
    "Cycle": {"session": 1.15, "revenue": 1.05, "risk": 0.9},
    "Dance": {"session": 1.05, "revenue": 0.95, "risk": 0.8},
    "MobilityLab": {"session": 0.85, "revenue": 1.0, "risk": 1.0},
}

EXTRA_STUDIOS = [
    {"studio_id": "SBUND06", "name": "한강 HIIT 포드", "category": "WellnessStudio", "city": "Seoul", "modality": "HIIT", "signature_program": "한강 HIIT Sprint", "target_focus": "Cardio", "plan_type": "VARIABLE", "billing_model": "Usage"},
    {"studio_id": "SNOW07", "name": "설악 리커버리 돔", "category": "WellnessStudio", "city": "Gangwon", "modality": "Rehab&Stretch", "signature_program": "등산 회복 플랜", "target_focus": "Recovery", "plan_type": "MIXED", "billing_model": "Subscription"},
    {"studio_id": "SBUS08", "name": "부산 바다 사이클", "category": "WellnessStudio", "city": "Busan", "modality": "Cycle", "signature_program": "마리나 파워라이드", "target_focus": "Endurance", "plan_type": "FIXED", "billing_model": "Monthly"},
    {"studio_id": "SDJE09", "name": "제주 브레스 요가", "category": "WellnessStudio", "city": "Jeju", "modality": "Yoga", "signature_program": "힐링 비치 요가", "target_focus": "Mindfulness", "plan_type": "MIXED", "billing_model": "Subscription"},
    {"studio_id": "SINC10", "name": "인천 플로우 모빌리티", "category": "WellnessStudio", "city": "Incheon", "modality": "MobilityLab", "signature_program": "도심 릴리즈", "target_focus": "JointCare", "plan_type": "VARIABLE", "billing_model": "Usage"},
    {"studio_id": "SSUW11", "name": "수원 트랙 스프린트", "category": "WellnessStudio", "city": "Suwon", "modality": "HIIT", "signature_program": "트랙 컨디셔닝", "target_focus": "Speed", "plan_type": "FIXED", "billing_model": "Term"},
    {"studio_id": "SDAE12", "name": "대전 슬로우 필라테스", "category": "WellnessStudio", "city": "Daejeon", "modality": "Pilates", "signature_program": "슬로우 컨트롤", "target_focus": "Posture", "plan_type": "MIXED", "billing_model": "Subscription"},
    {"studio_id": "SGIM13", "name": "김포 펀치팩토리", "category": "WellnessStudio", "city": "Gimpo", "modality": "Boxing/Conditioning", "signature_program": "에어로 복싱", "target_focus": "Cardio", "plan_type": "VARIABLE", "billing_model": "Usage"},
    {"studio_id": "SSCH14", "name": "서초 메타 요가", "category": "WellnessStudio", "city": "Seoul", "modality": "Yoga", "signature_program": "메타 밸런스", "target_focus": "Balance", "plan_type": "FIXED", "billing_model": "Monthly"},
    {"studio_id": "SULS15", "name": "울산 모션랩", "category": "WellnessStudio", "city": "Ulsan", "modality": "MobilityLab", "signature_program": "모션 리부트", "target_focus": "Rehab", "plan_type": "MIXED", "billing_model": "Subscription"},
    {"studio_id": "SCHE16", "name": "청주 러닝 로지", "category": "WellnessStudio", "city": "Cheongju", "modality": "HIIT", "signature_program": "러닝 파워믹스", "target_focus": "Cardio", "plan_type": "VARIABLE", "billing_model": "Usage"},
    {"studio_id": "SGOY17", "name": "고양 웨이트 아틀리에", "category": "WellnessStudio", "city": "Goyang", "modality": "PersonalTraining", "signature_program": "스트렝스 엣지", "target_focus": "Strength", "plan_type": "FIXED", "billing_model": "Monthly"},
    {"studio_id": "SJEJ18", "name": "전주 댄스 리폼", "category": "WellnessStudio", "city": "Jeonju", "modality": "Dance", "signature_program": "댄스 리폼 플로우", "target_focus": "Agility", "plan_type": "MIXED", "billing_model": "Subscription"},
    {"studio_id": "SGNA19", "name": "강릉 트레일 피트", "category": "WellnessStudio", "city": "Gangneung", "modality": "Cycle", "signature_program": "트레일 피트", "target_focus": "Endurance", "plan_type": "VARIABLE", "billing_model": "Usage"},
    {"studio_id": "SANS20", "name": "안산 리폼드", "category": "WellnessStudio", "city": "Ansan", "modality": "PersonalTraining", "signature_program": "퍼포먼스 스택", "target_focus": "Strength", "plan_type": "FIXED", "billing_model": "Term"},
]

ANOMALY_TAGS = ["정상", "과다환불", "세션급감", "장비고장 증가", "HealthKit 하락"]
RECOMMENDATIONS = ["광고 쿠폰 발행", "트레이너 교육 강화", "정책 리뷰", "장비 교체", "프로모션 확장"]
CUSTOMER_ACTIONS = ["격려 메시지", "코칭 연결", "휴식 권장", "챌린지 제안"]
SEGMENTS = ["액티브워처", "회복중", "신규회원", "하이리스크"]


def load_studios() -> List[Dict[str, str]]:
    path = SAMPLES_DIR / "studios.csv"
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        cleaned: List[Dict[str, str]] = []
        for raw in reader:
            cleaned.append({(k or "").strip().replace("\ufeff", ""): v for k, v in raw.items()})
    cleaned.extend(EXTRA_STUDIOS)
    return cleaned


def _studio_id(row: Dict[str, str]) -> str:
    for key in ("studio_id", "studioid", "id"):
        value = row.get(key)
        if value:
            return value
    raise KeyError("studio identifier not found")


def _trend_factor(offset: int) -> float:
    return 1 + 0.03 * math.sin(offset / 2)


def simulate_provider_metrics(studios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    base_week = dt.date.today().replace(day=1)
    rows: List[Dict[str, str]] = []
    for offset in range(PROVIDER_WEEKS):
        week_start = base_week - dt.timedelta(days=7 * offset)
        trend = _trend_factor(offset)
        for studio in studios:
            studio_id = _studio_id(studio)
            config = MODALITY_CONFIG.get(studio.get("modality", ""), {"session": 1.0, "revenue": 1.0, "risk": 1.0})
            avg_sessions = max(25, int(RNG.gauss(70 * config["session"] * trend, 12)))
            new_members = max(4, int(RNG.gauss(15 * config["session"], 4)))
            revenue = max(200_000, int(RNG.gauss(900_000 * config["revenue"] * trend, 150_000)))
            cost = int(revenue * RNG.uniform(0.45, 0.78))
            refund_rate = max(0.002, round(RNG.uniform(0.004, 0.08) * config["risk"], 3))
            healthkit_sync = max(0.3, min(0.99, round(RNG.uniform(0.55, 0.97) - 0.05 * (config["risk"] - 1), 2)))
            goal_completion = round(RNG.uniform(0.5, 0.95), 2)
            risk_events = max(0, int(RNG.gauss(config["risk"], 1)))
            equipment_faults = max(0, RNG.randint(0, int(round(config["risk"] + 0.5))))
            anomaly_tag = RNG.choice(ANOMALY_TAGS)
            recommendation = RNG.choice(RECOMMENDATIONS)
            rows.append({
                "스튜디오ID": studio_id,
                "주차시작일": week_start.isoformat(),
                "일평균세션": str(avg_sessions),
                "신규회원수": str(new_members),
                "주간매출KRW": str(revenue),
                "예상원가KRW": str(cost),
                "환불율": f"{refund_rate:.3f}",
                "리스크이벤트수": str(risk_events),
                "헬스킷동기화율": f"{healthkit_sync:.2f}",
                "건강목표달성율": f"{goal_completion:.2f}",
                "장비고장건수": str(equipment_faults),
                "이상징후라벨": anomaly_tag,
                "권장조치": recommendation,
                "대표프로그램": studio.get("signature_program", ""),
            })
    return rows


def simulate_operator_dashboard(studios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    week_start = dt.date.today().replace(day=1)
    rows: List[Dict[str, str]] = []
    for week_offset in range(OPERATOR_WEEKS):
        window = week_start - dt.timedelta(days=7 * week_offset)
        activation = round(RNG.uniform(0.72, 0.96), 3)
        settlement_success = round(RNG.uniform(0.9, 0.99), 3)
        investigations = RNG.randint(0, 5)
        policy_focus = RNG.choice(["환불", "장비", "가격", "교육", "프로모션"])
        rows.append({
            "주차시작일": window.isoformat(),
            "글로벌활성화율": f"{activation:.3f}",
            "정산성공율": f"{settlement_success:.3f}",
            "헬스킷OptIn율": f"{RNG.uniform(0.65, 0.94):.3f}",
            "파트너NPS": str(RNG.randint(40, 80)),
            "오픈인시던트": str(investigations),
            "정책포커스": policy_focus,
            "평균Loan잔액KRW": str(RNG.randint(50_000_000, 200_000_000)),
            "신규프로그램수": str(RNG.randint(1, 6)),
        })
    return rows


def simulate_customer_insights(studios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for studio in studios:
        studio_id = _studio_id(studio)
        for idx in range(CUSTOMERS_PER_STUDIO):
            member_id = f"MEM-{studio_id}-{idx+1:02d}"
            engagement = round(RNG.uniform(0.55, 0.97), 2)
            attendance = round(RNG.uniform(0.5, 0.95), 2)
            goal = round(RNG.uniform(0.45, 0.95), 2)
            health_opt = RNG.choice(["동의", "비동의"])
            rows.append({
                "회원ID": member_id,
                "스튜디오ID": studio_id,
                "프로그램": studio.get("signature_program", ""),
                "세그먼트": RNG.choice(SEGMENTS),
                "참여점수": f"{engagement:.2f}",
                "출석률": f"{attendance:.2f}",
                "헬스킷동의": health_opt,
                "목표달성도": f"{goal:.2f}",
                "평균심박": str(RNG.randint(60, 110)),
                "추천액션": RNG.choice(CUSTOMER_ACTIONS),
            })
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
    lines = [
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix lop-core: <https://lop.com/fibo/lifestyle/core/> .",
        "@prefix lop-sim: <https://lop.com/fibo/lifestyle/sim/> .",
        "",
        "lop-sim:ProviderMetric a owl:Class .",
        "lop-sim:studio a owl:ObjectProperty .",
        "lop-sim:weekStart a owl:DatatypeProperty .",
        "lop-sim:avgDailySessions a owl:DatatypeProperty .",
        "lop-sim:newMembers a owl:DatatypeProperty .",
        "lop-sim:weeklyRevenueKRW a owl:DatatypeProperty .",
        "lop-sim:estimatedCostKRW a owl:DatatypeProperty .",
        "lop-sim:refundRate a owl:DatatypeProperty .",
        "lop-sim:riskEvents a owl:DatatypeProperty .",
        "lop-sim:healthkitSync a owl:DatatypeProperty .",
        "lop-sim:goalCompletion a owl:DatatypeProperty .",
        "lop-sim:equipmentIncidents a owl:DatatypeProperty .",
        "lop-sim:anomalyTag a owl:DatatypeProperty .",
        "lop-sim:recommendedAction a owl:DatatypeProperty .",
        "",
    ]
    for row in rows:
        studio_id = row["스튜디오ID"]
        week_start = row["주차시작일"]
        ident = f"lop-sim:ProviderMetric-{studio_id}-{week_start}"
        lines.append(f"{ident} a lop-sim:ProviderMetric ;")
        lines.append(f"    lop-sim:studio lop-core:{studio_id} ;")
        lines.append(f"    lop-sim:weekStart \"{week_start}\"^^xsd:date ;")
        lines.append(f"    lop-sim:avgDailySessions \"{row['일평균세션']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:newMembers \"{row['신규회원수']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:weeklyRevenueKRW \"{row['주간매출KRW']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:estimatedCostKRW \"{row['예상원가KRW']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:refundRate \"{row['환불율']}\"^^xsd:decimal ;")
        lines.append(f"    lop-sim:riskEvents \"{row['리스크이벤트수']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:healthkitSync \"{row['헬스킷동기화율']}\"^^xsd:decimal ;")
        lines.append(f"    lop-sim:goalCompletion \"{row['건강목표달성율']}\"^^xsd:decimal ;")
        lines.append(f"    lop-sim:equipmentIncidents \"{row['장비고장건수']}\"^^xsd:integer ;")
        lines.append(f"    lop-sim:anomalyTag \"{row['이상징후라벨']}\" ;")
        lines.append(f"    lop-sim:recommendedAction \"{row['권장조치']}\" .")
        lines.append("")
    OUTPUT_TTL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_TTL.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    studios = load_studios()
    provider_rows = simulate_provider_metrics(studios)
    operator_rows = simulate_operator_dashboard(studios)
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
