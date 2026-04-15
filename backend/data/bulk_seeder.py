import time
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
for path in (PROJECT_ROOT, BACKEND_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from backend.data.vector_db import collection

TOP_STOCKS = [
    "RELIANCE", "TCS", "INFY", "ICICIBANK", "SBIN",
    "HINDUNILVR", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "BHARTIARTL", "BAJFINANCE", "MARUTI", "ASIANPAINT", "HCLTECH"
]


def generate_mock_transcript(ticker: str):
    """
    Creates realistic transcript chunks using standard YFinance-friendly jargon.
    Using target year 2024 so it successfully audits against current Yahoo data.
    """
    return [
        f"Operator: Welcome to the {ticker} Q1 2023 Earnings Call.",
        f"CEO: We are confident in our execution. Looking ahead, we expect our Total Revenue to grow by approximately 12.5% as we move into 2024.",
        f"CFO: Furthermore, despite macro headwinds, we project our Net Income to expand by 15% year-over-year in 2024.",
        f"CEO: Our operational efficiency remains strong, and we guide for Operating Income growth of 10% next year."
    ]


def seed_database():
    print("--- INITIATING FINNET BULK SEEDER ---")
    for ticker in TOP_STOCKS:
        print(f"Seeding transcript data for {ticker}...")
        chunks = generate_mock_transcript(ticker)

        ids = [f"{ticker}_seed_2023_{i}" for i in range(len(chunks))]
        metadatas = [{"ticker": ticker, "year": 2023, "source": "synthetic_seed"} for _ in chunks]

        existing_ids = set(collection.get(ids=ids).get("ids", []))
        documents = []
        pending_ids = []
        pending_metadatas = []

        for doc_id, chunk, metadata in zip(ids, chunks, metadatas):
            if doc_id not in existing_ids:
                documents.append(chunk)
                pending_ids.append(doc_id)
                pending_metadatas.append(metadata)

        if pending_ids:
            collection.add(
                documents=documents,
                metadatas=pending_metadatas,
                ids=pending_ids
            )
        time.sleep(0.5)

    print("BULK SEEDING COMPLETE. The AI now has data for 15 major stocks.")


if __name__ == "__main__":
    seed_database()
