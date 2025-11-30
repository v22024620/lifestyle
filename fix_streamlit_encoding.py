from pathlib import Path

path = Path("streamlit_app.py")
data = path.read_bytes()

# Reusable helper

def replace_slice(start_idx: int, end_idx: int, text: str) -> None:
    global data
    data = data[:start_idx] + text.encode("utf-8") + data[end_idx:]

# Column map block
col_start = data.index(b"MEMBER_COLUMN_MAP = {")
col_end = data.index(b"}\r\nNUMERIC_MEMBER_COLUMNS", col_start) + len(b"}\r\n")
col_block = """MEMBER_COLUMN_MAP = {
    \"회원ID\": \"member_id\",
    \"스튜디오ID\": \"studio_id\",
    \"프로그램\": \"program\",
    \"세그먼트\": \"segment\",
    \"참여점수\": \"participation_score\",
    \"출석률\": \"attendance_rate\",
    \"헬스킷동의\": \"healthkit_opt_in\",
    \"목표달성도\": \"goal_completion\",
    \"평균심박\": \"avg_heart_rate\",
    \"추천액션\": \"suggested_action\",
}\n""".replace("\n", "\r\n")
replace_slice(col_start, col_end, col_block)

# Member intent block
intent_start = data.index(b"MEMBER_INTENT_OPTIONS = [")
intent_end = data.index(b"INTENT_SPINNER_COPY = {", intent_start)
intent_end = data.index(b"}\r\n\r\n", intent_end) + len(b"}\r\n\r\n")
intent_block = """MEMBER_INTENT_OPTIONS = [\"회원 정보\", \"이번 주 운동\", \"안전 & 재정\"]
STUDIO_SECTION_OPTIONS = [\"Command Pulse\", \"Member Signals\", \"Revenue Guard\"]
OPERATOR_SECTION_OPTIONS = [\"Network Ops Pulse\", \"Graph Intelligence\", \"Partner Safety Desk\"]
INTENT_ICONS = {
    \"회원 정보\": \"💬\",
    \"이번 주 운동\": \"💪\",
    \"안전 & 재정\": \"🛡️\",
    \"Command Pulse\": \"🧭\",
    \"Member Signals\": \"📡\",
    \"Revenue Guard\": \"💱\",
    \"Network Ops Pulse\": \"🌐\",
    \"Graph Intelligence\": \"🧠\",
    \"Partner Safety Desk\": \"🛡️\",
}
INTENT_PRESETS = {
    \"회원 정보\": \"이 회원 소개와 트레이너, 대표 프로그램을 알려줘.\",
    \"이번 주 운동\": \"이번 주 내 운동 루틴과 추천 세션을 정리해줘.\",
    \"안전 & 재정\": \"결제, 환불 등 재정 상태가 안전한지 알려줘.\",
}
INTENT_KEYWORDS = {
    \"회원 정보\": [\"회원\", \"정보\", \"소개\", \"트레이너\", \"프로그램\"],
    \"이번 주 운동\": [\"운동\", \"루틴\", \"스케줄\", \"세션\", \"추천\"],
    \"안전 & 재정\": [\"재정\", \"안전\", \"결제\", \"환불\", \"리스크\"],
}
INTENT_SPINNER_COPY = {
    \"회원 정보\": \"회원 스토리를 정리하는 중입니다…\",
    \"이번 주 운동\": \"이번 주 루틴을 정리하는 중입니다…\",
    \"안전 & 재정\": \"재정·안전 신호를 확인하는 중입니다…\",
}\n\n""".replace("\n", "\r\n")
replace_slice(intent_start, intent_end, intent_block)

