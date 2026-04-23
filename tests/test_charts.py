"""Tests for :mod:`lynx_investor_core.charts`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lynx_investor_core import charts


class TestSparkline:
    def test_empty(self) -> None:
        assert charts.render_sparkline([]) == ""

    def test_constant(self) -> None:
        out = charts.render_sparkline([5.0, 5.0, 5.0, 5.0])
        assert len(out) == 4
        assert len(set(out)) == 1  # all the same block

    def test_monotonic_increasing(self) -> None:
        out = charts.render_sparkline([1.0, 2.0, 3.0, 4.0, 5.0])
        # heights should be non-decreasing
        heights = [charts._SPARK_BLOCKS.index(c) for c in out]
        assert heights == sorted(heights)

    def test_downsample(self) -> None:
        out = charts.render_sparkline([float(i) for i in range(100)], width=10)
        assert len(out) == 10


class TestComputeReturn:
    def test_flat(self) -> None:
        assert charts.compute_return([100.0, 100.0, 100.0]) == 0.0

    def test_up_50(self) -> None:
        assert charts.compute_return([100.0, 150.0]) == pytest.approx(50.0)

    def test_empty(self) -> None:
        assert charts.compute_return([]) is None

    def test_single(self) -> None:
        assert charts.compute_return([100.0]) is None

    def test_zero_start(self) -> None:
        assert charts.compute_return([0.0, 10.0]) is None


class TestRenderPriceChart:
    def test_no_data_message(self) -> None:
        out = charts.render_price_chart([], [], title="AAPL")
        assert "no price data" in out

    def test_returns_string(self) -> None:
        dates = [f"2026-04-{i:02d}" for i in range(1, 21)]
        closes = [100.0 + i * 2 for i in range(20)]
        out = charts.render_price_chart(dates, closes, title="TEST", width=60, height=12)
        assert isinstance(out, str)
        assert len(out) > 0
        # percent should appear somewhere in title (approx +38%)
        assert "%" in out


class TestMultiSeries:
    def test_empty(self) -> None:
        assert "no series" in charts.render_multi_series_chart([])

    def test_multiple(self) -> None:
        s1 = ("A", [f"2026-04-{i:02d}" for i in range(1, 11)], [100.0 + i for i in range(10)])
        s2 = ("B", [f"2026-04-{i:02d}" for i in range(1, 11)], [200.0 - i for i in range(10)])
        out = charts.render_multi_series_chart([s1, s2], width=60, height=12)
        assert "A" in out
        assert "B" in out


class TestFetch:
    def test_network_error_returns_empty(self) -> None:
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("network")
            dates, closes = charts.fetch_price_history("AAPL", period="1y")
        assert dates == []
        assert closes == []

    def test_unknown_period_falls_back_to_1y(self) -> None:
        # smoke test — just make sure invalid period doesn't crash
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = __import__(
                "types",
            ).SimpleNamespace(empty=True)
            dates, closes = charts.fetch_price_history("AAPL", period="not-a-period")
        assert dates == []
        assert closes == []
