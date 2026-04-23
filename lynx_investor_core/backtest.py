"""Portfolio backtesting + historical benchmark comparison (v5.1).

All computations are pure functions operating on close-price series
fetched via :mod:`lynx_investor_core.charts`. Nothing here writes to
disk; callers are free to feed the results into a Rich table, a JSON
response, or a chart renderer.

Key entry points:

* :func:`run_backtest` — equal-weight or custom-weight buy-and-hold
  portfolio over a date range, with optional rebalancing.
* :func:`compare_to_benchmark` — total-return, CAGR, volatility, max
  drawdown, Sharpe ratio, alpha, beta, and correlation vs a benchmark
  index.
* :func:`historical_benchmark` — high-quality replacement for the
  52-week-range heuristic in the v4.0 dashboard — portfolio return vs
  benchmark return over the last *N* years using real daily closes.

All percent values are returned in *percent* (e.g. 12.5 = 12.5%), not
fractions. Risk-free rate defaults to 0; pass a yearly rate as a
fraction to refine the Sharpe ratio.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Tuple

from . import charts


__all__ = [
    "BacktestResult",
    "BenchmarkComparison",
    "run_backtest",
    "compare_to_benchmark",
    "historical_benchmark",
    "max_drawdown_pct",
    "volatility_pct",
    "sharpe_ratio",
    "beta",
    "alpha_pct",
    "correlation",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """Result of running a buy-and-hold / rebalanced portfolio sim.

    Attributes
    ----------
    tickers : the input universe (cleaned / upper-cased)
    weights : final weights used (possibly normalized from inputs)
    initial_capital : starting cash in base units
    final_value : ending portfolio value
    total_return_pct : total return over the whole period (percent)
    cagr_pct : compound annual growth rate (percent)
    volatility_pct : annualized volatility of daily returns (percent)
    max_drawdown_pct : worst peak-to-trough drawdown (percent, negative)
    sharpe_ratio : annualized; risk_free_rate deducted if provided
    dates : series of date strings (``YYYY-MM-DD``)
    value_history : portfolio value on each date
    skipped_tickers : symbols with no data on the chosen window
    """

    tickers: List[str]
    weights: List[float]
    initial_capital: float
    final_value: float
    total_return_pct: float
    cagr_pct: float
    volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    dates: List[str] = field(default_factory=list)
    value_history: List[float] = field(default_factory=list)
    skipped_tickers: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return {
            "tickers": self.tickers,
            "weights": self.weights,
            "initial_capital": round(self.initial_capital, 2),
            "final_value": round(self.final_value, 2),
            "total_return_pct": round(self.total_return_pct, 2),
            "cagr_pct": round(self.cagr_pct, 2),
            "volatility_pct": round(self.volatility_pct, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "dates": self.dates,
            "value_history": [round(v, 2) for v in self.value_history],
            "skipped_tickers": self.skipped_tickers,
        }


@dataclass
class BenchmarkComparison:
    """Portfolio vs benchmark with modern-portfolio-theory stats.

    Attributes
    ----------
    portfolio_return_pct / benchmark_return_pct : total return over period
    portfolio_cagr_pct / benchmark_cagr_pct : annualized
    alpha_pct : portfolio return minus benchmark (percent)
    beta : sensitivity to benchmark returns (linear regression slope)
    correlation : Pearson correlation of daily returns
    max_drawdown_pct : portfolio's worst drawdown
    period : the ``period`` string passed in (e.g. ``"5y"``)
    """

    benchmark_ticker: str
    period: str
    portfolio_return_pct: float
    benchmark_return_pct: float
    portfolio_cagr_pct: float
    benchmark_cagr_pct: float
    alpha_pct: float
    beta: Optional[float]
    correlation: Optional[float]
    max_drawdown_pct: float

    def as_dict(self) -> Dict:
        return {
            "benchmark_ticker": self.benchmark_ticker,
            "period": self.period,
            "portfolio_return_pct": round(self.portfolio_return_pct, 2),
            "benchmark_return_pct": round(self.benchmark_return_pct, 2),
            "portfolio_cagr_pct": round(self.portfolio_cagr_pct, 2),
            "benchmark_cagr_pct": round(self.benchmark_cagr_pct, 2),
            "alpha_pct": round(self.alpha_pct, 2),
            "beta": round(self.beta, 3) if self.beta is not None else None,
            "correlation": round(self.correlation, 3) if self.correlation is not None else None,
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
        }


# ---------------------------------------------------------------------------
# Stats helpers — all percent values
# ---------------------------------------------------------------------------

TRADING_DAYS_PER_YEAR = 252


def _daily_returns(closes: Sequence[float]) -> List[float]:
    returns = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        curr = closes[i]
        if prev and prev > 0:
            returns.append((curr / prev) - 1.0)
    return returns


def _cagr(start_value: float, end_value: float, years: float) -> float:
    if start_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1.0 / years) - 1.0) * 100.0


def _years_between(start: str, end: str) -> float:
    try:
        a = datetime.fromisoformat(start[:10]).date()
        b = datetime.fromisoformat(end[:10]).date()
        return max((b - a).days / 365.25, 0.001)
    except (ValueError, TypeError):
        return 1.0


def max_drawdown_pct(value_history: Sequence[float]) -> float:
    """Peak-to-trough maximum drawdown (percent, negative number)."""
    if not value_history:
        return 0.0
    peak = value_history[0]
    worst = 0.0
    for v in value_history:
        if v > peak:
            peak = v
        if peak > 0:
            drawdown = (v / peak - 1.0) * 100.0
            if drawdown < worst:
                worst = drawdown
    return worst


def volatility_pct(daily_returns: Sequence[float]) -> float:
    """Annualized volatility (percent) from daily returns."""
    n = len(daily_returns)
    if n < 2:
        return 0.0
    mean = sum(daily_returns) / n
    var = sum((r - mean) ** 2 for r in daily_returns) / (n - 1)
    std = math.sqrt(var)
    return std * math.sqrt(TRADING_DAYS_PER_YEAR) * 100.0


def sharpe_ratio(
    daily_returns: Sequence[float],
    *,
    risk_free_rate: float = 0.0,
) -> float:
    """Annualized Sharpe ratio.

    *risk_free_rate* is a yearly rate as a fraction (e.g. 0.04 for 4%).
    """
    if not daily_returns:
        return 0.0
    rf_daily = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess = [r - rf_daily for r in daily_returns]
    n = len(excess)
    if n < 2:
        return 0.0
    mean = sum(excess) / n
    var = sum((r - mean) ** 2 for r in excess) / (n - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(TRADING_DAYS_PER_YEAR)


def beta(
    asset_returns: Sequence[float],
    benchmark_returns: Sequence[float],
) -> Optional[float]:
    """Linear-regression slope of *asset_returns* vs *benchmark_returns*."""
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 2:
        return None
    a = asset_returns[-n:]
    b = benchmark_returns[-n:]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    var = sum((b[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var == 0:
        return None
    return cov / var


def alpha_pct(
    portfolio_return: float,
    benchmark_return: float,
) -> float:
    """Simple alpha: portfolio minus benchmark return (percent)."""
    return portfolio_return - benchmark_return


def correlation(
    asset_returns: Sequence[float],
    benchmark_returns: Sequence[float],
) -> Optional[float]:
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 2:
        return None
    a = asset_returns[-n:]
    b = benchmark_returns[-n:]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    var_a = sum((x - mean_a) ** 2 for x in a) / (n - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (n - 1)
    if var_a == 0 or var_b == 0:
        return None
    return cov / math.sqrt(var_a * var_b)


# ---------------------------------------------------------------------------
# Main API — run_backtest
# ---------------------------------------------------------------------------

def _align_series(
    series_by_ticker: Dict[str, Tuple[List[str], List[float]]],
) -> Tuple[List[str], Dict[str, List[float]]]:
    """Return the common date axis and each ticker's closes aligned to it."""
    if not series_by_ticker:
        return [], {}
    common: Optional[set] = None
    for dates, _ in series_by_ticker.values():
        common = set(dates) if common is None else common.intersection(dates)
    if not common:
        return [], {}
    aligned_dates = sorted(common)
    out: Dict[str, List[float]] = {}
    for ticker, (dates, closes) in series_by_ticker.items():
        lookup = dict(zip(dates, closes))
        out[ticker] = [lookup[d] for d in aligned_dates]
    return aligned_dates, out


