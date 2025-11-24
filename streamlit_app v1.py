from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from app.config import get_settings
from app.services.agent_orchestrator import AgentOrchestrator


st.set_page_config(page_title="LOP Dashboard", page_icon="💫", layout="wide")


CUSTOM_CSS = """
<style>
:root {
    --lop-bg: #f5f5f7;
    --lop-card-bg: #ffffff;
    --lop-border: rgba(148, 163, 184, 0.28);
    --lop-shadow: 0 18px 45px rgba(15, 23, 42, 0.04);
    --lop-ink: #0f172a;
}
body, .stApp {
    background-color: var(--lop-bg);
    color: var(--lop-ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
}
.stApp > header {
    background: transparent;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.lop-header { margin-bottom: 1rem; }
.lop-header-title {
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 0.4rem;
    color: #0b1120;
}
.lop-header-subtitle {
    font-size: 1.05rem;
    color: #475467;
    margin-bottom: 1rem;
}
.lop-label-muted {
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
    font-weight: 600;
}
.lop-section-title {
    font-size: 1rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1f2937;
    margin: 1.5rem 0 0.5rem;
    font-weight: 600;
}
.lop-card {
    background: var(--lop-card-bg);
    border-radius: 18px;
    border: 1px solid var(--lop-border);
    box-shadow: var(--lop-shadow);
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.lop-metric {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.2rem 0 0.4rem;
    color: #0f172a;
}
.lop-card-note {
    font-size: 0.9rem;
    color: #64748b;
}
.lop-chip {
    display: inline-flex;
    background: #edf2ff;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    margin: 0.15rem 0.3rem 0 0;
    font-size: 0.78rem;
    color: #0f172a;
}
.lop-json-box {
    background: #0b1120;
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    color: #e2e8f0;
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 0.85rem;
}
.lop-json-box pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
}
.lop-card-list {
    padding-left: 1.1rem;
    color: #0f172a;
}
.lop-card-list li {
    margin-bottom: 0.35rem;
}
.lop-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    background: #ecfeff;
    color: #0e7490;
    font-size: 0.8rem;
    font-weight: 600;
}
.lop-badge-positive { color: #0d9488; }
</style>
"""


def inject_custom_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource
def load_orchestrator() -> AgentOrchestrator:
    settings = get_settings()
    return AgentOrchestrator(settings=settings)


MEMBER_DATA_PATH = Path("data/simulations/customer_insights.csv")
MEMBER_COLUMN_MAP = {
    "회원ID": "member_id",
    "스튜디오ID": "studio_id",
    "프로그램": "program",
    "세그먼트": "segment",
    "참여점수": "participation_score",
    "출석률": "attendance_rate",
    "헬스킷동의": "healthkit_opt_in",
    "목표달성도": "goal_completion",
    "평균심박": "avg_heart_rate",
    "추천액션": "suggested_action",
}
NUMERIC_MEMBER_COLUMNS = [
    "participation_score",
    "attendance_rate",
    "goal_completion",
    "avg_heart_rate",
]

@st.cache_data(show_spinner=False)
def load_member_simulation() -> pd.DataFrame:
    path = MEMBER_DATA_PATH
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8").rename(columns=MEMBER_COLUMN_MAP)
    for column in NUMERIC_MEMBER_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def get_member_snapshot(studio_id: str, member_identifier: str) -> Optional[Dict[str, Any]]:
    df = load_member_simulation()
    if df.empty:
        return None
    studio_mask = df["studio_id"].astype(str).str.lower() == (studio_id or "").lower()
    subset = df[studio_mask]
    if subset.empty:
        return None
    normalized = (member_identifier or "").strip().lower()
    if normalized:
        member_series = subset["member_id"].astype(str).str.lower()
        matches = subset[member_series == normalized]
        if matches.empty:
            matches = subset[member_series.str.contains(normalized, na=False)]
        row = matches.iloc[0] if not matches.empty else subset.iloc[0]
    else:
        row = subset.iloc[0]
    return row.dropna().to_dict()

