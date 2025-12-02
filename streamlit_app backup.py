from __future__ import annotations

import html
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from neo4j import GraphDatabase, Query

try:
    from pyvis.network import Network
except ImportError:  # pragma: no cover - optional visual enhancement
    Network = None  # type: ignore[assignment]

from app.config import get_settings
from app.services.agent_orchestrator import AgentOrchestrator


st.set_page_config(page_title="LOP Dashboard", page_icon="??", layout="wide")


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
    font-family: -LOP-system, BlinkMacSystemFont, "SF Pro Text", "LOP SD Gothic Neo", "Malgun Gothic", "Noto Sans KR", system-ui, sans-serif;
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
.lop-section-selector {
    margin: 1rem 0 1.5rem;
    padding: 0.6rem;
    border-radius: 16px;
    background: #f8fafc;
    border: 1px solid rgba(148, 163, 184, 0.3);
}
.lop-section-note {
    font-size: 0.9rem;
    color: #475467;
    margin-top: -0.5rem;
}
.lop-schedule {
    display: flex;
    gap: 0.85rem;
    overflow-x: auto;
    padding: 0.4rem 0.2rem 0.2rem;
}
.lop-schedule-item {
    min-width: 120px;
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    padding: 0.75rem 0.9rem;
}
.lop-schedule-title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0.2rem 0;
}
.lop-schedule-item .lop-card-note {
    font-size: 0.8rem;
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

.lop-graph-panels {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}
.lop-graph-panel {
    background: #ffffff;
    border-radius: 20px;
    padding: 1rem;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
}
.lop-graph-panel-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: 0.02em;
}
.lop-graph-panel-metric {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
}
.lop-graph-panel-note {
    font-size: 0.85rem;
    color: #475569;
}
.lop-graph-visual {
    position: relative;
    height: 160px;
    margin-bottom: 0.75rem;
    border-radius: 18px;
    background: radial-gradient(circle at 30% 30%, rgba(226, 232, 240, 0.6), rgba(248, 250, 252, 0.2));
    overflow: hidden;
}
.lop-node {
    position: absolute;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.lop-node.central {
    width: 90px;
    height: 90px;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    background: rgba(59, 130, 246, 0.18);
    border: 2px solid rgba(37, 99, 235, 0.5);
    color: #1d4ed8;
}
.lop-graph-visual-ontology .lop-node {
    background: rgba(191, 219, 254, 0.45);
    border: 1px solid rgba(147, 197, 253, 0.8);
    color: #1e3a8a;
    width: 46px;
    height: 46px;
}
.lop-graph-visual-ontology .lop-node.central {
    background: rgba(99, 102, 241, 0.18);
    border-color: rgba(79, 70, 229, 0.6);
    color: #312e81;
}
.lop-node.orb-1 { top: 10%; left: 18%; }
.lop-node.orb-2 { top: 12%; right: 15%; }
.lop-node.orb-3 { bottom: 14%; left: 20%; }
.lop-node.orb-4 { bottom: 10%; right: 18%; }
.lop-node.orb-5 { top: 45%; left: 6%; }
.lop-node.orb-6 { top: 45%; right: 6%; }
.lop-graph-visual-neo {
    background: radial-gradient(circle at 70% 30%, rgba(16, 185, 129, 0.25), rgba(248, 250, 252, 0.1));
}
.lop-graph-visual-neo .lop-node {
    background: rgba(110, 231, 183, 0.35);
    border: 1px solid rgba(16, 185, 129, 0.7);
    color: #065f46;
    width: 42px;
    height: 42px;
}
.lop-graph-visual-neo .lop-node.central {
    width: 72px;
    height: 72px;
    background: rgba(167, 243, 208, 0.45);
    border-color: rgba(45, 212, 191, 0.7);
    color: #064e3b;
}
.lop-node.neo-1 { top: 15%; left: 12%; }
.lop-node.neo-2 { top: 10%; right: 24%; }
.lop-node.neo-3 { top: 45%; left: 28%; }
.lop-node.neo-4 { top: 60%; right: 18%; }
.lop-node.neo-5 { bottom: 12%; left: 42%; }
.lop-node.neo-6 { bottom: 18%; right: 8%; }
.lop-edge {
    position: absolute;
    height: 2px;
    background: rgba(15, 118, 110, 0.4);
    transform-origin: left center;
}
.lop-edge.e1 { width: 120px; left: 20%; top: 30%; transform: rotate(5deg); }
.lop-edge.e2 { width: 150px; left: 32%; top: 60%; transform: rotate(-12deg); }
.lop-edge.e3 { width: 90px; left: 55%; top: 40%; transform: rotate(25deg); }
.lop-edge.e4 { width: 110px; left: 45%; top: 75%; transform: rotate(-30deg); }
.lop-graph-fusion {
    border-radius: 18px;
    padding: 0.85rem 1rem;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(14, 165, 233, 0.15));
    border: 1px dashed rgba(14, 165, 233, 0.4);
    font-weight: 600;
    color: #0f172a;
    text-align: center;
}
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

MEMBER_INTENT_OPTIONS = ["학원 정보", "이번 주 운동", "안전 & 재정"]
STUDIO_SECTION_OPTIONS = ["Command Pulse", "Member Signals", "Revenue Guard"]
OPERATOR_SECTION_OPTIONS = ["Network Ops Pulse", "Graph Intelligence", "Partner Safety Desk"]
DEFAULT_WORKFLOW_OPTION = "Default Flow"
INTENT_ICONS = {
    "학원 정보": "??",
    "이번 주 운동": "??",
    "안전 & 재정": "??",
    "Command Pulse": "??",
    "Member Signals": "??",
    "Revenue Guard": "??",
    "Network Ops Pulse": "🌐",
    "Graph Intelligence": "🧠",
    "Partner Safety Desk": "🛡️",
}
INTENT_PRESETS = {
    "학원 정보": "이 학원 소개와 트레이너, 대표 프로그램을 알려줘.",
    "이번 주 운동": "이번 주 내 운동 루틴과 추천 세션을 정리해줘.",
    "안전 & 재정": "결제, 환불 등 재정 상태가 안전한지 알려줘.",
}
INTENT_KEYWORDS = {
    "학원 정보": ["학원", "정보", "소개", "트레이너", "프로그램"],
    "이번 주 운동": ["운동", "루틴", "스케줄", "세션", "추천"],
    "안전 & 재정": ["재정", "안전", "결제", "환불", "리스크"],
}
INTENT_SPINNER_COPY = {
    "학원 정보": "학원 스토리를 정리하는 중입니다…",
    "이번 주 운동": "이번 주 루틴을 정리하는 중입니다…",
    "안전 & 재정": "재정·안전 신호를 확인하는 중입니다…",
}

def classify_member_intent(question: str) -> str:
    text = (question or "").strip()
    if not text:
        return MEMBER_INTENT_OPTIONS[0]
    lowered = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                return intent
    return MEMBER_INTENT_OPTIONS[0]


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
def fetch_pipeline_data(studio_id: str, normalized_query: str, workflow: Optional[str] = None) -> Dict[str, Any]:
    orchestrator = load_orchestrator()
    result = orchestrator.run_full_pipeline(
        user_query=normalized_query or None,
        studio_id=studio_id,
        workflow=workflow,
    )
    return result.to_dict()