def run_backtest(
    tickers: Sequence[str],
    *,
    weights: Optional[Sequence[float]] = None,
    period: str = "5y",
    initial_capital: float = 10000.0,
    rebalance: str = "none",  # "none", "monthly", "quarterly", "annual"
    risk_free_rate: float = 0.0,
) -> BacktestResult:
    """Run a buy-and-hold / rebalanced backtest.

    * ``weights`` — same length as *tickers*; if omitted, equal-weight.
      Negative values are clamped to 0; weights are normalized to sum
      to 1.0.
    * ``period`` — passed to :func:`lynx_investor_core.charts.fetch_price_history`.
    * ``rebalance`` — ``"none"`` buys once at t=0 and holds; the others
      reset to target weights on the first trading day of each month
      / quarter / year.

    Empty returns ``BacktestResult`` — callers can inspect
    ``skipped_tickers`` to detect data-fetch problems.
    """
    tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    if not tickers:
        return BacktestResult(
            tickers=[], weights=[], initial_capital=initial_capital,
            final_value=initial_capital, total_return_pct=0.0,
            cagr_pct=0.0, volatility_pct=0.0, max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
        )

    # Normalize weights
    if weights is None:
        weights = [1.0 / len(tickers)] * len(tickers)
    weights = [max(0.0, float(w)) for w in weights]
    if len(weights) != len(tickers):
        # Pad or truncate to match
        weights = (list(weights) + [0.0] * len(tickers))[: len(tickers)]
    total_w = sum(weights)
    if total_w == 0:
        weights = [1.0 / len(tickers)] * len(tickers)
    else:
        weights = [w / total_w for w in weights]

    # Fetch data
    series: Dict[str, Tuple[List[str], List[float]]] = {}
    skipped: List[str] = []
    for t in tickers:
        dates, closes = charts.fetch_price_history(t, period=period)
        if len(closes) < 2:
            skipped.append(t)
        else:
            series[t] = (dates, closes)

    if not series:
        return BacktestResult(
            tickers=tickers, weights=weights,
            initial_capital=initial_capital, final_value=initial_capital,
            total_return_pct=0.0, cagr_pct=0.0, volatility_pct=0.0,
            max_drawdown_pct=0.0, sharpe_ratio=0.0,
            skipped_tickers=skipped,
        )

    aligned_dates, aligned_closes = _align_series(series)
    if not aligned_dates:
        return BacktestResult(
            tickers=tickers, weights=weights,
            initial_capital=initial_capital, final_value=initial_capital,
            total_return_pct=0.0, cagr_pct=0.0, volatility_pct=0.0,
            max_drawdown_pct=0.0, sharpe_ratio=0.0,
            skipped_tickers=skipped,
        )

    # Filter weights to kept tickers only and renormalize
    kept = [t for t in tickers if t in aligned_closes]
    kept_weights = {
        t: weights[tickers.index(t)] for t in kept
    }
    wsum = sum(kept_weights.values())
    if wsum == 0:
        kept_weights = {t: 1.0 / len(kept) for t in kept}
    else:
        kept_weights = {t: w / wsum for t, w in kept_weights.items()}

    # Initial allocation on day 0
    shares = {t: (initial_capital * kept_weights[t]) / aligned_closes[t][0]
              for t in kept}

    rebalance = rebalance.lower()
    value_history: List[float] = []
    last_period_key: Optional[str] = None

    for i, d in enumerate(aligned_dates):
        value = sum(shares[t] * aligned_closes[t][i] for t in kept)
        value_history.append(value)

        # Rebalance at the start of each chosen period — skip the first
        # bar so the initial allocation already reflects the target.
        if i == 0 or rebalance == "none":
            continue

        if rebalance == "monthly":
            key = d[:7]  # "YYYY-MM"
        elif rebalance == "quarterly":
            key = f"{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}"
        elif rebalance == "annual":
            key = d[:4]
        else:
            key = None

        if key is not None and key != last_period_key and last_period_key is not None:
            # Hit a new period — rebalance to target weights.
            shares = {
                t: (value * kept_weights[t]) / aligned_closes[t][i]
                for t in kept
            }
        last_period_key = key

    final_value = value_history[-1]
    total_return = (final_value / initial_capital - 1.0) * 100.0
    years = _years_between(aligned_dates[0], aligned_dates[-1])
    cagr = _cagr(initial_capital, final_value, years)
    returns = _daily_returns(value_history)
    vol = volatility_pct(returns)
    mdd = max_drawdown_pct(value_history)
    sharpe = sharpe_ratio(returns, risk_free_rate=risk_free_rate)

    return BacktestResult(
        tickers=kept,
        weights=[kept_weights[t] for t in kept],
        initial_capital=initial_capital,
        final_value=final_value,
        total_return_pct=total_return,
        cagr_pct=cagr,
        volatility_pct=vol,
        max_drawdown_pct=mdd,
        sharpe_ratio=sharpe,
        dates=aligned_dates,
        value_history=value_history,
        skipped_tickers=skipped,
    )