@st.cache_data(show_spinner=False)
def fetch_pipeline_data(studio_id: str, normalized_query: str) -> Dict[str, Any]:
    orchestrator = load_orchestrator()
    result = orchestrator.run_full_pipeline(
        user_query=normalized_query or None,
        studio_id=studio_id,
    )
    return result.to_dict()


def run_pipeline_with_fallback(studio_id: str, query: str | None) -> Optional[Dict[str, Any]]:
    normalized = (query or "").strip()
    try:
        return fetch_pipeline_data(studio_id, normalized)
    except Exception as exc:
        st.error(f"에이전트 실행 중 오류가 발생했습니다: {exc}")
        return None


def ensure_pipeline_result(state_key: str, studio_id: str, query: str, label: str) -> Optional[Dict[str, Any]]:
    if state_key not in st.session_state:
        st.session_state[state_key] = run_pipeline_with_fallback(studio_id, query)
        st.session_state[f"{state_key}_meta"] = {"label": label, "query": query}
    return st.session_state.get(state_key)


def refresh_pipeline_result(state_key: str, studio_id: str, query: str, label: str) -> Optional[Dict[str, Any]]:
    data = run_pipeline_with_fallback(studio_id, query)
    st.session_state[f"{state_key}_meta"] = {"label": label, "query": query}
    if data is not None:
        st.session_state[state_key] = data
    return st.session_state.get(state_key)


def get_query_meta(state_key: str, fallback_label: str, fallback_query: str) -> Dict[str, str]:
    return st.session_state.get(
        f"{state_key}_meta",
        {"label": fallback_label, "query": fallback_query},
    )


def shorten_query(text: str, limit: int = 160) -> str:
    stripped = (text or "").strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}…"


def format_currency(amount: Optional[float]) -> str:
    if amount is None:
        return "데이터 수집 중"
    return f"₩{amount:,.0f}"


def build_modalities_html(modalities: List[str]) -> str:
    if not modalities:
        return "<span class='lop-card-note'>모달리티 신호 수집 중</span>"
    return "".join(f"<span class='lop-chip'>{html.escape(m)}</span>" for m in modalities)


