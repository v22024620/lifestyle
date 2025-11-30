from pathlib import Path

path = Path("streamlit_app.py")
data = path.read_bytes()
needle = b"        return \"?\xb0\xec\x9d\xb4"
pos = data.index(needle)
line_end = data.index(b"\r\n", pos)
print(data[pos:line_end])