# ---------------------------------------------------------------------------
# Benchmark comparison
# ---------------------------------------------------------------------------

def compare_to_benchmark(
    portfolio_dates: Sequence[str],
    portfolio_values: Sequence[float],
    benchmark_ticker: str,
    *,
    period: str = "5y",
) -> BenchmarkComparison:
    """Compare a precomputed portfolio value series to a benchmark index."""
    b_dates, b_closes = charts.fetch_price_history(benchmark_ticker, period=period)

    # Align on common dates (the index may have fewer bars than the
    # portfolio if the portfolio series was daily-rebalanced).
    port_map = dict(zip(portfolio_dates, portfolio_values))
    bench_map = dict(zip(b_dates, b_closes))
    common = sorted(set(port_map).intersection(bench_map))
    if len(common) < 2:
        # Not enough overlap — return an empty-ish comparison
        return BenchmarkComparison(
            benchmark_ticker=benchmark_ticker, period=period,
            portfolio_return_pct=0.0, benchmark_return_pct=0.0,
            portfolio_cagr_pct=0.0, benchmark_cagr_pct=0.0,
            alpha_pct=0.0, beta=None, correlation=None,
            max_drawdown_pct=0.0,
        )

    port_series = [port_map[d] for d in common]
    bench_series = [bench_map[d] for d in common]
    port_ret = charts.compute_return(port_series) or 0.0
    bench_ret = charts.compute_return(bench_series) or 0.0

    years = _years_between(common[0], common[-1])
    port_cagr = _cagr(port_series[0], port_series[-1], years)
    bench_cagr = _cagr(bench_series[0], bench_series[-1], years)

    port_returns = _daily_returns(port_series)
    bench_returns = _daily_returns(bench_series)

    return BenchmarkComparison(
        benchmark_ticker=benchmark_ticker,
        period=period,
        portfolio_return_pct=port_ret,
        benchmark_return_pct=bench_ret,
        portfolio_cagr_pct=port_cagr,
        benchmark_cagr_pct=bench_cagr,
        alpha_pct=alpha_pct(port_ret, bench_ret),
        beta=beta(port_returns, bench_returns),
        correlation=correlation(port_returns, bench_returns),
        max_drawdown_pct=max_drawdown_pct(port_series),
    )


