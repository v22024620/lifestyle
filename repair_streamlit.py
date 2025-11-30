from pathlib import Path

path = Path("streamlit_app.py")
data = path.read_bytes()

def repl(old: bytes, new: str) -> None:
    global data
    data = data.replace(old, new.encode("utf-8"), 1)

repl(b"    render_metric_card(col1, \"Revenue Pulse\", format_currency(metrics[\"monthly_revenue\"]), \"?\x95\xec\x82\xb0 \xec\xa7\x80??)\r\n",
     "    render_metric_card(col1, \"Revenue Pulse\", format_currency(metrics[\"monthly_revenue\"]), \"정산 지표\")\r\n")
repl(b"        \"Subscription Health\",\r\n        f\"{metrics['active_subscribers']:,:}?\xba\xec\x98??\",\r\n        \"?\xd5\xec\x9b ?\xb4?\",\r\n",
     "        \"Subscription Health\",\r\n        f\"{metrics['active_subscribers']:,:}명\",\r\n        \"활성 구독자\",\r\n")
