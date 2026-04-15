from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from tqdm import tqdm


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/",
    "Origin": "https://www.bseindia.com",
}

NIFTY_SCRIP_CODES = {
    "RELIANCE": "500325",
    "TCS": "532540",
    "HDFCBANK": "500180",
    "INFY": "500209",
    "LT": "500510",
}

RAW_PDF_DIR = Path(__file__).resolve().parent / "raw_pdfs"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.bseindia.com/", timeout=60)
    except Exception:
        pass
    return session


def download_pdf(url: str, filepath: Path) -> bool:
    """Stream the PDF download so large files do not blow up memory."""
    response = requests.get(url, headers=HEADERS, stream=True, timeout=60)
    if response.status_code != 200:
        return False

    total_size = int(response.headers.get("content-length", 0))
    with filepath.open("wb") as file, tqdm(
        desc=filepath.name,
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            if not data:
                continue
            size = file.write(data)
            bar.update(size)
    return True


def fetch_transcripts(ticker: str, scrip_code: str, session: requests.Session) -> None:
    """Hit the BSE announcements API and download transcript-like PDFs."""
    print(f"\nScanning BSE Database for {ticker}...")

    ticker_dir = RAW_PDF_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)

    api_url = (
        "https://api.bseindia.com/BseIndiaAPI/api/Announcements/w"
        "?pageno=1&strCat=-1&strPrevDate=20200101"
        f"&strScrip={scrip_code}&strSearch=p&strToDate=20260405&strType=C"
    )

    try:
        response = session.get(api_url, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            snippet = response.text.strip().replace("\n", " ")[:180]
            raise RuntimeError(
                "BSE announcements endpoint returned non-JSON content. "
                f"Content-Type={content_type!r}. Response preview: {snippet}"
            )

        data = response.json()

        if "Table" not in data or not data["Table"]:
            print(f"No announcements found for {ticker}.")
            return

        download_count = 0
        for item in data["Table"]:
            headline = str(item.get("NEWSSUB", "")).lower()

            if "transcript" in headline or "earnings call" in headline:
                pdf_link = item.get("ATTACHMENTNAME")
                news_dt = str(item.get("NEWS_DT", ""))
                date_str = news_dt[:4] if news_dt else "unknown"

                if pdf_link:
                    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_link}"
                    filename = f"{date_str}_Earnings_Call.pdf"
                    filepath = ticker_dir / filename

                    if not filepath.exists():
                        print(f"  -> Found {date_str} transcript. Downloading...")
                        success = download_pdf(pdf_url, filepath)
                        if success:
                            download_count += 1
                        else:
                            print(f"  -> Download failed for {pdf_url}")
                        time.sleep(2)

        if download_count == 0:
            print(f"  -> Already up to date for {ticker}.")
        else:
            print(f"  -> Downloaded {download_count} transcript(s) for {ticker}.")

    except Exception as exc:
        print(f"Failed to scrape {ticker}: {exc}")


if __name__ == "__main__":
    print("INITIALIZING FINNET AUTO-DOWNLOADER...")
    os.makedirs(RAW_PDF_DIR, exist_ok=True)
    session = create_session()

    for ticker, scrip_code in NIFTY_SCRIP_CODES.items():
        fetch_transcripts(ticker, scrip_code, session)
        time.sleep(5)

    print("\nDOWNLOAD COMPLETE. Ready for Vectorization.")