# Helper replacements for specific lines
from_patterns = {
    b"        st.error(f\"": "        st.error(f\"에이전트 실행 중 오류가 발생했습니다: {exc}\")\r\n",
}
for old, new in from_patterns.items():
    data = data.replace(old + b"?\x90\xec\x9d\xb4?\x84\xed\x8a\xb8 ?\xa4\xed\x96\x89 \xec\xa4??\xa4\xeb\xa5\x98\xea\xb0\x80 \xeb\xb0\x9c\xec\x83\x9d?\x88\xec\x8a\xb5?\x88\xeb\x8b\xa4: {exc}\")\r\n", new.encode("utf-8"))

# Format currency fallback
fmt_start = data.index(b"def format_currency")
none_line = data.index(b"        return ", fmt_start)
line_end = data.index(b"\r\n", none_line)
replace_slice(none_line, line_end + 2, "        return \"데이터 수집 중\"\r\n")

# Modalities line
modal_start = data.index(b"def build_modalities_html")
modal_line = data.index(b"        return \"<span", modal_start)
modal_end = data.index(b"\r\n", modal_line)
replace_slice(modal_line, modal_end + 2, "        return \"<span class='lop-card-note'>모달리티 신호 수집 중</span>\"\r\n")

# render_text_card fallback
text_start = data.index(b"def render_text_card")
safe_line = data.index(b"    safe_body = html.escape(body) if body else ", text_start)
safe_end = data.index(b"\r\n", safe_line)
replace_slice(safe_line, safe_end + 2, "    safe_body = html.escape(body) if body else \"데이터를 준비 중입니다.\"\r\n")

# render_list_card fallback
list_start = data.index(b"def render_list_card")
entries_line = data.index(b"    entries = lines or ", list_start)
entries_end = data.index(b"\r\n", entries_line)
replace_slice(entries_line, entries_end + 2, "    entries = lines or [\"데이터를 수집하는 중입니다.\"]\r\n")

# Member selector desc map and label
selector_start = data.index(b"def render_member_section_selector")
desc_start = data.index(b"    desc_map = {", selector_start)
desc_end = data.index(b"    }\r\n", desc_start) + len(b"    }\r\n")
desc_block = """    desc_map = {
        \"회원 정보\": \"브랜드 스토리와 핵심 프로그램을 한눈에 제공합니다.\",
        \"이번 주 운동\": \"회원님의 이번 주 루틴과 권장 세션을 정리했습니다.\",
        \"안전 & 재정\": \"결제/정산 상태와 리스크 신호를 조용하게 요약합니다.\",
    }\n""".replace("\n", "\r\n")
replace_slice(desc_start, desc_end, desc_block)
label_line = data.index(b'        "', data.index(b"    selection = st.radio", selector_start))
label_end = data.index(b"\r\n", label_line)
replace_slice(label_line, label_end + 2, "        \"궁금한 내용을 선택하세요.\",\r\n")

# Member timeline defaults
timeline_start = data.index(b"def build_member_schedule_timeline")
days_line = data.index(b"    days = ", timeline_start)
days_end = data.index(b"\r\n", days_line)
replace_slice(days_line, days_end + 2, "    days = [\"월\", \"화\", \"수\", \"목\", \"금\", \"토\", \"일\"]\r\n")
lines_line = data.index(b"    lines = program_lines", timeline_start)
lines_end = data.index(b"\r\n", lines_line)
replace_slice(lines_line, lines_end + 2, "    lines = program_lines or [\"시그니처 루틴 · 리듬을 유지하세요\"]\r\n")
info_line = data.index(b"        st.info(", timeline_start)
info_end = data.index(b"\r\n", info_line)
replace_slice(info_line, info_end + 2, "        st.info(\"스케줄 정보를 준비하는 중입니다.\")\r\n")

