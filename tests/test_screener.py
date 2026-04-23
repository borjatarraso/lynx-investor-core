"""Tests for :mod:`lynx_investor_core.screener`."""

from __future__ import annotations

import pytest

from lynx_investor_core import screener


# ---------------------------------------------------------------------------
# Fake fetcher — deterministic universe for testing
# ---------------------------------------------------------------------------

_UNIVERSE = {
    "AAPL": {
        "market_cap": 3_500_000_000_000, "pe_trailing": 30.1, "pb_ratio": 50.0,
        "dividend_yield": 0.004, "roe": 1.5, "profit_margin": 0.25,
        "sector": "Technology", "industry": "Consumer Electronics",
        "country": "United States", "name": "Apple Inc.",
    },
    "MSFT": {
        "market_cap": 3_000_000_000_000, "pe_trailing": 35.0, "pb_ratio": 11.5,
        "dividend_yield": 0.008, "roe": 0.45, "profit_margin": 0.36,
        "sector": "Technology", "industry": "Software",
        "country": "United States", "name": "Microsoft Corp.",
    },
    "JNJ": {
        "market_cap": 380_000_000_000, "pe_trailing": 15.5, "pb_ratio": 4.8,
        "dividend_yield": 0.031, "roe": 0.21, "profit_margin": 0.18,
        "sector": "Healthcare", "industry": "Drug Manufacturers",
        "country": "United States", "name": "Johnson & Johnson",
    },
    "KO": {
        "market_cap": 260_000_000_000, "pe_trailing": 26.0, "pb_ratio": 10.1,
        "dividend_yield": 0.031, "roe": 0.42, "profit_margin": 0.23,
        "sector": "Consumer Defensive", "industry": "Beverages—Non-Alcoholic",
        "country": "United States", "name": "The Coca-Cola Company",
    },
    "BAD": {
        "market_cap": None, "pe_trailing": None, "pb_ratio": None,
        "dividend_yield": None, "roe": None, "profit_margin": None,
        "sector": "Unknown", "industry": None, "country": None, "name": "Missing Data",
    },
}


def _fake_fetch(ticker):
    if ticker not in _UNIVERSE:
        return None, f"{ticker}: unknown"
    row = {k: None for k in screener.FIELDS}
    row.update(_UNIVERSE[ticker])
    return row, None


class TestFilterValidation:
    def test_unknown_field_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown field"):
            screener.run_screener(["AAPL"], [("noexist", ">", 0)], fetcher=_fake_fetch)

    def test_bad_operator_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported operator"):
            screener.run_screener(["AAPL"], [("pe_trailing", "=~", 10)], fetcher=_fake_fetch)

    def test_bad_arity(self) -> None:
        with pytest.raises(ValueError, match="3-tuple"):
            screener.run_screener(["AAPL"], [("pe_trailing", ">")], fetcher=_fake_fetch)


class TestRunScreener:
    def test_market_cap_filter(self) -> None:
        r = screener.run_screener(
            list(_UNIVERSE), [("market_cap", ">", 1_000_000_000_000)],
            fetcher=_fake_fetch,
        )
        tickers = {row.ticker for row in r.rows}
        assert tickers == {"AAPL", "MSFT"}

    def test_multiple_filters_AND(self) -> None:
        r = screener.run_screener(
            list(_UNIVERSE),
            [
                ("sector", "==", "Technology"),
                ("dividend_yield", ">=", 0.005),
            ],
            fetcher=_fake_fetch,
        )
        assert [row.ticker for row in r.rows] == ["MSFT"]

    def test_in_operator(self) -> None:
        r = screener.run_screener(
            list(_UNIVERSE),
            [("sector", "in", ["Healthcare", "Consumer Defensive"])],
            fetcher=_fake_fetch,
        )
        tickers = {row.ticker for row in r.rows}
        assert tickers == {"JNJ", "KO"}

    def test_contains_operator(self) -> None:
        r = screener.run_screener(
            list(_UNIVERSE),
            [("name", "contains", "apple")],
            fetcher=_fake_fetch,
        )
        assert [row.ticker for row in r.rows] == ["AAPL"]

    def test_skips_missing_data(self) -> None:
        r = screener.run_screener(
            list(_UNIVERSE),
            [("pe_trailing", "<", 50)],
            fetcher=_fake_fetch,
        )
        # BAD has pe_trailing=None — should be skipped, not crash
        assert "BAD" not in {row.ticker for row in r.rows}

    def test_universe_size_reported(self) -> None:
        r = screener.run_screener(
            ["AAPL", "MSFT"], [], fetcher=_fake_fetch,
        )
        assert r.universe_size == 2

    def test_unknown_ticker_recorded_as_error(self) -> None:
        r = screener.run_screener(
            ["XXYZ"], [("market_cap", ">", 0)], fetcher=_fake_fetch,
        )
        assert r.rows == []
        assert any("XXYZ" in e for e in r.errors)

    def test_as_dict_serializable(self) -> None:
        import json
        r = screener.run_screener(
            ["AAPL"], [("market_cap", ">", 0)], fetcher=_fake_fetch,
        )
        json.dumps(r.as_dict())

    def test_fields_subset(self) -> None:
        r = screener.run_screener(
            ["AAPL"], [("market_cap", ">", 0)],
            fields=["name", "market_cap"], fetcher=_fake_fetch,
        )
        assert set(r.rows[0].fields.keys()) == {"name", "market_cap"}