def historical_benchmark(
    positions: Sequence[Tuple[str, float]],  # (ticker, current_market_value)
    benchmark_ticker: str = "^GSPC",
    *,
    period: str = "5y",
) -> BenchmarkComparison:
    """Replacement for the v4.0 52-week-range heuristic.

    Builds a value-weighted daily portfolio series from current
    market-cap weights (approximate since past weights are unknown),
    then runs :func:`compare_to_benchmark`. Good for "what does my
    portfolio look like against SPY over the last 5 years at current
    allocations?"
    """
    total_value = sum(v for _, v in positions if v > 0)
    if total_value <= 0 or not positions:
        return BenchmarkComparison(
            benchmark_ticker=benchmark_ticker, period=period,
            portfolio_return_pct=0.0, benchmark_return_pct=0.0,
            portfolio_cagr_pct=0.0, benchmark_cagr_pct=0.0,
            alpha_pct=0.0, beta=None, correlation=None,
            max_drawdown_pct=0.0,
        )
    weights = [v / total_value for _, v in positions if v > 0]
    tickers = [t for t, v in positions if v > 0]
    result = run_backtest(
        tickers, weights=weights,
        period=period, initial_capital=1.0, rebalance="none",
    )
    if not result.value_history:
        return BenchmarkComparison(
            benchmark_ticker=benchmark_ticker, period=period,
            portfolio_return_pct=0.0, benchmark_return_pct=0.0,
            portfolio_cagr_pct=0.0, benchmark_cagr_pct=0.0,
            alpha_pct=0.0, beta=None, correlation=None,
            max_drawdown_pct=0.0,
        )
    return compare_to_benchmark(
        result.dates, result.value_history,
        benchmark_ticker, period=period,
    )