def render_header(title: str, subtitle: str, badge: Optional[str] = None) -> None:
    badge_html = f"<div class='lop-label-muted'>{html.escape(badge)}</div>" if badge else ""
    st.markdown(
        f"""
        <div class="lop-header">
            {badge_html}
            <div class="lop-header-title">{html.escape(title)}</div>
            <div class="lop-header-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(container, title: str, value: str, detail: Optional[str] = None, extra_html: str = "") -> None:
    value_html = html.escape(value)
    detail_html = f"<div class='lop-card-note'>{html.escape(detail)}</div>" if detail else ""
    container.markdown(
        f"""
        <div class="lop-card">
            <div class="lop-label-muted">{html.escape(title)}</div>
            <div class="lop-metric">{value_html}</div>
            {detail_html}
            {extra_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_text_card(title: str, body: Optional[str], footer: Optional[str] = None) -> None:
    safe_body = html.escape(body) if body else "데이터를 준비 중입니다."
    safe_body = "<br>".join(safe_body.splitlines())
    footer_html = f"<div class='lop-card-note'>{html.escape(footer)}</div>" if footer else ""
    st.markdown(
        f"""
        <div class="lop-card">
            <div class="lop-label-muted">{html.escape(title)}</div>
            <div style="color:#0f172a; font-size:0.95rem; line-height:1.5;">{safe_body}</div>
            {footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_list_card(title: str, lines: List[str]) -> None:
    entries = lines or ["데이터를 수집하는 중입니다."]
    list_html = "".join(f"<li>{html.escape(item)}</li>" for item in entries)
    st.markdown(
        f"""
        <div class="lop-card">
            <div class="lop-label-muted">{html.escape(title)}</div>
            <ul class="lop-card-list">
                {list_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_risk_timeseries(score: Optional[float]) -> pd.DataFrame:
    base = score if score is not None else 0.35
    base = max(0.05, min(0.95, base))
    series = [
        round(max(0.02, base - 0.12), 2),
        round(max(0.04, base - 0.05), 2),
        round(base, 2),
        round(min(0.98, base + 0.04), 2),
    ]
    index = ["-3h", "-2h", "-1h", "지금"]
    return pd.DataFrame({"Risk score": series}, index=index)


def build_program_flow_dataframe(kpis: Dict[str, Any]) -> pd.DataFrame:
    documents = kpis.get("documents_indexed") or 80
    base = max(50, min(95, documents % 120 + 55))
    participation = [base - 6, base - 2, base, base - 3, base + 5]
    retention = [min(99, p + 8) for p in participation]
    index = ["월", "화", "수", "목", "금"]
    return pd.DataFrame(
        {"프로그램 참여도": participation, "구독 유지율": retention},
        index=index,
    )


def build_member_activity(kpis: Dict[str, Any], member_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if member_profile:
        participation = float(member_profile.get("participation_score") or 0)
        attendance = float(member_profile.get("attendance_rate") or 0)
        goal_pct = int(round((member_profile.get("goal_completion") or 0) * 100))
        sessions = max(2, int(round(participation * 12)))
        minutes = max(60, sessions * 45)
        recommendation = member_profile.get("suggested_action") or "이번 주에는 한 번 더 루틴을 넣어보세요."
        program = member_profile.get("program") or "홈 트레이닝"
        segment = member_profile.get("segment") or "회원"
        sessions_note = f"{segment} · 출석률 {attendance * 100:.0f}%" if attendance else f"{segment} 세그먼트"
        minutes_note = f"{program} 기반 플로우"
        return {
            "sessions": sessions,
            "minutes": minutes,
            "goal": max(0, min(goal_pct, 100)),
            "recommendation": recommendation,
            "sessions_note": sessions_note,
            "minutes_note": minutes_note,
        }
    documents = kpis.get("documents_indexed") or 48
    sessions = max(4, documents // 4)
    minutes = sessions * 45
    goal_pct = min(100, 40 + sessions * 4)
    return {
        "sessions": sessions,
        "minutes": minutes,
        "goal": goal_pct,
        "recommendation": f"이번 주 {sessions + 1}회 세션을 가볍게 예약해보세요.",
        "sessions_note": "안정적인 페이스",
        "minutes_note": "평균 45분 세션",
    }


RISK_SIGNAL_COPY = {
    "refund_pressure": "환불 문의가 소폭 늘었습니다. 오후 타임 결제를 한번 더 점검해보세요.",
    "payment_decline": "일부 결제 거절률이 상승했습니다. 카드사 라우팅을 확인하면 안정성이 높아집니다.",
    "session_health_risk": "세션 헬스 지표에 미세한 이상이 있습니다. 트레이너와 짧은 리마인드를 공유해보세요.",
    "graph_anomaly_suspected": "그래프 상에서 새로운 연결이 감지되었습니다. 관계형 데이터를 재검수하면 도움이 됩니다.",
    "ontology_complex_relation": "온톨로지 관계가 복잡해졌습니다. 핵심 분류만 우선 살피면 충분합니다.",
    "stable": "격한 이상 징후는 없어요. 현재 페이스를 유지하면 좋겠습니다.",
}


def build_signal_copy(signal: str) -> str:
    return RISK_SIGNAL_COPY.get(signal, f"{signal} 시그널이 관측되었습니다. 컨텍스트를 확인해보세요.")


def build_alert_messages(risk_payload: Dict[str, Any]) -> List[str]:
    signals = risk_payload.get("signals") or []
    messages = [build_signal_copy(sig) for sig in signals]
    narrative = risk_payload.get("narrative")
    if narrative:
        messages.append(narrative)
    if not messages:
        messages = ["현재는 안정적인 상태입니다."]
    return messages[:4]


def build_recommendation_lines(payload: Dict[str, Any], limit: int = 3) -> List[str]:
    items = payload.get("items") or []
    lines: List[str] = []
    for item in items[:limit]:
        title = item.get("title", "추천")
        action = item.get("action", "")
        lines.append(f"{title} · {action}")
    narrative = payload.get("narrative")
    if narrative:
        lines.append(narrative)
    return lines or ["추천 카드를 준비하는 중입니다."]


def build_execution_actions(recommendation: Dict[str, Any], risk: Dict[str, Any]) -> List[str]:
    actions: List[str] = []
    for idx, item in enumerate((recommendation.get("items") or [])[:3], start=1):
        title = item.get("title", "실행")
        action = item.get("action", "")
        actions.append(f"{idx}. {title} — {action}")
    signals = risk.get("signals") or []
    if signals:
        actions.append(f"⚠︎ {build_signal_copy(signals[0])}")
    return actions or ["우선 조치가 필요한 항목이 없습니다."]


def build_member_coach_tips(recommendation: Dict[str, Any], explanation: Dict[str, Any], activity: Dict[str, Any]) -> List[str]:
    tips: List[str] = []
    if explanation.get("message"):
        tips.append(explanation["message"])
    for item in (recommendation.get("items") or [])[:2]:
        title = item.get("title", "추천")
        action = item.get("action", "")
        tips.append(f"{title} — {action}")
    tips.append(activity.get("recommendation") or "이번 주에는 한 번만 더 세션을 추가해보세요.")
    return tips[:3]


def build_member_graph_summary(
    kpis: Dict[str, Any],
    strategy: Dict[str, Any],
    member_profile: Optional[Dict[str, Any]] = None,
) -> str:
    key_actions = strategy.get("key_actions") or ["편안한 속도로 루틴을 이어가세요."]
    if member_profile:
        program = member_profile.get("program") or "선호 루틴"
        segment = member_profile.get("segment") or "회원"
        attendance = member_profile.get("attendance_rate")
        attendance_note = f"출석률 {attendance * 100:.0f}%" if isinstance(attendance, (int, float)) else "출석률 집계 중"
        healthkit = member_profile.get("healthkit_opt_in") or "미동의"
        summary = (
            f"{segment} 세그먼트에서 {program} 중심으로 루틴을 운영 중입니다. "
            f"{attendance_note} · HealthKit {healthkit}."
        )
        return summary + f"\n추천 액션: {key_actions[0]}"
    modalities = kpis.get("modalities") or ["요가", "필라테스"]
    highlight = ", ".join(modalities[:3])
    return (
        f"{highlight} 프로그램을 자주 이용하고 있어요. 즐겨 찾는 시간대를 유지하면 컨디션이 잘 유지됩니다.\n"
        f"추천 액션: {key_actions[0]}"
    )


def build_operator_view_model(bundle: Dict[str, Any]) -> Dict[str, Any]:
    insight = bundle.get("insight", {})
    risk = bundle.get("risk", {})
    recommendation = bundle.get("recommendation", {})
    strategy = bundle.get("strategy_framework", {})
    explanation = bundle.get("explanation", {})
    kpis = insight.get("kpis", {})
    return {
        "kpis": kpis,
        "summary": insight.get("summary"),
        "risk_series": build_risk_timeseries(risk.get("risk_score")),
        "risk_messages": build_alert_messages(risk),
        "playbook": build_recommendation_lines(recommendation),
        "strategy_actions": strategy.get("key_actions") or [],
        "strategy": strategy,
        "consumer_voice": explanation.get("message"),
    }


def build_studio_view_model(bundle: Dict[str, Any]) -> Dict[str, Any]:
    insight = bundle.get("insight", {})
    kpis = insight.get("kpis", {})
    recommendation = bundle.get("recommendation", {})
    risk = bundle.get("risk", {})
    return {
        "kpis": kpis,
        "pulse": insight.get("summary"),
        "program_flow": build_program_flow_dataframe(kpis),
        "execution_actions": build_execution_actions(recommendation, risk),
        "alerts": build_alert_messages(risk),
        "narrative": recommendation.get("narrative") or insight.get("summary"),
    }


def build_member_view_model(
    bundle: Dict[str, Any], member_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    insight = bundle.get("insight", {})
    recommendation = bundle.get("recommendation", {})
    explanation = bundle.get("explanation", {})
    strategy = bundle.get("strategy_framework", {})
    kpis = insight.get("kpis", {})
    activity = build_member_activity(kpis, member_profile)
    rec_items = recommendation.get("items") or []
    program_lines = [f"{item.get('title', '추천')} · {item.get('action', '')}" for item in rec_items[:3]]
    profile_context: List[str] = []
    if member_profile:
        member_id = member_profile.get("member_id")
        segment = member_profile.get("segment")
        program = member_profile.get("program")
        if member_id:
            profile_context.append(f"회원 ID: {member_id}")
        if program or segment:
            profile_context.append(f"{segment or '세그먼트 미지정'} · {program or '루틴 설명 준비 중'}")
        attendance = member_profile.get("attendance_rate")
        participation = member_profile.get("participation_score")
        if isinstance(attendance, (int, float)) or isinstance(participation, (int, float)):
            parts = []
            if isinstance(attendance, (int, float)):
                parts.append(f"출석률 {attendance * 100:.0f}%")
            if isinstance(participation, (int, float)):
                parts.append(f"참여점수 {participation:.2f}")
            profile_context.append(" · ".join(parts))
        heart_rate = member_profile.get("avg_heart_rate")
        if isinstance(heart_rate, (int, float)):
            profile_context.append(f"평균 심박 {int(round(heart_rate))} bpm")
        healthkit = member_profile.get("healthkit_opt_in")
        if healthkit:
            profile_context.append(f"HealthKit {healthkit}")
    return {
        "activity": activity,
        "program_lines": program_lines,
        "coach_tips": build_member_coach_tips(recommendation, explanation, activity),
        "graph_summary": build_member_graph_summary(kpis, strategy, member_profile),
        "profile_context": profile_context,
    }


def render_operator_view(bundle: Optional[Dict[str, Any]], *, studio_id: str, query_meta: Dict[str, str]) -> None:
    if not bundle:
        st.info("Command Center 데이터를 불러오지 못했습니다. 쿼리를 다시 실행해 주세요.")
        return
    model = build_operator_view_model(bundle)
    kpis = model["kpis"]
    render_header(
        title=f"Command Center — {studio_id}",
        subtitle="Neo4j · GraphDB 시그널을 조용하고 명확하게 집계했습니다.",
        badge=query_meta.get("label", "자연어"),
    )
    request_text = shorten_query(query_meta.get("query", ""), 220) or "기본 질의를 사용 중입니다."
    cached_label = "캐시 응답" if bundle.get("cached") else "실시간"
    render_text_card(
        title="요청 컨텍스트",
        body=request_text,
        footer=f"Trace {bundle.get('trace_id', 'N/A')} · {cached_label}",
    )

    documents = kpis.get("documents_indexed") or 0
    modalities = kpis.get("modalities") or []
    avg_amount = kpis.get("avg_amount")
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "인덱싱 문서", f"{documents:,}", "그래프·벡터 소스")
    render_metric_card(
        col2,
        "관측된 모달리티",
        f"{len(modalities)}개",
        extra_html=f"<div>{build_modalities_html(modalities)}</div>",
    )
    render_metric_card(col3, "평균 거래 규모", format_currency(avg_amount), "GraphRAG 추정치")

    st.markdown("<div class='lop-section-title'>Graph Risk Trajectory</div>", unsafe_allow_html=True)
    st.area_chart(model["risk_series"], use_container_width=True, height=260)

    render_list_card("시그널 & 코칭 메모", model["risk_messages"])

    render_text_card("LLM Insight Summary", model.get("summary"))
    render_list_card("추천 플레이북", model["playbook"])

    render_text_card("Consumer Voice", model.get("consumer_voice"))
    render_list_card("전략 키 액션", model["strategy_actions"])

    st.markdown("<div class='lop-section-title'>Raw Multi-Agent Payload</div>", unsafe_allow_html=True)
    pretty = json.dumps(bundle, ensure_ascii=False, indent=2)
    st.markdown(
        f"<div class='lop-json-box'><pre>{html.escape(pretty)}</pre></div>",
        unsafe_allow_html=True,
    )


def render_studio_view(bundle: Optional[Dict[str, Any]], *, studio_id: str, query_meta: Dict[str, str]) -> None:
    if not bundle:
        st.info("스튜디오 콘솔 데이터를 불러오지 못했습니다.")
        return
    model = build_studio_view_model(bundle)
    kpis = model["kpis"]
    render_header(
        title=f"Studio Console — {studio_id}",
        subtitle="오늘의 예약, 수익, 구독 흐름을 한 번에 살펴보세요.",
        badge="실행 요약",
    )
    render_text_card("운영자 질문", shorten_query(query_meta.get("query", ""), 220))

    documents = kpis.get("documents_indexed") or 80
    avg_amount = kpis.get("avg_amount") or 78000
    monthly_revenue = max(25_000_000, int(avg_amount * max(documents, 60)))
    active_subscribers = max(120, documents + 60)
    programs = len(kpis.get("modalities") or []) or 3
    trainers = max(4, programs + 2)

    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "이번 달 매출", format_currency(monthly_revenue), "정산·거래 기준")
    render_metric_card(col2, "활성 구독자", f"{active_subscribers:,}명", "앱/오프라인 합산")
    render_metric_card(col3, "진행 중 프로그램", f"{programs}개 / 트레이너 {trainers}명")

    st.markdown("<div class='lop-section-title'>프로그램 & 구독 흐름</div>", unsafe_allow_html=True)
    st.line_chart(model["program_flow"], use_container_width=True, height=260)

    render_text_card("오늘의 실행 인사이트", model.get("narrative"))

    render_list_card("Execution Playbook", model["execution_actions"])

    render_list_card("Light Alerts", model["alerts"])


def render_member_view(
    bundle: Optional[Dict[str, Any]],
    *,
    studio_id: str,
    member_name: str,
    query_meta: Dict[str, str],
    member_profile: Optional[Dict[str, Any]] = None,
) -> None:
    if not bundle:
        st.info("회원 포털 데이터를 불러오지 못했습니다.")
        return
    model = build_member_view_model(bundle, member_profile)
    activity = model["activity"]

    render_header(
        title=f"Member Portal — {member_name} 님",
        subtitle="최근 활동과 다음 루틴을 한 곳에서 확인하세요.",
        badge="맞춤 제안",
    )
    render_text_card(
        "나의 질문",
        shorten_query(query_meta.get("query", ""), 220),
        footer=f"{studio_id} 기반 컨텍스트",
    )
    if model.get("profile_context"):
        render_list_card("계정 컨텍스트", model["profile_context"])

    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "이번 달 세션", f"{activity['sessions']}회", activity.get("sessions_note"))
    render_metric_card(col2, "누적 운동 시간", f"{activity['minutes']}분", activity.get("minutes_note"))
    render_metric_card(col3, "목표 달성률", f"{activity['goal']}%", activity["recommendation"])

    render_list_card("추천 프로그램 / 트레이너", model["program_lines"])

    render_list_card("다음 주를 위한 제안", model["coach_tips"])

    render_text_card("나의 그래프 요약", model["graph_summary"])


def render_operator_page(studio_id: str) -> None:
    default_nl = "GraphDB와 Neo4j 시그널을 합쳐 오늘의 리스크 힌트를 요약해줘."
    default_sparql = "SELECT ?studio ?program WHERE { ?studio a lop:Studio . ?studio lop:offers ?program } LIMIT 10"

    result = ensure_pipeline_result("operator_data", studio_id, default_nl, "자연어")

    st.markdown("<div class='lop-section-title'>HQ 질의</div>", unsafe_allow_html=True)
    with st.form("operator-query-form", clear_on_submit=False):
        query_mode = st.radio("쿼리 방식", ["자연어", "SPARQL"], horizontal=True, index=0, key="operator_query_mode")
        if "operator_natural" not in st.session_state:
            st.session_state["operator_natural"] = default_nl
        if "operator_sparql_text" not in st.session_state:
            st.session_state["operator_sparql_text"] = default_sparql
        natural_query = st.text_input(
            "자연어 질의",
            key="operator_natural",
            placeholder="예) 강남 스튜디오의 Neo4j 리스크를 정리해줘",
        )
        sparql_query = st.text_area(
            "SPARQL 질의",
            key="operator_sparql_text",
            height=160,
            placeholder="PREFIX lop: <http://lop.example/ontology/> ...",
        )
        submitted = st.form_submit_button("Command Center 실행", use_container_width=True)
    if submitted:
        raw_query = natural_query if query_mode == "자연어" else sparql_query
        fallback = default_nl if query_mode == "자연어" else default_sparql
        target_query = raw_query.strip() or fallback
        with st.spinner("그래프 시그널을 합성하는 중입니다…"):
            result = refresh_pipeline_result("operator_data", studio_id, target_query, query_mode)
    meta = get_query_meta("operator_data", "자연어", default_nl)
    render_operator_view(result, studio_id=studio_id, query_meta=meta)


def render_studio_page(studio_id: str) -> None:
    default_query = "이번 주 스튜디오 KPI와 실행 인사이트를 정리해줘."
    result = ensure_pipeline_result("studio_data", studio_id, default_query, "자연어")

    st.markdown("<div class='lop-section-title'>스튜디오 질문</div>", unsafe_allow_html=True)
    if "studio_question" not in st.session_state:
        st.session_state["studio_question"] = default_query
    with st.form("studio-query-form", clear_on_submit=False):
        studio_query = st.text_input(
            "전달하고 싶은 질문",
            key="studio_question",
            placeholder="예) 저녁 시간 예약 흐름을 요약해줘",
        )
        submitted = st.form_submit_button("Console 업데이트", use_container_width=True)
    if submitted:
        target_query = studio_query.strip() or default_query
        with st.spinner("스튜디오 신호를 정리하는 중입니다…"):
            result = refresh_pipeline_result("studio_data", studio_id, target_query, "자연어")
    meta = get_query_meta("studio_data", "자연어", default_query)
    render_studio_view(result, studio_id=studio_id, query_meta=meta)


def render_member_page(studio_id: str, member_name: str) -> None:
    default_query = "내가 집중해야 할 다음 주 운동 루틴을 추천해줘."
    member_profile = get_member_snapshot(studio_id, member_name)
    result = ensure_pipeline_result("member_data", studio_id, default_query, "회원 질문")

    st.markdown("<div class='lop-section-title'>회원 질문</div>", unsafe_allow_html=True)
    if "member_question" not in st.session_state:
        st.session_state["member_question"] = default_query
    with st.form("member-query-form", clear_on_submit=False):
        member_query = st.text_area(
            "궁금한 점을 적어주세요",
            key="member_question",
            height=120,
            placeholder="예) 이번 주에는 어떤 프로그램으로 리듬을 만들면 좋을까?",
        )
        submitted = st.form_submit_button("추천 업데이트", use_container_width=True)
    if submitted:
        target_query = member_query.strip() or default_query
        with st.spinner("회원 맞춤 제안을 준비하는 중입니다…"):
            result = refresh_pipeline_result("member_data", studio_id, target_query, "회원 질문")
    meta = get_query_meta("member_data", "회원 질문", default_query)
    render_member_view(
        result,
        studio_id=studio_id,
        member_name=member_name,
        query_meta=meta,
        member_profile=member_profile,
    )


def main() -> None:
    inject_custom_css()
    st.sidebar.markdown("### LOP Dashboard")
    persona = st.sidebar.radio("View", ["운영사", "스튜디오", "회원"], index=0)
    if "sidebar_studio_id" not in st.session_state:
        st.session_state["sidebar_studio_id"] = "SGANG01"
    studio_id = st.sidebar.text_input("Studio ID", key="sidebar_studio_id")
    if persona == "회원":
        if "sidebar_member_name" not in st.session_state:
            st.session_state["sidebar_member_name"] = "계정"
        member_name = st.sidebar.text_input("회원 이름", key="sidebar_member_name")
    else:
        member_name = st.session_state.get("sidebar_member_name", "계정")
    st.sidebar.caption("Neo4j · GraphDB · 멀티 에이전트 신호를 Apple Fitness+ 톤으로 정리했습니다.")

    if persona == "운영사":
        render_operator_page(studio_id)
    elif persona == "스튜디오":
        render_studio_page(studio_id)
    else:
        render_member_page(studio_id, member_name)


if __name__ == "__main__":
    main()