# Member academy block replacements
academy_start = data.index(b"def render_member_academy_section")
title_line = data.index(b'render_text_card("', academy_start)
title_end = data.index(b"\r\n", title_line)
replace_slice(title_line, title_end + 2, "    render_text_card(\"학원 스토리\", story, footer=f\"{studio_id} · GraphRAG 신호\")\r\n")
context_line = data.index(b"    context = model.get(\"profile_context\")", academy_start)
context_end = data.index(b"\r\n", context_line)
replace_slice(context_line, context_end + 2, "    context = model.get(\"profile_context\") or [\"회원 컨텍스트를 준비하는 중입니다.\"]\r\n")
card1 = data.index(b"    render_list_card(", academy_start)
card1_end = data.index(b"\r\n", card1)
replace_slice(card1, card1_end + 2, "    render_list_card(\"계정 컨텍스트\", context)\r\n")
card2 = data.index(b"    render_list_card(", card1 + 10)
card2_end = data.index(b"\r\n", card2)
replace_slice(card2, card2_end + 2, "    render_list_card(\"대표 프로그램 & 트레이너\", model.get(\"program_lines\") or [])\r\n")
segment_line = data.index(b"    segment = ", academy_start)
segment_end = data.index(b"\r\n", segment_line)
replace_slice(segment_line, segment_end + 2, "    segment = context[0] if context else \"회원\"\r\n")
col1_line = data.index(b"    render_metric_card(col1", academy_start)
col1_end = data.index(b"\r\n", col1_line)
replace_slice(col1_line, col1_end + 2, "    render_metric_card(col1, \"그래프 문서\", f\"{documents:,}\", \"학습된 자료\")\r\n")
col2_line = data.index(b"    render_metric_card(col2", academy_start)
col2_end = data.index(b"\r\n", col2_line)
replace_slice(col2_line, col2_end + 2, "    render_metric_card(col2, \"모달리티\", f\"{len(modalities)}개\", \"주요 루틴\")\r\n")
col3_line = data.index(b"    render_metric_card(col3", academy_start)
col3_end = data.index(b"\r\n", col3_line)
replace_slice(col3_line, col3_end + 2, "    render_metric_card(col3, \"회원 세그먼트\", segment, \"Apple Fitness+ 톤\")\r\n")

# Member schedule section
schedule_start = data.index(b"def render_member_schedule_section")
sc_col1 = data.index(b"    render_metric_card(col1", schedule_start)
sc_col1_end = data.index(b"\r\n", sc_col1)
replace_slice(sc_col1, sc_col1_end + 2, "    render_metric_card(col1, \"이번 달 세션\", f\"{activity['sessions']}회\", activity.get(\"sessions_note\"))\r\n")
sc_col2 = data.index(b"    render_metric_card(col2", schedule_start)
sc_col2_end = data.index(b"\r\n", sc_col2)
replace_slice(sc_col2, sc_col2_end + 2, "    render_metric_card(col2, \"누적 운동 시간\", f\"{activity['minutes']}분\", activity.get(\"minutes_note\"))\r\n")
sc_col3 = data.index(b"    render_metric_card(col3", schedule_start)
sc_col3_end = data.index(b"\r\n", sc_col3)
replace_slice(sc_col3, sc_col3_end + 2, "    render_metric_card(col3, \"목표 달성률\", f\"{activity['goal']}%\", activity[\"recommendation\"])\r\n")
section_line = data.index(b"    st.markdown(\"<div class='lop-section-title'>", schedule_start)
section_end = data.index(b"\r\n", section_line)
replace_slice(section_line, section_end + 2, "    st.markdown(\"<div class='lop-section-title'>이번 주 일정</div>\", unsafe_allow_html=True)\r\n")
list1 = data.index(b"    render_list_card(\"", schedule_start)
list1_end = data.index(b"\r\n", list1)
replace_slice(list1, list1_end + 2, "    render_list_card(\"추천 프로그램 / 트레이너\", model.get(\"program_lines\") or [])\r\n")
list2 = data.index(b"    render_list_card(\"", list1 + 10)
list2_end = data.index(b"\r\n", list2)
replace_slice(list2, list2_end + 2, "    render_list_card(\"다음 주를 위한 제안\", model.get(\"coach_tips\") or [])\r\n")
text_summary = data.index(b"    render_text_card(\"", schedule_start)
text_summary_end = data.index(b"\r\n", text_summary)
replace_slice(text_summary, text_summary_end + 2, "    render_text_card(\"나의 그래프 요약\", model.get(\"graph_summary\"))\r\n")

