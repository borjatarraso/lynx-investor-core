"""ASCII / Unicode charting helpers for the Lince Investor Suite.

Every program in the Suite can render historical price or performance
charts directly in a terminal. The helpers here wrap `plotext` (a
cross-platform terminal-plotting library) behind a small stable surface
so individual packages never call plotext directly — keeping the
dependency swappable.

Typical usage — sparkline in the CLI or TUI::

    from lynx_investor_core.charts import render_price_chart, fetch_price_history
    dates, closes = fetch_price_history("AAPL", period="1y")
    render_price_chart(dates, closes, title="AAPL — 12m",
                       width=100, height=24, color="cyan")

:func:`render_price_chart` returns a string of pre-rendered ANSI-colored
text; callers can feed it straight into ``rich.console.Console.print``
or a Textual ``Static``.

Network calls go through yfinance (``period`` uses the same strings as
``yf.Ticker.history``: ``"1d"``, ``"5d"``, ``"1mo"``, ``"3mo"``,
``"6mo"``, ``"1y"``, ``"2y"``, ``"5y"``, ``"10y"``, ``"ytd"``,
``"max"``).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence, Tuple

__all__ = [
    "PERIOD_CHOICES",
    "fetch_price_history",
    "render_price_chart",
    "render_multi_series_chart",
    "render_sparkline",
    "compute_return",
]

PERIOD_CHOICES: Tuple[str, ...] = (
    "1d", "5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "5y", "10y", "max",
)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_price_history(
    ticker: str,
    *,
    period: str = "1y",
    interval: Optional[str] = None,
) -> Tuple[List[str], List[float]]:
    """Return `(dates, closes)` for *ticker* over *period*.

    *dates* are ``YYYY-MM-DD`` strings (terminal charts benefit from
    short labels); *closes* are adjusted close prices. On any fetch
    error an empty tuple ``([], [])`` is returned — callers should
    render a "no data" message rather than crashing.
    """
    try:
        import yfinance as yf  # lazy import: yfinance is heavy
    except ImportError:
        return [], []

    if period not in PERIOD_CHOICES:
        period = "1y"

    # Default interval tuned per period for a readable chart width.
    if interval is None:
        interval = _default_interval_for(period)

    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        return [], []

    if hist is None or hist.empty:
        return [], []

    dates: List[str] = []
    closes: List[float] = []
    for idx, row in hist.iterrows():
        close = row.get("Close")
        if close is None or close != close:  # skip NaN
            continue
        stamp = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        dates.append(stamp)
        closes.append(float(close))
    return dates, closes


def _default_interval_for(period: str) -> str:
    return {
        "1d": "5m",
        "5d": "30m",
        "1mo": "1h",
        "3mo": "1d",
        "6mo": "1d",
        "ytd": "1d",
        "1y": "1d",
        "2y": "1wk",
        "5y": "1wk",
        "10y": "1mo",
        "max": "1mo",
    }.get(period, "1d")


# ---------------------------------------------------------------------------
# Simple stats
# ---------------------------------------------------------------------------

def compute_return(closes: Sequence[float]) -> Optional[float]:
    """Total return % over the series (first → last close)."""
    if len(closes) < 2 or not closes[0]:
        return None
    return (closes[-1] / closes[0] - 1.0) * 100.0


# ---------------------------------------------------------------------------
# Render — single-series price chart
# ---------------------------------------------------------------------------

def render_price_chart(
    dates: Sequence[str],
    closes: Sequence[float],
    *,
    title: str = "",
    width: int = 100,
    height: int = 22,
    color: str = "cyan",
) -> str:
    """Render a terminal price line-chart and return it as text.

    Output is an ANSI-colored string — safe to `print()` or to feed
    into ``rich.console.Console``. Width/height are *character* cells.
    When there is no data, the returned string is a short placeholder.
    """
    if not closes:
        return f"(no price data for {title})" if title else "(no price data)"

    try:
        import plotext as plt
    except ImportError:
        return _fallback_sparkline(closes, title=title)

    plt.clear_figure()
    plt.theme("pro")
    plt.plot(list(range(len(closes))), list(closes), color=color, marker="braille")
    plt.plotsize(width, height)

    if title:
        pct = compute_return(closes)
        label = title if pct is None else f"{title}   {pct:+.2f}%"
        plt.title(label)

    # Show a handful of x-tick labels — matplotlib-style overcrowding
    # is ugly in a terminal.
    if len(dates) > 1:
        n_ticks = min(6, len(dates))
        step = max(1, (len(dates) - 1) // (n_ticks - 1))
        positions = list(range(0, len(dates), step))
        if positions[-1] != len(dates) - 1:
            positions.append(len(dates) - 1)
        labels = [dates[i] for i in positions]
        plt.xticks(positions, labels)

    plt.xlabel("date")
    plt.ylabel("close")
    plt.grid(horizontal=True, vertical=False)
    return plt.build()


def render_multi_series_chart(
    series: Sequence[Tuple[str, Sequence[str], Sequence[float]]],
    *,
    title: str = "",
    width: int = 100,
    height: int = 22,
    normalize: bool = True,
) -> str:
    """Render multiple symbols on one chart.

    ``series`` is a sequence of ``(label, dates, closes)`` tuples.
    When ``normalize=True``, each series is rebased to 100 at its
    starting point so shapes can be compared across price scales.
    """
    if not series:
        return "(no series to plot)"

    try:
        import plotext as plt
    except ImportError:
        return _fallback_sparkline(series[0][2], title=title)

    plt.clear_figure()
    plt.theme("pro")
    plt.plotsize(width, height)

    palette = ["cyan", "magenta", "yellow", "green", "red", "blue", "orange+", "white"]

    for idx, (label, dates, closes) in enumerate(series):
        if not closes:
            continue
        values: List[float]
        if normalize and closes[0]:
            values = [(c / closes[0]) * 100.0 for c in closes]
        else:
            values = list(closes)
        color = palette[idx % len(palette)]
        plt.plot(
            list(range(len(values))),
            values,
            color=color,
            marker="braille",
            label=label,
        )

    if title:
        plt.title(title)
    plt.xlabel("time")
    plt.ylabel("indexed to 100" if normalize else "price")
    plt.grid(horizontal=True, vertical=False)
    return plt.build()


# ---------------------------------------------------------------------------
# Sparkline — tiny fixed-width chart for tables / inline use
# ---------------------------------------------------------------------------

_SPARK_BLOCKS = " ▁▂▃▄▅▆▇█"


def render_sparkline(values: Sequence[float], *, width: Optional[int] = None) -> str:
    """One-line Unicode sparkline.

    Good for table cells and footer bars: ``▁▂▂▃▅▄▆▆▆▇█▇▆▅``.
    """
    if not values:
        return ""
    if width and len(values) > width:
        step = len(values) / width
        values = [values[int(i * step)] for i in range(width)]
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return _SPARK_BLOCKS[len(_SPARK_BLOCKS) // 2] * len(values)
    span = hi - lo
    out = []
    for v in values:
        idx = int((v - lo) / span * (len(_SPARK_BLOCKS) - 1))
        out.append(_SPARK_BLOCKS[idx])
    return "".join(out)


def _fallback_sparkline(closes: Sequence[float], *, title: str = "") -> str:
    spark = render_sparkline(list(closes), width=60)
    pct = compute_return(closes)
    pct_str = f"  {pct:+.2f}%" if pct is not None else ""
    return f"{title}\n{spark}{pct_str}" if title else f"{spark}{pct_str}"
