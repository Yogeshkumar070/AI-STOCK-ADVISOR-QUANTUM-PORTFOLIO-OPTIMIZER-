import sqlite3
import json
from pathlib import Path

# Connect to a local SQLite database file
DB_PATH = Path(__file__).resolve().parent / "finnet_cache.db"
conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
cursor = conn.cursor()

# Create a table to store our AI results if it doesn't exist yet
cursor.execute("""
    CREATE TABLE IF NOT EXISTS mcs_cache (
        ticker TEXT PRIMARY KEY,
        score REAL,
        audit_data JSON,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()


def get_cached_mcs(ticker: str):
    """Checks if we already asked the AI about this stock."""
    cursor.execute("SELECT score, audit_data FROM mcs_cache WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if row:
        return {
            "ticker": ticker,
            "mcs_score": row[0],
            "audits": json.loads(row[1]),
            "cached": True
        }
    return None


def save_mcs_to_cache(ticker: str, score: float, audit_data: list):
    """Saves the AI's hard work so we never pay for this ticker again."""
    cursor.execute("""
        INSERT OR REPLACE INTO mcs_cache (ticker, score, audit_data)
        VALUES (?, ?, ?)
    """, (ticker, score, json.dumps(audit_data)))
    conn.commit()
