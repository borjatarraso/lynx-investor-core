"""SEC EDGAR and regulatory report fetching.

Each agent supplies ``user_agent_product`` so SEC EDGAR and HTTP requests
identify the specific agent (``"LynxMining"``, ``"LynxEnergy"``, etc.) — SEC
access policy requires a unique product identifier per client.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Protocol

import requests
import yfinance as yf

from lynx_investor_core.storage import get_reports_dir, save_binary, save_json, save_text

EDGAR_BASE = "https://data.sec.gov"
TARGET_FORMS = {"10-K", "10-Q", "20-F", "6-K", "8-K", "10-K/A", "10-Q/A"}


class FilingLike(Protocol):
    form_type: str
    filing_date: str
    period: str
    url: str
    description: str
    local_path: Optional[str]


@dataclass
class _FilingSeed:
    form_type: str
    filing_date: str
    period: str
    url: str
    description: str


def _build_headers(user_agent_product: str) -> tuple[dict, dict]:
    ua_download = {
        "User-Agent": f"Mozilla/5.0 (compatible; {user_agent_product}/0.1)",
        "Accept-Encoding": "gzip, deflate",
    }
    ua_edgar = {
        "User-Agent": f"{user_agent_product}/0.1 {user_agent_product.lower()}-research@example.com",
        "Accept-Encoding": "gzip, deflate",
    }
    return ua_download, ua_edgar


def fetch_sec_filings(
    ticker: str,
    filing_factory,
    *,
    user_agent_product: str,
) -> list:
    """Discover SEC filings for *ticker* and return ``filing_factory(...)`` results.

    ``filing_factory`` is a callable with the same signature as the agent's
    ``Filing`` dataclass so that core never imports domain-specific models.
    """
    _, edgar_headers = _build_headers(user_agent_product)
    seeds = _fetch_via_yfinance(ticker)
    if not seeds:
        seeds = _fetch_via_edgar(ticker, edgar_headers)
    filings = [
        filing_factory(
            form_type=s.form_type,
            filing_date=s.filing_date,
            period=s.period,
            url=s.url,
            description=s.description,
        )
        for s in seeds
    ]
    if filings:
        rdir = get_reports_dir(ticker)
        save_json(rdir / "filings_index.json", [
            {"form": f.form_type, "date": f.filing_date, "period": f.period, "url": f.url}
            for f in filings
        ])
    return filings


def _fetch_via_yfinance(ticker: str) -> list[_FilingSeed]:
    seeds: list[_FilingSeed] = []
    try:
        t = yf.Ticker(ticker)
        sec_filings = t.sec_filings
        if not sec_filings:
            return seeds
        for item in sec_filings:
            form_type = item.get("type", "")
            if form_type not in TARGET_FORMS:
                continue
            filing_date = str(item.get("date", ""))
            url = ""
            exhibits = item.get("exhibits", {})
            for key in [form_type, form_type.replace("/", ""), "htm", "html"]:
                if key in exhibits:
                    url = exhibits[key]
                    break
            if not url and exhibits:
                url = next(iter(exhibits.values()), "")
            if not url:
                url = item.get("edgarUrl", "")
            seeds.append(_FilingSeed(
                form_type=form_type, filing_date=filing_date, period=filing_date, url=url,
                description=item.get("title", f"{form_type} filed {filing_date}"),
            ))
    except Exception:
        pass
    return seeds


def _fetch_via_edgar(ticker: str, edgar_headers: dict) -> list[_FilingSeed]:
    cik = _resolve_cik(ticker, edgar_headers)
    if not cik:
        return []
    cik_padded = cik.zfill(10)
    try:
        resp = requests.get(f"{EDGAR_BASE}/submissions/CIK{cik_padded}.json", headers=edgar_headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    seeds: list[_FilingSeed] = []
    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return seeds
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    periods = recent.get("reportDate", [])
    for i, form in enumerate(forms):
        if form not in TARGET_FORMS or i >= len(accessions):
            continue
        accession = accessions[i].replace("-", "")
        doc = primary_docs[i] if i < len(primary_docs) else ""
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"
        seeds.append(_FilingSeed(
            form_type=form, filing_date=dates[i] if i < len(dates) else "",
            period=periods[i] if i < len(periods) else "", url=filing_url,
            description=f"{form} filed {dates[i] if i < len(dates) else 'N/A'}",
        ))
    return seeds


def download_filing(
    ticker: str,
    filing: FilingLike,
    *,
    user_agent_product: str,
    max_size_mb: int = 20,
) -> Optional[str]:
    if not filing.url:
        return None
    download_headers, _ = _build_headers(user_agent_product)
    rdir = get_reports_dir(ticker)
    safe_date = (filing.filing_date or "unknown").replace("-", "")
    filename = f"{filing.form_type.replace('/', '_')}_{safe_date}"
    try:
        resp = requests.get(filing.url, headers=download_headers, timeout=60)
        resp.raise_for_status()
        content = resp.content
        if len(content) > max_size_mb * 1024 * 1024:
            return None
        content_type = resp.headers.get("content-type", "")
        if "pdf" in content_type or filing.url.endswith(".pdf"):
            path = rdir / f"{filename}.pdf"
            save_binary(path, content)
        else:
            path = rdir / f"{filename}.html"
            save_text(path, content.decode("utf-8", errors="replace"))
        filing.local_path = str(path)
        return str(path)
    except Exception:
        return None


def download_top_filings(
    ticker: str,
    filings: list,
    *,
    user_agent_product: str,
    max_count: int = 10,
) -> list:
    downloaded = []
    for filing in filings[:max_count]:
        path = download_filing(ticker, filing, user_agent_product=user_agent_product)
        if path:
            filing.local_path = path
            downloaded.append(filing)
        time.sleep(0.15)
    return downloaded


def _resolve_cik(ticker: str, edgar_headers: dict) -> Optional[str]:
    try:
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=edgar_headers, timeout=15)
        if resp.status_code == 200:
            for entry in resp.json().values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"])
    except Exception:
        pass
    return None