def run_pipeline_with_fallback(
    studio_id: str,
    query: str | None,
    workflow: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    normalized = (query or "").strip()
    try:
        return fetch_pipeline_data(studio_id, normalized, workflow=workflow)
    except Exception as exc:
        st.error(f"Command Center 실행 중 오류가 발생했습니다: {exc}")
        return None

@st.cache_data(show_spinner=False)
def fetch_graph_context(studio_id: str, query: str) -> Dict[str, Any]:
    """Collect GraphRAG context so the UI can surface graph + Neo4j signals."""
    orchestrator = load_orchestrator()
    normalized = (query or "").strip() or "studio insight"
    return orchestrator.graphrag.build_reasoned_evidence(normalized, studio_id)


@st.cache_data(show_spinner=False)
def run_sparql_console(query: str) -> List[Dict[str, Any]]:
    """Execute raw SPARQL against GraphDB via the ontology service."""
    orchestrator = load_orchestrator()
    clean = (query or "").strip()
    if not clean:
        return []
    return orchestrator.ontology.sparql_query(clean)

@st.cache_data(show_spinner=False)
def _graphdb_select(endpoint: str, query: str) -> List[Dict[str, str]]:
    headers = {"Accept": "application/sparql-results+json"}
    params = {"query": query}
    response = requests.get(endpoint, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as err:
        snippet = response.text.strip().replace("\n", " ")[:200]
        raise ValueError(f"GraphDB returned non-JSON payload: {snippet}") from err
    results: List[Dict[str, str]] = []
    for binding in payload.get("results", {}).get("bindings", []):
        row = {key: value.get("value") for key, value in binding.items()}
        results.append(row)
    return results


@st.cache_data(show_spinner=False)
def fetch_graphdb_stats_cached(endpoint: str) -> Dict[str, Any]:
    queries = {
        "triples": "SELECT (COUNT(*) AS ?value) WHERE { ?s ?p ?o }",
        "classes": "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT (COUNT(DISTINCT ?cls) AS ?value) WHERE { ?cls a owl:Class }",
        "properties": "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT (COUNT(DISTINCT ?prop) AS ?value) WHERE { ?prop a ?type . FILTER(?type IN (owl:ObjectProperty, owl:DatatypeProperty)) }",
        "sample_classes": "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT ?class WHERE { ?class a owl:Class } ORDER BY ?class LIMIT 6",
        "sample_properties": "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT ?prop WHERE { ?prop a ?type . FILTER(?type IN (owl:ObjectProperty, owl:DatatypeProperty)) } ORDER BY ?prop LIMIT 6",
    }
    stats: Dict[str, Any] = {"endpoint": endpoint}
    try:
        for key in ("triples", "classes", "properties"):
            rows = _graphdb_select(endpoint, queries[key])
            first_row = rows[0] if rows else None
            value = first_row.get("value") if first_row else None
            stats[key] = int(float(value)) if value is not None else None
        stats["sample_classes"] = [row.get("class") for row in _graphdb_select(endpoint, queries["sample_classes"]) if row.get("class")]
        stats["sample_properties"] = [row.get("prop") for row in _graphdb_select(endpoint, queries["sample_properties"]) if row.get("prop")]
        return stats
    except Exception as exc:
        return {"error": str(exc), "endpoint": endpoint}


@st.cache_data(show_spinner=False)
def fetch_graphdb_stats() -> Dict[str, Any]:
    settings = get_settings()
    return fetch_graphdb_stats_cached(settings.graphdb_endpoint)


@st.cache_data(show_spinner=False)
def fetch_neo4j_stats_cached(uri: str, user: str, password: str) -> Dict[str, Any]:
    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            node_record = session.run("MATCH (n) RETURN count(n) AS nodes").single()
            rel_record = session.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()
            nodes = (node_record or {}).get("nodes", 0)
            rels = (rel_record or {}).get("rels", 0)
            labels = [record["label"] for record in session.run("CALL db.labels()")]
            rel_types = [record["relationshipType"] for record in session.run("CALL db.relationshipTypes()")]
        return {"uri": uri, "nodes": nodes, "relationships": rels, "labels": labels, "relationship_types": rel_types}
    except Exception as exc:
        return {"error": str(exc), "uri": uri}
    finally:
        if driver is not None:
            try:
                driver.close()
            except Exception:
                pass


@st.cache_data(show_spinner=False)
def fetch_neo4j_stats() -> Dict[str, Any]:
    settings = get_settings()
    return fetch_neo4j_stats_cached(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)


@st.cache_data(show_spinner=False)
def fetch_neo4j_graph_sample(studio_id: str) -> List[Dict[str, Any]]:
    """Return neighborhood rows for GraphViz visualization."""
    settings = get_settings()
    def _serialize(node: Any) -> Dict[str, Any]:
        if node is None:
            return {}
        if isinstance(node, dict):
            return node
        data: Dict[str, Any] = {}
        try:
            data.update(dict(node))  # type: ignore[arg-type]
        except Exception:
            data["id"] = str(node)
        labels = []
        try:
            labels = list(getattr(node, "labels", []))
        except Exception:
            labels = []
        if labels:
            data.setdefault("labels", labels)
        if labels and "label" not in data:
            data["label"] = labels[0]
        if "id" not in data:
            data["id"] = data.get("name") or data.get("label") or str(node)
        return data
    driver = None
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        params = {"studio_id": studio_id}
        with driver.session() as session:
            def _run(query: Query) -> List[Dict[str, Any]]:
                result = session.run(query, params)
                rows: List[Dict[str, Any]] = []
                for record in result:
                    rows.append(
                        {
                            "studio": _serialize(record.get("studio")),
                            "neighbor": _serialize(record.get("neighbor")),
                            "rel_type": record.get("rel_type"),
                        }
                    )
                return rows

            targeted_query: Query = Query(
                """
                MATCH (m)-[r]-(n)
                WHERE toLower(COALESCE(
                    m.id,
                    m.studio_id,
                    m.studioId,
                    m.merchant_id,
                    m.merchantId,
                    m.name,
                    m.label
                )) CONTAINS toLower($studio_id)
                RETURN m AS studio, TYPE(r) AS rel_type, n AS neighbor
                LIMIT 60
                """
            )
            rows = _run(targeted_query)
            if rows:
                return rows
            fallback_query: Query = Query(
                """
                MATCH (m)-[r]-(n)
                RETURN m AS studio, TYPE(r) AS rel_type, n AS neighbor
                LIMIT 40
                """
            )
            return _run(fallback_query)
    except Exception as exc:
        return [{"mode": "stub", "error": str(exc)}]
    finally:
        if driver is not None:
            try:
                driver.close()
            except Exception:
                pass
def ensure_pipeline_result(
    state_key: str, studio_id: str, query: str, label: str, workflow: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    if state_key not in st.session_state:
        st.session_state[state_key] = run_pipeline_with_fallback(studio_id, query, workflow=workflow)
        st.session_state[f"{state_key}_meta"] = {"label": label, "query": query, "workflow": workflow or DEFAULT_WORKFLOW_OPTION}
    return st.session_state.get(state_key)


def refresh_pipeline_result(
    state_key: str, studio_id: str, query: str, label: str, workflow: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    data = run_pipeline_with_fallback(studio_id, query, workflow=workflow)
    st.session_state[f"{state_key}_meta"] = {"label": label, "query": query, "workflow": workflow or DEFAULT_WORKFLOW_OPTION}
    if data is not None:
        st.session_state[state_key] = data
    return st.session_state.get(state_key)


def get_query_meta(state_key: str, fallback_label: str, fallback_query: str) -> Dict[str, str]:
    return st.session_state.get(
        f"{state_key}_meta",
        {"label": fallback_label, "query": fallback_query, "workflow": DEFAULT_WORKFLOW_OPTION},
    )


def shorten_query(text: str, limit: int = 160) -> str:
    stripped = (text or "").strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}…"


def format_currency(amount: Optional[float]) -> str:
    if amount is None:
        return "데이터 수집 중"
    return f"\\{amount:,.0f}"


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



def render_member_section_selector(default_section: Optional[str] = None) -> str:
    options = MEMBER_INTENT_OPTIONS
    desc_map = {
        "학원 정보": "브랜드 스토리와 핵심 프로그램을 한눈에 제공합니다.",
        "이번 주 운동": "회원님의 이번 주 루틴과 권장 세션을 정리했습니다.",
        "안전 & 재정": "결제/정산 상태와 리스크 신호를 조용하게 요약합니다.",
    }
    state_key = "member_section_choice"
    if default_section and default_section in options:
        st.session_state[state_key] = default_section
    current = st.session_state.get(state_key, default_section or options[0])
    if current not in options:
        current = options[0]
    index = options.index(current)
    st.markdown("<div class='lop-section-selector'>", unsafe_allow_html=True)
    selection = st.radio(
        "궁금한 내용을 선택하세요.",
        options,
        index=index,
        horizontal=True,
        format_func=lambda label: f"{INTENT_ICONS.get(label, '?')}  {label}",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state[state_key] = selection
    st.markdown(
        f"<div class='lop-section-note'>{html.escape(desc_map.get(selection, ''))}</div>",
        unsafe_allow_html=True,
    )
    return selection


def build_member_schedule_timeline(
    program_lines: List[str], member_profile: Optional[Dict[str, Any]]
) -> List[Dict[str, str]]:
    days = ["월", "화", "수", "목", "금", "토", "일"]
    lines = program_lines or ["시그니처 루틴 · 리듬을 유지하세요"]
    seed_text = (member_profile or {}).get("member_id", "")
    offset = sum(ord(ch) for ch in seed_text) % len(lines) if lines else 0
    timeline: List[Dict[str, str]] = []
    for idx, day in enumerate(days):
        line = lines[(idx + offset) % len(lines)]
        parts = [part.strip() for part in line.split("·", 1)]
        title = parts[0]
        detail = parts[1] if len(parts) > 1 else "컨디션 체크"
        timeline.append({"day": day, "title": title, "detail": detail})
    return timeline


def render_member_shortcut_buttons() -> Optional[str]:
    st.markdown("<div class='lop-label-muted'>빠른 질문</div>", unsafe_allow_html=True)
    cols = st.columns(len(MEMBER_INTENT_OPTIONS), gap="small")
    triggered: Optional[str] = None
    for col, intent in zip(cols, MEMBER_INTENT_OPTIONS):
        label = f"{INTENT_ICONS.get(intent, '?')} {intent}"
        if col.button(label, key=f"member_quick_{intent}", use_container_width=True):
            triggered = intent
    return triggered


def render_member_schedule_timeline(timeline: List[Dict[str, str]]) -> None:
    if not timeline:
        st.info("스케줄 정보를 준비하는 중입니다.")
        return
    items_html = "".join(
        (
            f"<div class='lop-schedule-item'>"
            f"<div class='lop-label-muted'>{html.escape(item['day'])}</div>"
            f"<div class='lop-schedule-title'>{html.escape(item['title'])}</div>"
            f"<div class='lop-card-note'>{html.escape(item['detail'])}</div>"
            "</div>"
        )
        for item in timeline
    )
    st.markdown(f"<div class='lop-schedule'>{items_html}</div>", unsafe_allow_html=True)


def render_member_academy_section(
    model: Dict[str, Any], bundle: Optional[Dict[str, Any]], studio_id: str
) -> None:
    insight = (bundle or {}).get("insight", {})
    story = insight.get("summary") or model.get("graph_summary")
    render_text_card("학원 스토리", story, footer=f"{studio_id} · GraphRAG 신호")
    context = model.get("profile_context") or ["회원 컨텍스트를 준비하는 중입니다."]
    render_list_card("계정 컨텍스트", context)
    render_list_card("대표 프로그램 & 트레이너", model.get("program_lines") or [])
    kpis = insight.get("kpis", {})
    documents = kpis.get("documents_indexed") or 0
    modalities = kpis.get("modalities") or []
    segment = context[0] if context else "회원"
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "그래프 문서", f"{documents:,}", "학습된 자료")
    render_metric_card(col2, "모달리티", f"{len(modalities)}개", "주요 루틴")
    render_metric_card(col3, "회원 세그먼트", segment, "LOP 톤")


def render_member_schedule_section(
    model: Dict[str, Any], member_profile: Optional[Dict[str, Any]]
) -> None:
    activity = model["activity"]
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "이번 달 세션", f"{activity['sessions']}회", activity.get("sessions_note"))
    render_metric_card(col2, "누적 운동 시간", f"{activity['minutes']}분", activity.get("minutes_note"))
    render_metric_card(col3, "목표 달성률", f"{activity['goal']}%", activity["recommendation"])
    st.markdown("<div class='lop-section-title'>이번 주 일정</div>", unsafe_allow_html=True)
    render_member_schedule_timeline(
        build_member_schedule_timeline(model.get("program_lines") or [], member_profile)
    )
    render_list_card("추천 프로그램 / 트레이너", model.get("program_lines") or [])
    render_list_card("다음 주를 위한 제안", model.get("coach_tips") or [])
    render_text_card("나의 그래프 요약", model.get("graph_summary"))


def build_member_safety_metrics(bundle: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    insight = (bundle or {}).get("insight", {})
    kpis = insight.get("kpis", {})
    documents = kpis.get("documents_indexed") or 80
    avg_amount = kpis.get("avg_amount") or 78000
    monthly_revenue = max(20_000_000, int(avg_amount * max(documents, 60)))
    active_subscribers = max(120, documents + 45)
    risk = (bundle or {}).get("risk", {})
    risk_score = float(risk.get("risk_score") or 0.35)
    risk_pct = int(round(risk_score * 100))
    if risk_score < 0.4:
        status = "안정"
        status_copy = "결제·정산 흐름이 안정적이에요."
    elif risk_score < 0.65:
        status = "주의"
        status_copy = "한두 건의 결제 확인만 하면 완벽해요."
    else:
        status = "집중 케어"
        status_copy = "코치와 함께 리스크를 빠르게 점검해보세요."
    alerts = build_alert_messages(risk) if risk else ["현재는 안정적인 상태입니다."]
    return {
        "monthly_revenue": monthly_revenue,
        "active_subscribers": active_subscribers,
        "risk_pct": risk_pct,
        "status": status,
        "status_copy": status_copy,
        "alerts": alerts,
    }


def render_member_safety_section(bundle: Optional[Dict[str, Any]]) -> None:
    metrics = build_member_safety_metrics(bundle)
    risk = (bundle or {}).get("risk", {})
    explanation = (bundle or {}).get("explanation", {})
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "Revenue Pulse", format_currency(metrics["monthly_revenue"]), "정산 지표")
    render_metric_card(
        col2,
        "Subscription Health",
        f"{metrics['active_subscribers']:,}명",
        "활성 구독자",
    )
    render_metric_card(
        col3,
        "Risk Index",
        f"{metrics['risk_pct']}%",
        f"{metrics['status']} · {metrics['status_copy']}",
    )
    st.area_chart(build_risk_timeseries(risk.get("risk_score")), use_container_width=True, height=220)
    render_list_card("시그널 & 가이드", metrics["alerts"])
    render_text_card("LLM 안전 브리핑", explanation.get("message"))

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
        actions.append(f"{idx}. {title} ? {action}")
    signals = risk.get("signals") or []
    if signals:
        actions.append(f"?? {build_signal_copy(signals[0])}")
    return actions or ["우선 조치가 필요한 항목이 없습니다."]


def build_member_coach_tips(recommendation: Dict[str, Any], explanation: Dict[str, Any], activity: Dict[str, Any]) -> List[str]:
    tips: List[str] = []
    if explanation.get("message"):
        tips.append(explanation["message"])
    for item in (recommendation.get("items") or [])[:2]:
        title = item.get("title", "추천")
        action = item.get("action", "")
        tips.append(f"{title} ? {action}")
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


def render_operator_section_selector(default_section: Optional[str] = None) -> str:
    desc_map = {
        "Network Ops Pulse": "네트워크·에이전트 가동률을 한눈에 보여드립니다.",
        "Graph Intelligence": "GraphRAG·LLM이 발견한 시그널을 요약했습니다.",
        "Partner Safety Desk": "결제·정산 리스크를 LOP 톤으로 안내합니다.",
    }
    state_key = "operator_section_choice"
    if default_section and default_section in OPERATOR_SECTION_OPTIONS:
        st.session_state[state_key] = default_section
    current = st.session_state.get(state_key, default_section or OPERATOR_SECTION_OPTIONS[0])
    if current not in OPERATOR_SECTION_OPTIONS:
        current = OPERATOR_SECTION_OPTIONS[0]
    index = OPERATOR_SECTION_OPTIONS.index(current)
    st.markdown("<div class='lop-section-selector'>", unsafe_allow_html=True)
    selection = st.radio(
        "관심 주제를 선택하세요.",
        OPERATOR_SECTION_OPTIONS,
        index=index,
        horizontal=True,
        format_func=lambda label: f"{INTENT_ICONS.get(label, '?')}  {label}",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state[state_key] = selection
    st.markdown(
        f"<div class='lop-section-note'>{html.escape(desc_map.get(selection, ''))}</div>",
        unsafe_allow_html=True,
    )
    return selection


def get_backend_health_snapshot() -> Dict[str, Dict[str, Any]]:
    orchestrator = load_orchestrator()

    def measure(action) -> Optional[int]:
        start_time = time.perf_counter()
        try:
            action()
            elapsed = int((time.perf_counter() - start_time) * 1000)
            return max(1, elapsed)
        except Exception:
            return None

    latency_vector = measure(lambda: orchestrator.vector.search("health check", k=1))
    latency_graph = measure(lambda: orchestrator.ontology.sparql_query("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"))
    latency_neo4j = measure(lambda: orchestrator.neo4j.run_cypher("RETURN $value AS value LIMIT 1", {"value": 1}))
    vector_connected = getattr(orchestrator.vector, "is_connected", lambda: False)()
    graph_connected = getattr(orchestrator.ontology, "is_connected", lambda: False)()
    neo4j_connected = getattr(orchestrator.neo4j, "is_connected", lambda: False)()
    graph_summary = getattr(orchestrator.ontology, "status_summary", lambda: {})()
    neo_summary = getattr(orchestrator.neo4j, "summary", lambda: {})()

    def _status(latency: Optional[int], connected: bool, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        base: Dict[str, Any]
        if latency is None:
            base = {"status": "입력 대기", "detail": "헬스 체크를 불러올 수 없음"}
        elif latency < 200:
            base = {"status": "정상", "detail": f"지연 {latency}ms"}
        elif latency < 400:
            base = {"status": "주의", "detail": f"지연 {latency}ms"}
        else:
            base = {"status": "지연 심화", "detail": f"지연 {latency}ms"}
        suffix = "Connected" if connected else "Stub"
        base["detail"] = f"{base['detail']} · {suffix}"
        base["meta"] = meta or {}
        return base

    vector_meta = {"capability": "Hash embedding demo store"}
    return {
        "VectorDB": _status(latency_vector, vector_connected, vector_meta),
        "GraphDB": _status(latency_graph, graph_connected, graph_summary),
        "Neo4j": _status(latency_neo4j, neo4j_connected, neo_summary),
    }

def render_operator_network_section(model: Dict[str, Any]) -> None:
    kpis = model.get("kpis", {})
    documents = kpis.get("documents_indexed") or 120
    modalities = len(kpis.get("modalities") or [])
    uptime = min(100, 97 + documents % 3)
    agent_success = min(100, 94 + (documents % 5))
    latency = max(110, 210 - documents)
    health = get_backend_health_snapshot()
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "Network Uptime", f"{uptime:.1f}%", "API & Graph")
    render_metric_card(col2, "Agent Success", f"{agent_success:.1f}%", "Multi Agent")
    render_metric_card(col3, "Latency", f"{latency}ms", f"{modalities} 모달리티 관측")
    col_a, col_b, col_c = st.columns(3, gap="small")
    backend_labels = ("VectorDB", "GraphDB", "Neo4j")
    for col, label in zip((col_a, col_b, col_c), backend_labels):
        status = health.get(label, {"status": "입력 대기", "detail": "헬스 상태를 준비중", "meta": {}})
        meta = status.get("meta", {}) or {}
        extra = ""
        if label == "GraphDB":
            triples = meta.get("triples")
            if triples:
                extra = f"{int(triples):,} triples"
            last_loaded = meta.get("last_loaded_at")
            if last_loaded:
                extra = f"{extra} · Sync {last_loaded}" if extra else f"Sync {last_loaded}"
        elif label == "Neo4j":
            nodes = meta.get("nodes")
            rels = meta.get("relationships")
            if nodes is not None and rels is not None:
                extra = f"{int(nodes):,} nodes / {int(rels):,} rels"
            seeded = meta.get("last_seeded_at")
            if seeded:
                extra = f"{extra} · Evidence {seeded}" if extra else f"Evidence {seeded}"
        detail_text = status.get("detail") or ""
        if extra:
            detail_text = f"{detail_text} · {extra}"
        html_block = ("<div class='lop-card'>"
            f"<div class='lop-label-muted'>{label}</div>"
            f"<div class='lop-metric'>{status['status']}</div>"
            f"<div class='lop-card-note'>{detail_text}</div>"
            "</div>")
        col.markdown(html_block, unsafe_allow_html=True)
    render_operator_graph_story(health)
    st.area_chart(model["risk_series"], use_container_width=True, height=220)
    render_list_card("Ops Alerts", model.get("risk_messages") or [])
    render_text_card("LLM Insight Summary", model.get("summary"))








def render_operator_graph_story(health: Dict[str, Dict[str, Any]]) -> None:
    """Render dual graph story with lightweight visuals."""
    graph_meta = (health.get("GraphDB") or {}).get("meta", {}) or {}
    neo_meta = (health.get("Neo4j") or {}).get("meta", {}) or {}

    def _format_timestamp(value: Optional[str], fallback: str) -> str:
        if not value:
            return fallback
        normalized = value.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(normalized).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value

    triples = graph_meta.get("triples")
    last_loaded = _format_timestamp(graph_meta.get("last_loaded_at"), "Sync pending")
    nodes = neo_meta.get("nodes")
    rels = neo_meta.get("relationships")
    seeded = _format_timestamp(neo_meta.get("last_seeded_at"), "Evidence pending")

    graph_metric = f"{int(triples):,} triples" if isinstance(triples, (int, float)) else "Triples loading"
    if nodes is not None and rels is not None:
        neo_metric = f"{int(nodes):,} nodes / {int(rels):,} rels"
    else:
        neo_metric = "Network warming up"

    graph_visual = (
        "<div class='lop-graph-visual lop-graph-visual-ontology'>"
        "<span class='lop-node central'>POLICY</span> "
        "<span class='lop-node orb-1'>TTL</span> "
        "<span class='lop-node orb-2'>FND</span> "
        "<span class='lop-node orb-3'>BIZ</span> "
        "<span class='lop-node orb-4'>RISK</span> "
        "<span class='lop-node orb-5'>LIFE</span> "
        "<span class='lop-node orb-6'>FIN</span> "
        "</div>"
    )
    neo_visual = (
        "<div class='lop-graph-visual lop-graph-visual-neo'>"
        "<span class='lop-edge e1'></span>"
        "<span class='lop-edge e2'></span>"
        "<span class='lop-edge e3'></span>"
        "<span class='lop-edge e4'></span>"
        "<span class='lop-node central'>CORE</span> "
        "<span class='lop-node neo-1'>STU</span> "
        "<span class='lop-node neo-2'>MEM</span> "
        "<span class='lop-node neo-3'>TRN</span> "
        "<span class='lop-node neo-4'>PRG</span> "
        "<span class='lop-node neo-5'>RISK</span> "
        "<span class='lop-node neo-6'>LTV</span> "
        "</div>"
    )

    graph_panel = (
        "<div class='lop-graph-panel'>"
        f"{graph_visual}"
        "<div class='lop-graph-panel-title'>GraphDB Policy Ontology</div>"
        f"<div class='lop-graph-panel-metric'>{graph_metric}</div>"
        f"<div class='lop-graph-panel-note'>Sync {last_loaded}</div>"
        "</div>"
    )
    neo_panel = (
        "<div class='lop-graph-panel'>"
        f"{neo_visual}"
        "<div class='lop-graph-panel-title'>Neo4j Relationship Graph</div>"
        f"<div class='lop-graph-panel-metric'>{neo_metric}</div>"
        f"<div class='lop-graph-panel-note'>Evidence {seeded}</div>"
        "</div>"
    )
    fusion_copy = "? GraphRAG fuses policy + relationship signals for LOP alerts."
    html_block = (
        "<div class='lop-graph-panels'>"
        f"{graph_panel}"
        f"{neo_panel}"
        "</div>"
        f"<div class='lop-graph-fusion'>{fusion_copy}</div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)







def _escape_sparql_literal(value: str) -> str:
    """Escape user text for inline SPARQL FILTER usage."""
    return value.replace("\\", "\\\\").replace("\"", "\\\"")


def build_graphdb_keyword_query(term: str, studio_id: Optional[str] = None, limit: int = 50) -> str:
    """Build a simple CONTAINS SPARQL query for keyword search."""
    search = term.strip()
    if not search:
        search = studio_id or "studio"
    literal = _escape_sparql_literal(search)
    filters = [
        f'CONTAINS(LCASE(STR(?s)), LCASE("{literal}"))',
        f'CONTAINS(LCASE(STR(?o)), LCASE("{literal}"))',
    ]
    if studio_id:
        studio_literal = _escape_sparql_literal(studio_id)
        filters.insert(0, f'CONTAINS(STR(?s), "{studio_literal}")')
    filter_block = ' || '.join(filters)
    return (
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
        "SELECT ?s ?p ?o WHERE {\n"
        "  ?s ?p ?o .\n"
        f"  FILTER({filter_block})\n"
        f"}} LIMIT {limit}"
    )


def render_graph_intel_metrics(graph_ctx: Dict[str, Any]) -> None:
    graph_hits = len(graph_ctx.get("graph") or [])
    vector_hits = len(graph_ctx.get("vector") or [])
    neo_hits = len(graph_ctx.get("neo4j") or [])
    meta = graph_ctx.get("meta", {})
    combined = meta.get("combined_score")
    col1, col2, col3 = st.columns(3, gap="small")
    render_metric_card(col1, "Graph Triples", f"{graph_hits}", "GraphDB context window")
    render_metric_card(col2, "Vector Docs", f"{vector_hits}", "Chroma studio filter")
    render_metric_card(
        col3,
        "Neo4j Links",
        f"{neo_hits}",
        f"Combined {combined}" if combined is not None else "Neo4j relationship sample",
    )


def render_graphdb_console(studio_id: str, graph_ctx: Dict[str, Any]) -> None:
    key_prefix = f"{studio_id}_graphdb"
    keyword_key = f"{key_prefix}_keyword"
    st.session_state.setdefault(keyword_key, studio_id)
    search_term = st.text_input(
        "Graph keyword",
        key=keyword_key,
        placeholder="studio / program / modality",
        help="GraphDB triple subject/object FILTER 검색",
    )
    keyword_results_key = f"{key_prefix}_keyword_results"
    if st.button("Keyword Search", key=f"{key_prefix}_keyword_btn", use_container_width=True):
        query_text = build_graphdb_keyword_query(search_term or studio_id, studio_id)
        with st.spinner("GraphDB 검색 중..."):
            rows = run_sparql_console(query_text)
        st.session_state[keyword_results_key] = {"query": query_text, "rows": rows}
    keyword_result = st.session_state.get(keyword_results_key)
    if keyword_result:
        rows = keyword_result.get("rows") or []
        st.caption(f"GraphDB 결과 {len(rows)}건 · LIMIT 50")
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("결과가 없습니다. 다른 키워드를 시도해 주세요.")
    sparql_text_key = f"{key_prefix}_sparql_text"
    st.session_state.setdefault(sparql_text_key, build_graphdb_keyword_query(studio_id, studio_id))
    sparql_results_key = f"{key_prefix}_sparql_results"
    with st.expander("SPARQL 콘솔", expanded=False):
        sparql_query = st.text_area("SPARQL", key=sparql_text_key, height=160)
        if st.button("SPARQL 실행", key=f"{key_prefix}_sparql_btn", use_container_width=True):
            with st.spinner("GraphDB SPARQL 실행 중..."):
                rows = run_sparql_console(sparql_query)
            st.session_state[sparql_results_key] = {"query": sparql_query, "rows": rows}
        sparql_result = st.session_state.get(sparql_results_key)
        if sparql_result:
            rows = sparql_result.get("rows") or []
            st.caption(f"SPARQL 결과 {len(rows)}건")
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("SPARQL 결과가 없습니다.")
    sample_graph = graph_ctx.get("graph") or []
    if sample_graph:
        st.caption("현재 컨텍스트 Triple 샘플 (최대 10)")
        df = pd.DataFrame(sample_graph)
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)


def _normalize_neo4j_node(raw: Any, fallback: str) -> tuple[str, str]:
    if isinstance(raw, dict):
        identifier = str(raw.get("id") or raw.get("name") or raw.get("label") or fallback)
        label = str(raw.get("label") or raw.get("name") or raw.get("id") or fallback)
    elif isinstance(raw, str):
        parts = raw.rstrip("/").split("/")
        identifier = raw
        label = parts[-1] if parts else raw
    else:
        identifier = fallback
        label = fallback
    return identifier, label


def _build_neo4j_network_html(rows: List[Dict[str, Any]], studio_id: str) -> str:
    if Network is None:
        raise RuntimeError("PyVis is not installed; please install the optional dependency.")

    palette: List[tuple[str, str]] = [
        ("studio", "#1d4ed8"),
        ("member", "#c2410c"),
        ("trainer", "#0f766e"),
        ("program", "#7e22ce"),
        ("transaction", "#0369a1"),
        ("contract", "#0f172a"),
    ]

    def _sanitize(value: Any) -> str:
        return html.escape(str(value or "")).replace('"', "'").replace("\n", " ")

    alias: Dict[str, str] = {}
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    graph = nx.Graph()
    fallback_counter = 0

    def ensure_node(raw: Any, fallback: str, is_central: bool = False) -> str:
        nonlocal fallback_counter
        identifier, label = _normalize_neo4j_node(raw, fallback)
        if not identifier or identifier == fallback:
            fallback_counter += 1
            identifier = f"{fallback}-{fallback_counter}"
        alias.setdefault(identifier, identifier)
        node_id = alias[identifier]
        meta = raw if isinstance(raw, dict) else {"label": label, "id": identifier}
        raw_labels = meta.get("labels") or []
        labels = raw_labels if isinstance(raw_labels, list) else [raw_labels]
        lowered = " ".join(str(value).lower() for value in [label, *labels])
        color = "#475569"
        for keyword, shade in palette:
            if keyword in lowered:
                color = shade
                break
        if is_central:
            color = "#0ea5e9"
        safe_label = _sanitize(label)
        tooltip_parts = [safe_label]
        identifier_value = meta.get("id") or meta.get("name")
        if identifier_value:
            tooltip_parts.append(_sanitize(f"ID: {identifier_value}"))
        if labels:
            labels_text = ", ".join(_sanitize(str(lab)) for lab in labels if lab)
            tooltip_parts.append(f"Labels: {labels_text}")
        nodes[node_id] = {
            "label": safe_label,
            "color": color,
            "tooltip": "<br>".join(tooltip_parts),
            "is_central": is_central,
        }
        graph.add_node(node_id)
        return node_id

    def _edge_color(rel_type: str) -> str:
        palette = {
            "OWNS": "#7c3aed",
            "HAS": "#2563eb",
            "PAY": "#f97316",
            "ATTEND": "#0ea5e9",
            "CONNECTED": "#22c55e",
        }
        upper = rel_type.upper()
        for key, value in palette.items():
            if key in upper:
                return value
        return "#94a3b8"

    for rel in rows:
        start_alias = ensure_node(rel.get("studio") or {"id": studio_id, "label": studio_id}, studio_id, is_central=True)
        neighbor_alias = ensure_node(rel.get("neighbor") or {"label": "Neighbor"}, "Neighbor")
        rel_label = str(rel.get("rel_type") or rel.get("type") or rel.get("mode") or "RELATED")
        color = _edge_color(rel_label)
        edges.append(
            {
                "start": start_alias,
                "end": neighbor_alias,
                "label": _sanitize(rel_label),
                "color": color,
                "title": _sanitize(f"{rel_label}: {nodes[start_alias]['label']} → {nodes[neighbor_alias]['label']}")
            }
        )
        graph.add_edge(start_alias, neighbor_alias)

    if graph.number_of_nodes() > 1:
        positions = nx.spring_layout(graph, seed=42, k=0.8)
    else:
        single = next(iter(graph.nodes()), studio_id)
        positions = {single: (0.0, 0.0)}

    net = Network(height="520px", width="100%", bgcolor="#f8fafc", directed=True)
    net.toggle_physics(False)

    scale = 900
    for node_id, meta in nodes.items():
        x, y = positions.get(node_id, (0.0, 0.0))
        net.add_node(
            node_id,
            label=meta["label"],
            title=meta["tooltip"],
            color=meta["color"],
            x=float(x * scale),
            y=float(y * scale),
            physics=False,
            shape="dot",
            size=28 if meta["is_central"] else 16,
        )

    for edge in edges:
        net.add_edge(
            edge["start"],
            edge["end"],
            label=edge["label"],
            title=edge["title"],
            color=edge["color"],
            arrows="to",
            smooth=True,
        )

    options = {
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "zoomView": True,
        },
        "nodes": {"borderWidth": 1, "font": {"size": 14}},
        "edges": {"font": {"size": 12}},
    }
    net.set_options(json.dumps(options))
    return net.generate_html(notebook=False)


def render_neo4j_graph_panel(graph_ctx: Dict[str, Any], studio_id: str) -> None:
    rows = graph_ctx.get("neo4j") or []
    st.markdown("<div class='lop-label-muted'>Neo4j Graph</div>", unsafe_allow_html=True)
    if not rows:
        st.info("Neo4j ??? ????.")
        return
    if all(isinstance(row, dict) and row.get("mode") == "stub" for row in rows):
        error_msg = rows[0].get("error") if isinstance(rows[0], dict) else "Neo4j connection error"
        st.error("Neo4j ???? ?? ??? ??????.")
        st.caption(error_msg)
        return
    subset = rows[:80]
    try:
        html_graph = _build_neo4j_network_html(subset, studio_id)
    except Exception as exc:
        st.error(f"Neo4j ???? ????? ?????: {exc}")
        return
    components.html(html_graph, height=560, scrolling=False)
    st.caption(
        f"{len(subset)}? ??? ???????. ??? ???/???? hover? ?? ID/Label? ?????."
    )
    label_counter: Counter[str] = Counter()
    for rel in subset:
        for node in (rel.get("studio"), rel.get("neighbor")):
            if not isinstance(node, dict):
                continue
            labels = node.get("labels") or []
            if isinstance(labels, str):
                label_counter[labels] += 1
            else:
                for label in labels:
                    if label:
                        label_counter[str(label)] += 1
    if label_counter:
        top_labels = sorted(label_counter.items(), key=lambda item: item[1], reverse=True)[:6]
        st.write("?? ??")
        st.dataframe(
            pd.DataFrame(top_labels, columns=["Label", "Count"]),
            use_container_width=True,
            hide_index=True,
        )

def render_graph_evidence_panel(graph_ctx: Dict[str, Any]) -> None:
    evidence = ((graph_ctx.get("evidence") or {}).get("items") or [])[:6]
    if not evidence:
        return
    lines = []
    for item in evidence:
        source = str(item.get("source") or "graph").upper()
        subject = str(item.get("label") or item.get("subject") or "subject")
        predicate = str(item.get("predicate") or item.get("rel_type") or "related")
        obj = item.get("object")
        obj_text = obj if isinstance(obj, str) else str(obj)
        lines.append(f"{source} · {subject} --{predicate}--> {obj_text}")
    render_list_card("Graph Evidence", lines)



def render_operator_graph_section(
    model: Dict[str, Any],
    bundle: Optional[Dict[str, Any]],
    *,
    studio_id: str,
    query_meta: Dict[str, str],
) -> None:
    render_text_card("Graph Intelligence", model.get("summary"))
    try:
        graph_ctx = fetch_graph_context(studio_id, query_meta.get("query", ""))
    except Exception as exc:  # pragma: no cover - network/runtime
        st.error(f"Graph 컨텍스트를 불러오지 못했습니다: {exc}")
        return
    render_graph_intel_metrics(graph_ctx)
    left, right = st.columns((3, 2), gap="large")
    with left:
        render_graphdb_console(studio_id, graph_ctx)
    with right:
        render_neo4j_graph_panel(graph_ctx, studio_id)
    render_graph_evidence_panel(graph_ctx)
    render_list_card("추천 플레이북", model.get("playbook") or [])
    render_text_card("Consumer Voice", model.get("consumer_voice"))
    render_list_card("전략 액션", model.get("strategy_actions") or [])

def render_operator_safety_section(model: Dict[str, Any], bundle: Optional[Dict[str, Any]]) -> None:
    metrics = build_member_safety_metrics(bundle or {})
    risk = (bundle or {}).get("risk", {})
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "정산 예정액", format_currency(metrics.get("monthly_revenue")), "GraphRAG 추정")
    render_metric_card(col2, "구독 상태", f"{metrics.get('active_subscribers', 0):,}명", "활성 계정")
    render_metric_card(
        col3,
        "Risk Index",
        f"{metrics.get('risk_pct', 0)}%",
        f"{metrics.get('status')} · {metrics.get('status_copy')}",
    )
    st.area_chart(build_risk_timeseries(risk.get("risk_score")), use_container_width=True, height=220)
    render_list_card("결제/환불 알림", metrics.get("alerts", []))


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


def render_knowledge_digest(knowledge: Optional[List[Dict[str, Any]]]) -> None:
    if not knowledge:
        return
    insights: List[str] = []
    for ref in knowledge:
        title = ref.get('title') or 'Agentic Insight'
        snippet = (ref.get('snippet') or '').strip().replace('\n', ' ')
        source = ref.get('source')
        line = f"{title} · {snippet[:120]}..."
        if source:
            line += f" ({source})"
        insights.append(line)
    render_list_card('McKinsey Knowledge', insights)


def render_trace_timeline(trace_log: Optional[List[Dict[str, Any]]]) -> None:
    if not trace_log:
        return
    rows = []
    for event in trace_log:
        rows.append({
            'Skill': event.get('skill'),
            'Status': event.get('status'),
            'Latency(ms)': int((event.get('latency_s') or 0) * 1000),
            'Started': event.get('started_at'),
        })
    st.markdown("<div class='lop-section-title'>Workflow Timeline</div>", unsafe_allow_html=True)
    frame = pd.DataFrame(rows)
    st.dataframe(frame, use_container_width=True, hide_index=True)


def render_studio_section_selector(default_section: Optional[str] = None) -> str:
    desc_map = {
        "Command Pulse": "오늘의 운영 가동률과 즉시 조치 항목을 모았습니다.",
        "Member Signals": "회원 세그먼트·참여 시그널을 조용하게 정리했습니다.",
        "Revenue Guard": "정산 예정액과 리스크 알람을 안전하게 감시합니다.",
    }
    state_key = "studio_section_choice"
    if default_section and default_section in STUDIO_SECTION_OPTIONS:
        st.session_state[state_key] = default_section
    current = st.session_state.get(state_key, default_section or STUDIO_SECTION_OPTIONS[0])
    if current not in STUDIO_SECTION_OPTIONS:
        current = STUDIO_SECTION_OPTIONS[0]
    index = STUDIO_SECTION_OPTIONS.index(current)
    st.markdown("<div class='lop-section-selector'>", unsafe_allow_html=True)
    selection = st.radio(
        "관심 주제를 선택하세요.",
        STUDIO_SECTION_OPTIONS,
        index=index,
        horizontal=True,
        format_func=lambda label: f"{INTENT_ICONS.get(label, '?')}  {label}"
        if label in INTENT_ICONS
        else label,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state[state_key] = selection
    st.markdown(
        f"<div class='lop-section-note'>{html.escape(desc_map.get(selection, ''))}</div>",
        unsafe_allow_html=True,
    )
    return selection


def render_studio_command_section(model: Dict[str, Any], bundle: Optional[Dict[str, Any]]) -> None:
    kpis = model.get("kpis", {})
    documents = kpis.get("documents_indexed") or 80
    peak_utilization = min(100, 60 + documents % 45)
    evening_utilization = max(55, peak_utilization - 18)
    waitlist = max(12, documents // 2)
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "Peak Slots", f"{peak_utilization}%", "오늘의 가동률")
    render_metric_card(col2, "Evening Slots", f"{evening_utilization}%", "퇴근 시간 집중")
    render_metric_card(col3, "대기자", f"{waitlist}명", "즉시 조치 추천")
    st.line_chart(model.get("program_flow"), use_container_width=True, height=240)
    render_text_card("운영 Pulse", model.get("pulse"))
    render_list_card("Execution Playbook", model.get("execution_actions") or [])
    render_list_card("Light Alerts", model.get("alerts") or [])


def render_studio_member_signals_section(model: Dict[str, Any], bundle: Optional[Dict[str, Any]]) -> None:
    recommendation = (bundle or {}).get("recommendation", {})
    explanation = (bundle or {}).get("explanation", {})
    voice = explanation.get("message") or recommendation.get("narrative")
    render_text_card("회원 목소리", voice)
    render_list_card("추천 프로그램 퍼포먼스", model.get("execution_actions") or [])
    render_list_card("회원 제안", model.get("alerts") or [])
    render_list_card("LLM Member Signals", build_recommendation_lines(recommendation))


def render_studio_revenue_guard_section(bundle: Optional[Dict[str, Any]]) -> None:
    metrics = build_member_safety_metrics(bundle or {})
    risk = (bundle or {}).get("risk", {})
    explanation = (bundle or {}).get("explanation", {})
    col1, col2, col3 = st.columns(3, gap="large")
    render_metric_card(col1, "예상 정산액", format_currency(metrics.get("monthly_revenue")), "GraphRAG 추정")
    render_metric_card(col2, "활성 구독자", f"{metrics.get('active_subscribers', 0):,}명", "계정 기준")
    render_metric_card(
        col3,
        "Risk Index",
        f"{metrics.get('risk_pct', 0)}%",
        f"{metrics.get('status')} · {metrics.get('status_copy')}",
    )
    st.area_chart(build_risk_timeseries(risk.get("risk_score")), use_container_width=True, height=220)
    render_list_card("결제 알림", metrics.get("alerts", []))
    render_text_card("LLM 안전 브리핑", explanation.get("message"))


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
    render_header(
        title=f"Command Center ? {studio_id}",
        subtitle="멀티 에이전트 신호와 네트워크 상태를 LOP 톤으로 정리했습니다.",
        badge=query_meta.get("label", "자연어"),
    )
    request_text = shorten_query(query_meta.get("query", ""), 220) or "기본 질의를 사용 중입니다."
    cached_label = "캐시 응답" if bundle.get("cached") else "실시간"
    render_text_card(
        title="요청 컨텍스트",
        body=request_text,
        footer=f"Trace {bundle.get('trace_id', 'N/A')} · {cached_label}",
    )
    section = render_operator_section_selector()
    if section == "Network Ops Pulse":
        render_operator_network_section(model)
    elif section == "Graph Intelligence":
        render_operator_graph_section(model, bundle, studio_id=studio_id, query_meta=query_meta)
    else:
        render_operator_safety_section(model, bundle)

    render_knowledge_digest(bundle.get("knowledge"))
    render_trace_timeline(bundle.get("trace_log"))

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
    render_header(
        title=f"Studio Console ? {studio_id}",
        subtitle="LOP 톤으로 오늘의 운영 신호를 정리했습니다.",
        badge="실행 요약",
    )
    render_text_card("운영자 질문", shorten_query(query_meta.get("query", ""), 220))
    section = render_studio_section_selector()
    if section == "Command Pulse":
        render_studio_command_section(model, bundle)
    elif section == "Member Signals":
        render_studio_member_signals_section(model, bundle)
    else:
        render_studio_revenue_guard_section(bundle)


def render_member_view(
    bundle: Optional[Dict[str, Any]],
    *,
    studio_id: str,
    member_name: str,
    query_meta: Dict[str, str],
    member_profile: Optional[Dict[str, Any]] = None,
    section_override: Optional[str] = None,
) -> None:
    if not bundle:
        st.info("회원 포털 데이터를 불러오지 못했습니다.")
        return
    model = build_member_view_model(bundle, member_profile)
    activity = model["activity"]

    render_header(
        title=f"Member Portal ? {member_name} 님",
        subtitle="최근 활동과 다음 루틴을 한 곳에서 확인하세요.",
        badge="맞춤 제안",
    )
    render_text_card(
        "나의 질문",
        shorten_query(query_meta.get("query", ""), 220),
        footer=f"{studio_id} 기반 컨텍스트",
    )
    hero_copy = (member_profile or {}).get("suggested_action") or activity["recommendation"]
    render_text_card("오늘의 톤", hero_copy, footer="LOP 스타일")

    section = render_member_section_selector(section_override)
    if section == "학원 정보":
        render_member_academy_section(model, bundle, studio_id)
    elif section == "이번 주 운동":
        render_member_schedule_section(model, member_profile)
    else:
        render_member_safety_section(bundle)


def render_graph_overview_page(studio_id: str) -> None:
    if st.button(
        "그래프 통계 새로고침",
        help="st.cache_data를 초기화한 뒤 GraphDB/Neo4j 통계를 다시 조회합니다.",
        key="graph-refresh-button",
    ):
        st.cache_data.clear()
        fetch_graphdb_stats_cached.clear()
        fetch_graphdb_stats.clear()
        fetch_neo4j_stats_cached.clear()
        fetch_neo4j_stats.clear()
        rerun_fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
        if rerun_fn:
            rerun_fn()
        else:
            st.warning("캐시 초기화 완료. 그래프 탭을 수동으로 새로고침해 주세요.")
    graph_stats = fetch_graphdb_stats()
    neo_stats = fetch_neo4j_stats()
    neo4j_rows = fetch_neo4j_graph_sample(studio_id)
    st.markdown("<div class='lop-section-title'>Graph Observability</div>", unsafe_allow_html=True)
    tabs = st.tabs(["GraphDB", "Neo4j"])
    with tabs[0]:
        if graph_stats.get("error"):
            st.error(f"GraphDB 연결 오류: {graph_stats['error']}")
        else:
            col1, col2, col3 = st.columns(3)
            render_metric_card(col1, "Triples", f"{graph_stats.get('triples') or 0:,}", detail="전체 triple 수")
            render_metric_card(col2, "Classes", f"{graph_stats.get('classes') or 0:,}")
            render_metric_card(col3, "Properties", f"{graph_stats.get('properties') or 0:,}")
            with st.expander("대표 Class", expanded=False):
                st.write(graph_stats.get('sample_classes') or [])
            with st.expander("대표 Property", expanded=False):
                st.write(graph_stats.get('sample_properties') or [])
            st.caption("GraphDB SPARQL 검색")
            render_graphdb_console(studio_id, {"graph": []})
    with tabs[1]:
        if neo_stats.get("error"):
            st.error(f"Neo4j 연결 오류: {neo_stats['error']}")
        else:
            col1, col2, col3 = st.columns(3)
            render_metric_card(col1, "Nodes", f"{neo_stats.get('nodes') or 0:,}")
            render_metric_card(col2, "Relationships", f"{neo_stats.get('relationships') or 0:,}")
            render_metric_card(col3, "Labels", f"{len(neo_stats.get('labels') or [])}")
            with st.expander("Labels", expanded=False):
                st.write(neo_stats.get('labels') or [])
            with st.expander("Relationship Types", expanded=False):
                st.write(neo_stats.get('relationship_types') or [])
            st.caption("Neo4j 노드·엣지 시각화")
            render_neo4j_graph_panel({"neo4j": neo4j_rows}, studio_id)


def render_operator_page(studio_id: str) -> None:
    default_nl = "Summarize GraphDB and Neo4j insights for this studio."
    default_sparql = "SELECT ?studio ?program WHERE { ?studio a lop:Studio . ?studio lop:offers ?program } LIMIT 10"

    workflow_templates = getattr(load_orchestrator(), 'workflow_templates', {})
    workflow_options = [DEFAULT_WORKFLOW_OPTION] + list(workflow_templates.keys())
    if 'operator_workflow_value' not in st.session_state:
        st.session_state['operator_workflow_value'] = DEFAULT_WORKFLOW_OPTION
    workflow_choice = st.selectbox(
        'Workflow Template',
        workflow_options,
        index=workflow_options.index(st.session_state['operator_workflow_value']),
    )
    if workflow_choice != st.session_state['operator_workflow_value']:
        st.session_state['operator_workflow_value'] = workflow_choice
        st.session_state.pop('operator_data', None)
        st.session_state.pop('operator_data_meta', None)
    selected_workflow = None if workflow_choice == DEFAULT_WORKFLOW_OPTION else workflow_choice
    template_desc = workflow_templates.get(workflow_choice, {}).get('description') if selected_workflow else None
    if template_desc:
        st.caption(template_desc)

    result = ensure_pipeline_result('operator_data', studio_id, default_nl, '자연어', workflow=selected_workflow)

    st.markdown("<div class='lop-section-title'>HQ Analysis</div>", unsafe_allow_html=True)
    with st.form('operator-query-form', clear_on_submit=False):
        query_mode = st.radio('Question Type', ['자연어', 'SPARQL'], horizontal=True, index=0, key='operator_query_mode')
        if 'operator_natural' not in st.session_state:
            st.session_state['operator_natural'] = default_nl
        if 'operator_sparql_text' not in st.session_state:
            st.session_state['operator_sparql_text'] = default_sparql
        natural_query = st.text_input(
            'Natural language prompt',
            key='operator_natural',
            placeholder='예) 이번 스튜디오 Neo4j 그래프를 요약해줘',
            autocomplete='off',
        )
        sparql_query = st.text_area(
            'SPARQL query',
            key='operator_sparql_text',
            height=160,
            placeholder='PREFIX lop: <http://lop.example/ontology/> ...',
        )
        submitted = st.form_submit_button('Run Command Center', use_container_width=True)
    if submitted:
        raw_query = natural_query if query_mode == '자연어' else sparql_query
        fallback = default_nl if query_mode == '자연어' else default_sparql
        target_query = raw_query.strip() or fallback
        with st.spinner('Collecting multi-source context…'):
            result = refresh_pipeline_result('operator_data', studio_id, target_query, query_mode, workflow=selected_workflow)
    meta = get_query_meta('operator_data', '자연어', default_nl)
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
            autocomplete="off",
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
    section_override: Optional[str] = None
    quick_intent = render_member_shortcut_buttons()
    if quick_intent:
        preset_query = INTENT_PRESETS.get(quick_intent, default_query)
        st.session_state["member_question"] = preset_query
        spinner_label = INTENT_SPINNER_COPY.get(quick_intent, "회원 맞춤 제안을 준비하는 중입니다…")
        with st.spinner(spinner_label):
            result = refresh_pipeline_result("member_data", studio_id, preset_query, "회원 질문")
        section_override = quick_intent

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
        inferred_intent = classify_member_intent(target_query)
        spinner_label = INTENT_SPINNER_COPY.get(inferred_intent, "회원 맞춤 제안을 준비하는 중입니다…")
        with st.spinner(spinner_label):
            result = refresh_pipeline_result("member_data", studio_id, target_query, "회원 질문")
        section_override = inferred_intent

    if section_override is None:
        section_override = classify_member_intent(st.session_state.get("member_question", default_query))

    meta = get_query_meta("member_data", "회원 질문", default_query)
    render_member_view(
        result,
        studio_id=studio_id,
        member_name=member_name,
        query_meta=meta,
        member_profile=member_profile,
        section_override=section_override,
    )


def main() -> None:
    inject_custom_css()
    st.sidebar.markdown("### LOP Dashboard")
    persona_options = ["Operator", "Studio", "Member", "Graph"]
    persona = st.sidebar.radio("View", persona_options, index=0)
    if "sidebar_studio_id" not in st.session_state:
        st.session_state["sidebar_studio_id"] = "SGANG01"
    studio_id = st.sidebar.text_input("Studio ID", key="sidebar_studio_id", autocomplete="off")
    if persona == "Member":
        if "sidebar_member_name" not in st.session_state:
            st.session_state["sidebar_member_name"] = "Member-01"
        member_name = st.sidebar.text_input("Member Name", key="sidebar_member_name", autocomplete="off")
    else:
        member_name = st.session_state.get("sidebar_member_name", "Member-01")
    st.sidebar.caption("Neo4j · GraphDB · Multi-agent context를 LOP 톤으로 집계합니다.")

    if persona == "Operator":
        render_operator_page(studio_id)
    elif persona == "Studio":
        render_studio_page(studio_id)
    elif persona == "Member":
        render_member_page(studio_id, member_name)
    else:
        render_graph_overview_page(studio_id)



if __name__ == "__main__":
    main()
