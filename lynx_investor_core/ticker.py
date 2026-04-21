"""Ticker / ISIN / name resolution.

Each agent passes ``suggestions`` so the error message for unresolved queries
shows sector-appropriate ticker examples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

import yfinance as yf
from rich.console import Console
from rich.table import Table

console = Console(stderr=True)

EXCHANGE_SUFFIXES = [
    "", ".V", ".TO", ".DE", ".L", ".PA", ".AS", ".MI", ".SW", ".VI",
    ".AX", ".HK", ".SI", ".F", ".BR", ".ST", ".CO", ".OL", ".HE",
    ".MC", ".LS", ".WA", ".JK", ".NS", ".BO", ".TW", ".KS", ".T",
    ".MX", ".SA",
]


@dataclass
class SearchResult:
    symbol: str
    name: str
    exchange: str
    quote_type: str
    score: float = 0.0


def is_isin(code: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", code.strip().upper()))


def resolve_identifier(
    identifier: str,
    *,
    suggestions: Optional[Iterable[str]] = None,
) -> tuple[str, str | None]:
    raw = identifier.strip()
    upper = raw.upper()
    looks_like_name = " " in raw or len(raw) > 12

    if is_isin(upper):
        result = _search_best_equity(upper)
        if result:
            console.print(f"[dim]ISIN resolved to:[/] {result.symbol} ({result.name}) on {result.exchange}")
            return result.symbol, upper
        raise ValueError(f"Could not resolve ISIN '{upper}' to any ticker.")

    if looks_like_name:
        result = _search_best_equity(raw)
        if result:
            console.print(f"[dim]Search resolved '{raw}' -> {result.symbol} ({result.name}) on {result.exchange}[/]")
            return result.symbol, None
        raise ValueError(f"Could not find any company matching '{raw}'.")

    ticker_candidate = _try_direct_ticker(upper)
    if ticker_candidate:
        return ticker_candidate, None

    result = _search_best_equity(raw)
    if result:
        console.print(f"[dim]Search resolved '{raw}' -> {result.symbol} ({result.name}) on {result.exchange}[/]")
        return result.symbol, None

    if "." not in upper:
        for suffix in EXCHANGE_SUFFIXES:
            if not suffix:
                continue
            found = _try_direct_ticker(upper + suffix)
            if found:
                console.print(f"[dim]Resolved {raw} -> {found} (via suffix {suffix})[/]")
                return found, None

    for extra_query in [f"{raw} stock", f"{raw} corp"]:
        result = _search_best_equity(extra_query)
        if result:
            console.print(f"[dim]Search resolved '{raw}' -> {result.symbol} ({result.name}) on {result.exchange}[/]")
            return result.symbol, None

    tips_block = "\n".join(suggestions) if suggestions else (
        "  - Try a full company name, or a specific exchange suffix."
    )
    raise ValueError(
        f"Could not find any company matching '{raw}'.\n"
        f"Tips:\n{tips_block}"
    )


def search_companies(query: str, max_results: int = 10) -> list[SearchResult]:
    try:
        s = yf.Search(query)
        quotes = s.quotes or []
    except Exception:
        return []
    results: list[SearchResult] = []
    for q in quotes[:max_results]:
        results.append(SearchResult(
            symbol=q.get("symbol", ""),
            name=q.get("longname") or q.get("shortname", ""),
            exchange=q.get("exchDisp") or q.get("exchange", ""),
            quote_type=q.get("quoteType", ""),
            score=q.get("score", 0),
        ))
    return results


def display_search_results(results: list[SearchResult]) -> None:
    t = Table(title="Search Results", border_style="cyan")
    t.add_column("#", style="dim", width=3)
    t.add_column("Symbol", style="bold cyan", min_width=12)
    t.add_column("Name", min_width=30)
    t.add_column("Exchange", min_width=15)
    t.add_column("Type", min_width=8)
    for i, r in enumerate(results, 1):
        t.add_row(str(i), r.symbol, r.name, r.exchange, r.quote_type)
    console.print(t)


def validate_ticker(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info or {}
    name = info.get("longName") or info.get("shortName")
    if not name:
        raise ValueError(f"Could not find company data for ticker '{ticker}'.")
    return info


def _try_direct_ticker(symbol: str) -> Optional[str]:
    import logging
    _loggers = ["yfinance", "peewee", "urllib3", "urllib3.connectionpool"]
    saved = {}
    for name in _loggers:
        logger = logging.getLogger(name)
        saved[name] = logger.level
        logger.setLevel(logging.CRITICAL + 1)
    try:
        t = yf.Ticker(symbol)
        info = t.info
        if not info:
            return None
        has_price = info.get("regularMarketPrice") is not None or info.get("currentPrice") is not None
        has_name = bool(info.get("longName") or info.get("shortName"))
        if has_price and has_name:
            return symbol
        if has_name and info.get("marketCap"):
            return symbol
    except Exception:
        pass
    finally:
        for name, level in saved.items():
            logging.getLogger(name).setLevel(level)
    return None


def _search_best_equity(query: str) -> Optional[SearchResult]:
    results = search_companies(query, max_results=15)
    if not results:
        return None
    query_upper = query.strip().upper()
    equities = [r for r in results if r.quote_type == "EQUITY"]
    if equities:
        exact = [r for r in equities if r.symbol.upper().split(".")[0] == query_upper or r.symbol.upper() == query_upper]
        if exact:
            primary = _filter_primary(exact)
            return primary[0] if primary else exact[0]
        primary = _filter_primary(equities)
        if primary:
            return primary[0]
        return equities[0]
    non_fund = [r for r in results if r.quote_type not in ("MUTUALFUND",)]
    if non_fund:
        return non_fund[0]
    return results[0]


_PRIMARY_EXCHANGES = {
    "NMS", "NYQ", "NYSE", "NASDAQ", "NGM", "NCM", "NIM",
    "CDNX", "VAN", "TOR", "Toronto",
    "OTC Markets", "OQB", "OQX", "PNK",
    "GER", "XETRA", "LSE", "London", "PAR", "Paris",
    "AMS", "Amsterdam", "MIL", "Milan", "EBS", "SIX",
    "ASX", "Australian", "HKG", "Hong Kong",
}


def _filter_primary(results: list[SearchResult]) -> list[SearchResult]:
    return [r for r in results if r.exchange in _PRIMARY_EXCHANGES]
