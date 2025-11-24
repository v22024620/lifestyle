from pathlib import Path

old = "    flow_cols = st.columns([1.4, 1], gap=\"large\")\n    with flow_cols[0]:\n        st.markdown(\"<div class='lop-section-title'>프로그램 & 구독 흐름</div>\", unsafe_allow_html=True)\n        st.line_chart(model[\"program_flow\"], use_container_width=True, height=260)\n    with flow_cols[1]:\n        render_text_card(\"오늘의 실행 인사이트\", model.get(\"narrative\"))\n\n    action_cols = st.columns(2, gap=\"large\")\n    with action_cols[0]:\n        render_list_card(\"Execution Playbook\", model[\"execution_actions\"])\n    with action_cols[1]:\n        render_list_card(\"Light Alerts\", model[\"alerts\"])\n"

new = "    st.markdown(\"<div class='lop-section-title'>프로그램 & 구독 흐름</div>\", unsafe_allow_html=True)\n    st.line_chart(model[\"program_flow\"], use_container_width=True, height=260)\n\n    render_text_card(\"오늘의 실행 인사이트\", model.get(\"narrative\"))\n\n    render_list_card(\"Execution Playbook\", model[\"execution_actions\"])\n\n    render_list_card(\"Light Alerts\", model[\"alerts\"])\n"

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
