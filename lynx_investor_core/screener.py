"""Cross-sector screener for the Lince Investor Suite (v5.1).

The screener evaluates a **user-provided universe** of tickers against
numeric / string filters and returns the rows that pass. It is
deliberately simple — the Suite doesn't pretend to be a paid data
vendor with the full US listing in memory — but it's plenty useful for
screening a watchlist, a portfolio, or a hand-curated list of 100
symbols.

Data source: yfinance's ``fast_info`` + ``info`` dictionaries.
Network calls happen lazily inside the screener; callers that want to
screen a very large universe should batch with multiple workers (the
Suite does not: simplicity first).

Filter DSL
----------

A *filter* is one of:

* ``(field, op, value)`` where ``op`` ∈ ``>`` ``>=`` ``<`` ``<=`` ``==``
  ``!=`` and ``value`` is a number or string.
* ``(field, "in", [a, b, ...])`` — value must be in the list.
* ``(field, "contains", "substring")`` — case-insensitive.

Supported fields (subset of yfinance):

* ``market_cap``, ``pe_trailing``, ``pe_forward``, ``pb_ratio``,
  ``dividend_yield``, ``roe``, ``revenue_growth``,
  ``profit_margin``, ``operating_margin``,
  ``price``, ``beta``, ``currency``, ``sector``, ``industry``,
  ``country``, ``name``, ``exchange``.

Result rows are JSON-serializable dicts ready for a Rich table or the
Flask API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


__all__ = [
    "Filter",
    "ScreenerRow",
    "ScreenerResult",
    "FIELDS",
    "run_screener",
]


Filter = Union[Tuple[str, str, Any], Tuple[str, str, List[Any]]]


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

# Maps Suite-level field name → yfinance info.get() key
_FIELD_MAP: Dict[str, str] = {
    "market_cap":      "marketCap",
    "pe_trailing":     "trailingPE",
    "pe_forward":      "forwardPE",
    "pb_ratio":        "priceToBook",
    "ps_ratio":        "priceToSalesTrailing12Months",
    "dividend_yield":  "dividendYield",
    "roe":             "returnOnEquity",
    "roa":             "returnOnAssets",
    "profit_margin":   "profitMargins",
    "operating_margin":"operatingMargins",
    "revenue_growth":  "revenueGrowth",
    "earnings_growth": "earningsQuarterlyGrowth",
    "beta":            "beta",
    "price":           "currentPrice",
    "currency":        "currency",
    "sector":          "sector",
    "industry":        "industry",
    "country":         "country",
    "name":            "longName",
    "exchange":        "exchange",
}

FIELDS: Tuple[str, ...] = tuple(sorted(_FIELD_MAP))

_NUMERIC_FIELDS = frozenset([
    "market_cap", "pe_trailing", "pe_forward", "pb_ratio", "ps_ratio",
    "dividend_yield", "roe", "roa", "profit_margin", "operating_margin",
    "revenue_growth", "earnings_growth", "beta", "price",
])

_ALLOWED_OPS = {">", ">=", "<", "<=", "==", "!=", "in", "contains"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ScreenerRow:
    ticker: str
    fields: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {"ticker": self.ticker, **self.fields}


@dataclass
class ScreenerResult:
    filters: List[Filter]
    universe_size: int
    rows: List[ScreenerRow]
    errors: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "filters": [list(f) for f in self.filters],
            "universe_size": self.universe_size,
            "rows_passed": len(self.rows),
            "rows": [r.as_dict() for r in self.rows],
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def _normalize_filter(f: Filter) -> Filter:
    if len(f) != 3:
        raise ValueError(f"filter must be a 3-tuple, got {f!r}")
    field, op, value = f
    if field not in _FIELD_MAP:
        raise ValueError(f"unknown field '{field}'. Valid fields: {FIELDS}")
    if op not in _ALLOWED_OPS:
        raise ValueError(f"unsupported operator '{op}'. Allowed: {sorted(_ALLOWED_OPS)}")
    return (field, op, value)


def _evaluate(field: str, op: str, value: Any, row_value: Any) -> Optional[bool]:
    """Return True/False/None (None = can't evaluate; row is skipped)."""
    if op == "contains":
        if row_value is None:
            return False
        return str(value).lower() in str(row_value).lower()
    if op == "in":
        if not isinstance(value, (list, tuple, set)):
            return None
        if row_value is None:
            return False
        if field in _NUMERIC_FIELDS:
            try:
                return float(row_value) in [float(v) for v in value]
            except (TypeError, ValueError):
                return False
        return str(row_value).lower() in [str(v).lower() for v in value]

    # numeric / equality
    if row_value is None:
        return None

    if field in _NUMERIC_FIELDS:
        try:
            lhs = float(row_value)
            rhs = float(value)
        except (TypeError, ValueError):
            return None
    else:
        # string comparison — case-insensitive
        lhs = str(row_value).strip().lower()
        rhs = str(value).strip().lower()

    if op == ">":  return lhs > rhs
    if op == ">=": return lhs >= rhs
    if op == "<":  return lhs < rhs
    if op == "<=": return lhs <= rhs
    if op == "==": return lhs == rhs
    if op == "!=": return lhs != rhs
    return None


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def _fetch_row(ticker: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return (fields-dict, error). On success, error is None."""
    try:
        import yfinance as yf
    except ImportError:
        return None, "yfinance not available"
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as exc:
        return None, f"{ticker}: fetch failed ({type(exc).__name__})"

    row = {}
    for suite_key, yf_key in _FIELD_MAP.items():
        val = info.get(yf_key)
        row[suite_key] = val
    return row, None


def run_screener(
    universe: Sequence[str],
    filters: Sequence[Filter],
    *,
    fields: Optional[Sequence[str]] = None,
    fetcher: Optional[Callable[[str], Tuple[Optional[Dict[str, Any]], Optional[str]]]] = None,
) -> ScreenerResult:
    """Screen *universe* (a list of tickers) against *filters*.

    Parameters
    ----------
    universe : tickers to evaluate.
    filters : list of ``(field, op, value)`` tuples. All filters
        must pass for a row to be included.
    fields : subset of :data:`FIELDS` to include in each row. Defaults
        to every field.
    fetcher : inject a custom fetcher — useful for tests. Signature
        ``(ticker) -> (dict_or_None, error_or_None)``.
    """
    universe = [t.strip().upper() for t in universe if t and t.strip()]
    validated: List[Filter] = [_normalize_filter(f) for f in filters]
    selected_fields = list(fields) if fields else list(FIELDS)
    for f in selected_fields:
        if f not in _FIELD_MAP:
            raise ValueError(f"unknown field '{f}'")

    fetch = fetcher or _fetch_row
    rows: List[ScreenerRow] = []
    errors: List[str] = []

    for ticker in universe:
        data, err = fetch(ticker)
        if err:
            errors.append(err)
            continue
        if data is None:
            errors.append(f"{ticker}: no data")
            continue

        keep = True
        for field, op, value in validated:
            verdict = _evaluate(field, op, value, data.get(field))
            if verdict is None or not verdict:
                keep = False
                break
        if keep:
            rows.append(ScreenerRow(
                ticker=ticker,
                fields={k: data.get(k) for k in selected_fields},
            ))

    return ScreenerResult(
        filters=validated,
        universe_size=len(universe),
        rows=rows,
        errors=errors,
    )
