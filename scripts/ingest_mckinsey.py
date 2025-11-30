"""Ingest McKinsey PDFs into the local vector store."""
from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Dict, List

from PyPDF2 import PdfReader

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.config import get_settings
from app.services.vector_service import VectorService

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
PDF_DIR = BASE_DIR / "Mckinsey"


def load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        texts.append(page_text)
    return "\n".join(texts)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    tokens = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunk = " ".join(tokens[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(tokens):
            break
        start = max(end - overlap, 0)
    return chunks


def build_docs(pdf_path: Path) -> List[Dict[str, str]]:
    raw_text = load_pdf_text(pdf_path)
    chunks = chunk_text(raw_text)
    docs: List[Dict[str, str]] = []
    for idx, chunk in enumerate(chunks):
        doc_id = f"mckinsey-{pdf_path.stem}-{idx}"
        docs.append({
            "id": doc_id,
            "content": chunk,
            "metadata": {
                "source": str(pdf_path),
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "title": pdf_path.stem.replace("-", " "),
            },
        })
    return docs


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing in environment/.env")
    vector_service = VectorService(settings.chroma_path)
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError("No PDFs found in Mckinsey directory")
    all_docs: List[Dict[str, str]] = []
    for pdf in pdf_files:
        docs = build_docs(pdf)
        all_docs.extend(docs)
        print(f"Parsed {pdf.name}: {len(docs)} chunks")
    vector_service.add_documents(all_docs)
    print(f"Indexed {len(all_docs)} chunks into vector store at {settings.chroma_path}")


if __name__ == "__main__":
    main()
