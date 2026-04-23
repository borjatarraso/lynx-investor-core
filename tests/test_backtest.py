"""Tests for :mod:`lynx_investor_core.backtest`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lynx_investor_core import backtest, charts


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

class TestStatsHelpers:
    def test_max_drawdown_uptrend(self) -> None:
        values = [100, 110, 120, 130, 140]
        assert backtest.max_drawdown_pct(values) == 0.0

    def test_max_drawdown_crash(self) -> None:
        values = [100, 150, 75]
        # peak 150 -> trough 75: -50%
        assert backtest.max_drawdown_pct(values) == pytest.approx(-50.0)

    def test_volatility_zero_for_flat(self) -> None:
        returns = [0.0, 0.0, 0.0]
        assert backtest.volatility_pct(returns) == 0.0

    def test_sharpe_zero_returns(self) -> None:
        assert backtest.sharpe_ratio([]) == 0.0

    def test_beta_perfect_correlation(self) -> None:
        # Identical series → beta = 1
        r = [0.01, -0.01, 0.02, -0.02, 0.005]
        assert backtest.beta(r, r) == pytest.approx(1.0)

    def test_beta_none_on_zero_variance(self) -> None:
        assert backtest.beta([0.0] * 5, [0.0] * 5) is None

    def test_correlation_perfect(self) -> None:
        r = [0.01, 0.02, 0.03, 0.04, 0.05]
        assert backtest.correlation(r, r) == pytest.approx(1.0)

    def test_correlation_inverse(self) -> None:
        r = [0.01, 0.02, 0.03, 0.04, 0.05]
        inv = [-x for x in r]
        assert backtest.correlation(r, inv) == pytest.approx(-1.0)

    def test_alpha_is_simple_difference(self) -> None:
        assert backtest.alpha_pct(20.0, 8.0) == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# Backtest integration — mock fetch_price_history
# ---------------------------------------------------------------------------

def _fake_series(n: int, start: float, step: float):
    dates = [f"2020-01-{i+1:02d}" for i in range(min(n, 30))] + [
        f"2020-02-{i+1:02d}" for i in range(max(0, n - 30))
    ]
    closes = [start + i * step for i in range(n)]
    return dates[:n], closes


class TestRunBacktest:
    def test_empty_tickers(self) -> None:
        result = backtest.run_backtest([])
        assert result.final_value == 10000.0
        assert result.total_return_pct == 0.0

    def test_equal_weight_single_ticker(self) -> None:
        with patch.object(
            charts, "fetch_price_history",
            return_value=_fake_series(100, 100.0, 1.0),
        ):
            result = backtest.run_backtest(["AAPL"], initial_capital=1000.0)
        # Price goes from 100 to 199 — final value ≈ 10 shares * 199 = 1990
        assert result.final_value == pytest.approx(1990.0)
        assert result.total_return_pct == pytest.approx(99.0)

    def test_equal_weight_two_tickers_no_skip(self) -> None:
        def side_effect(ticker, *, period="1y", interval=None):
            if ticker == "AAA":
                return _fake_series(50, 100.0, 2.0)
            return _fake_series(50, 200.0, 1.0)

        with patch.object(charts, "fetch_price_history", side_effect=side_effect):
            result = backtest.run_backtest(["AAA", "BBB"], initial_capital=1000.0)
        # Both stocks gain but by different amounts
        assert result.final_value > 1000.0
        assert result.skipped_tickers == []
        assert result.weights == pytest.approx([0.5, 0.5])

    def test_skipped_tickers_on_no_data(self) -> None:
        def side_effect(ticker, *, period="1y", interval=None):
            return ([], [])
        with patch.object(charts, "fetch_price_history", side_effect=side_effect):
            result = backtest.run_backtest(["UNKNOWN"])
        assert "UNKNOWN" in result.skipped_tickers
        assert result.final_value == 10000.0  # untouched

    def test_rebalance_monthly_runs(self) -> None:
        with patch.object(
            charts, "fetch_price_history",
            return_value=_fake_series(60, 100.0, 1.0),
        ):
            result = backtest.run_backtest(
                ["T"], initial_capital=1000.0, rebalance="monthly",
            )
        # Sanity — at least computed some value history
        assert len(result.value_history) > 0


# ---------------------------------------------------------------------------
# Benchmark comparison
# ---------------------------------------------------------------------------

class TestBenchmarkComparison:
    def test_insufficient_data(self) -> None:
        with patch.object(charts, "fetch_price_history", return_value=([], [])):
            result = backtest.compare_to_benchmark(
                ["2020-01-01"], [100.0], "^GSPC",
            )
        assert result.portfolio_return_pct == 0.0
        assert result.correlation is None

    def test_full_comparison(self) -> None:
        port_dates = [f"2020-01-{i+1:02d}" for i in range(30)]
        port_values = [100.0 + i for i in range(30)]
        bench_dates = port_dates[:]
        bench_closes = [200.0 + i * 0.5 for i in range(30)]

        with patch.object(
            charts, "fetch_price_history",
            return_value=(bench_dates, bench_closes),
        ):
            result = backtest.compare_to_benchmark(
                port_dates, port_values, "^GSPC",
            )
        # Portfolio went from 100 to 129 → +29%
        # Bench went from 200 to 214.5 → +7.25%
        # Alpha ≈ +21.75%
        assert result.portfolio_return_pct == pytest.approx(29.0)
        assert result.benchmark_return_pct == pytest.approx(7.25)
        assert result.alpha_pct == pytest.approx(21.75)
        assert result.beta is not None
        assert result.correlation is not None


class TestHistoricalBenchmark:
    def test_empty_positions(self) -> None:
        result = backtest.historical_benchmark([], "^GSPC")
        assert result.portfolio_return_pct == 0.0

    def test_single_position(self) -> None:
        # mock every fetch to return the same simple rising series
        def side_effect(ticker, *, period="5y", interval=None):
            return _fake_series(50, 100.0, 1.0)
        with patch.object(charts, "fetch_price_history", side_effect=side_effect):
            result = backtest.historical_benchmark(
                [("AAPL", 1000.0)], "^GSPC",
            )
        assert result.portfolio_return_pct == pytest.approx(49.0)  # 100 → 149
        assert result.alpha_pct == pytest.approx(0.0)  # same series