# Safety metrics strings
safety_start = data.index(b"def build_member_safety_metrics")
status_line = data.index(b"        status = ", safety_start)
status_end = data.index(b"\r\n", status_line)
replace_slice(status_line, status_end + 2, "        status = \"안정\"\r\n")
status_copy_line = data.index(b"        status_copy = ", safety_start)
status_copy_end = data.index(b"\r\n", status_copy_line)
replace_slice(status_copy_line, status_copy_end + 2, "        status_copy = \"결제·정산 흐름이 안정적이에요.\"\r\n")
status2_line = data.index(b"        status = ", status_copy_end)
status2_end = data.index(b"\r\n", status2_line)
replace_slice(status2_line, status2_end + 2, "        status = \"주의\"\r\n")
status2_copy_line = data.index(b"        status_copy = ", status2_end)
status2_copy_end = data.index(b"\r\n", status2_copy_line)
replace_slice(status2_copy_line, status2_copy_end + 2, "        status_copy = \"한두 건의 결제 확인만 하면 완벽해요.\"\r\n")
status3_line = data.index(b"        status = ", status2_copy_end)
status3_end = data.index(b"\r\n", status3_line)
replace_slice(status3_line, status3_end + 2, "        status = \"집중 케어\"\r\n")
status3_copy_line = data.index(b"        status_copy = ", status3_end)
status3_copy_end = data.index(b"\r\n", status3_copy_line)
replace_slice(status3_copy_line, status3_copy_end + 2, "        status_copy = \"코치와 함께 리스크를 빠르게 점검해보세요.\"\r\n")
alerts_line = data.index(b"    alerts = ", safety_start)
alerts_end = data.index(b"\r\n", alerts_line)
replace_slice(alerts_line, alerts_end + 2, "    alerts = build_alert_messages(risk) if risk else [\"현재는 안정적인 상태입니다.\"]\r\n")

# Operator metrics block
ops_line = data.index(b"    render_metric_card(col1, \"Revenue Pulse\")")
ops_end = data.index(b"\r\n", ops_line)
replace_slice(ops_line, ops_end + 2, "    render_metric_card(col1, \"Revenue Pulse\", format_currency(metrics[\"monthly_revenue\"]), \"정산 지표\")\r\n")
sub_line = data.index(b"        \"Subscription Health\",", ops_end)
sub_end = data.index(b"\r\n", sub_line + 1)
replace_slice(sub_line, sub_end + 2, "        \"Subscription Health\",\r\n        f\"{metrics['active_subscribers']:,}명\",\r\n        \"활성 구독자\",\r\n")
risk_line = data.index(b"        \"Risk Index\",", sub_end)
risk_end = data.index(b"\r\n", risk_line + 1)
replace_slice(risk_line, risk_end + 2, "        \"Risk Index\",\r\n        f\"{metrics['risk_pct']}%\",\r\n        f\"{metrics['status']} · {metrics['status_copy']}\",\r\n")
list_alerts_line = data.index(b"    render_list_card(\"", risk_end)
list_alerts_end = data.index(b"\r\n", list_alerts_line)
replace_slice(list_alerts_line, list_alerts_end + 2, "    render_list_card(\"시그널 & 가이드\", metrics[\"alerts\"])\r\n")
text_alert_line = data.index(b"    render_text_card(\"", list_alerts_end)
text_alert_end = data.index(b"\r\n", text_alert_line)
replace_slice(text_alert_line, text_alert_end + 2, "    render_text_card(\"LLM 안전 브리핑\", explanation.get(\"message\"))\r\n")

path.write_bytes(data)
