from pathlib import Path

data = Path("streamlit_app.py").read_bytes()
pos = data.index(b"st.error(")
line_end = data.index(b"\r\n", pos)
print(data[pos:line_end])
