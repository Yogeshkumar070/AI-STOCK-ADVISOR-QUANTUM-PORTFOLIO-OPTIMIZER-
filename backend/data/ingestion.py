from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
for path in (PROJECT_ROOT, BACKEND_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

try:
    from backend.data.vector_db import collection
except ModuleNotFoundError:
    from data.vector_db import collection


RAW_PDF_DIR = Path(__file__).resolve().parent / "raw_pdfs"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n".join(pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks


def infer_year_from_name(file_name: str) -> int | None:
    match = re.search(r"(20\d{2})", file_name)
    if match:
        return int(match.group(1))
    return None


def ingest_ticker_folder(ticker_dir: Path) -> int:
    ticker = ticker_dir.name.upper()
    pdf_files = sorted(ticker_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found for {ticker}.")
        return 0

    documents = []
    ids = []
    metadatas = []

    for pdf_path in pdf_files:
        text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(text)
        year = infer_year_from_name(pdf_path.name)

        for index, chunk in enumerate(chunks):
            doc_id = f"{ticker}_{pdf_path.stem}_{index}"
            documents.append(chunk)
            ids.append(doc_id)
            metadatas.append(
                {
                    "ticker": ticker,
                    "source_file": pdf_path.name,
                    "chunk_index": index,
                    "year": year,
                }
            )

    if not ids:
        print(f"No readable text extracted for {ticker}.")
        return 0

    existing = set(collection.get(ids=ids).get("ids", []))
    new_documents = []
    new_ids = []
    new_metadatas = []

    for doc_id, document, metadata in zip(ids, documents, metadatas):
        if doc_id not in existing:
            new_documents.append(document)
            new_ids.append(doc_id)
            new_metadatas.append(metadata)

    if new_ids:
        collection.add(documents=new_documents, metadatas=new_metadatas, ids=new_ids)

    print(f"Successfully stored {len(new_ids)} chunks in ChromaDB for {ticker}!")
    return len(new_ids)


def main() -> None:
    total = 0
    for ticker_dir in sorted(RAW_PDF_DIR.iterdir()):
        if ticker_dir.is_dir():
            total += ingest_ticker_folder(ticker_dir)
    print(f"Vectorization complete. Added {total} total chunks.")


if __name__ == "__main__":
    main()
