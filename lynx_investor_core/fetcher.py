"""Financial data fetching via yfinance.

Each agent keeps its own ``CompanyProfile`` / ``FinancialStatement`` dataclasses
because they embed domain-specific enum types (stage, commodity, tier). Core
operates on them via factory callables so nothing domain-specific leaks in.
"""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd
import yfinance as yf

from lynx_investor_core.storage import get_financials_dir, save_json


def fetch_info(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception:
        return {}


def fetch_company_profile(
    ticker: str,
    profile_factory: Callable[..., object],
    *,
    info: dict | None = None,
):
    """Build a CompanyProfile via *profile_factory* (agent-supplied).

    ``profile_factory`` is called with keyword arguments matching the agent's
    ``CompanyProfile`` dataclass so core never imports domain-specific enums.
    """
    if info is None:
        info = fetch_info(ticker)
    return profile_factory(
        ticker=ticker.upper(),
        name=info.get("longName") or info.get("shortName", ticker),
        sector=info.get("sector"),
        industry=info.get("industry"),
        country=info.get("country"),
        exchange=info.get("exchange"),
        currency=info.get("currency", "USD"),
        market_cap=info.get("marketCap"),
        description=info.get("longBusinessSummary"),
        website=info.get("website"),
        employees=info.get("fullTimeEmployees"),
    )


def fetch_financial_statements(
    ticker: str,
    statement_factory: Callable[..., object],
) -> list:
    """Fetch annual financial statements and build them via *statement_factory*."""
    try:
        t = yf.Ticker(ticker)
    except Exception:
        return []
    statements: list = []

    try:
        income = _safe_df(t.financials)
    except Exception:
        income = None
    try:
        balance = _safe_df(t.balance_sheet)
    except Exception:
        balance = None
    try:
        cashflow = _safe_df(t.cashflow)
    except Exception:
        cashflow = None

    fdir = get_financials_dir(ticker)
    for name, df in [("income_annual", income), ("balance_annual", balance), ("cashflow_annual", cashflow)]:
        if df is not None and not df.empty:
            save_json(fdir / f"{name}.json", _df_to_dict(df))

    if income is not None and not income.empty:
        for col in income.columns:
            period = col.strftime("%Y") if hasattr(col, "strftime") else str(col)
            stmt = statement_factory(period=period)
            stmt.revenue = _get(income, col, "Total Revenue")
            stmt.cost_of_revenue = _get(income, col, "Cost Of Revenue")
            stmt.gross_profit = _get(income, col, "Gross Profit")
            stmt.operating_income = _get(income, col, "Operating Income")
            stmt.net_income = _get(income, col, "Net Income")
            stmt.ebitda = _get(income, col, "EBITDA")
            stmt.interest_expense = _get(income, col, "Interest Expense", "Interest Expense Non Operating")
            stmt.eps = _get(income, col, "Basic EPS")

            if balance is not None and col in balance.columns:
                stmt.total_assets = _get(balance, col, "Total Assets")
                stmt.total_liabilities = _get(balance, col, "Total Liabilities Net Minority Interest")
                stmt.total_equity = _get(balance, col, "Stockholders Equity", "Total Equity Gross Minority Interest")
                stmt.total_debt = _get(balance, col, "Total Debt")
                stmt.total_cash = _get(balance, col, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
                stmt.current_assets = _get(balance, col, "Current Assets")
                stmt.current_liabilities = _get(balance, col, "Current Liabilities")
                stmt.shares_outstanding = _get(balance, col, "Ordinary Shares Number", "Share Issued")
                if stmt.total_equity is not None and stmt.shares_outstanding and stmt.shares_outstanding > 0:
                    stmt.book_value_per_share = stmt.total_equity / stmt.shares_outstanding

            if cashflow is not None and col in cashflow.columns:
                stmt.operating_cash_flow = _get(cashflow, col, "Operating Cash Flow")
                stmt.capital_expenditure = _get(cashflow, col, "Capital Expenditure")
                stmt.free_cash_flow = _get(cashflow, col, "Free Cash Flow")
                stmt.dividends_paid = _get(cashflow, col, "Common Stock Dividend Paid")
                if stmt.free_cash_flow is None and stmt.operating_cash_flow is not None:
                    capex = stmt.capital_expenditure or 0
                    stmt.free_cash_flow = stmt.operating_cash_flow + capex

            statements.append(stmt)

    return statements


def _safe_df(df) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return None


def _get(df: pd.DataFrame, col, *row_names) -> Optional[float]:
    for name in row_names:
        if name in df.index:
            val = df.loc[name, col]
            if pd.notna(val):
                return float(val)
    return None


def _df_to_dict(df: pd.DataFrame) -> dict:
    result = {}
    for col in df.columns:
        key = col.isoformat() if hasattr(col, "isoformat") else str(col)
        result[key] = {}
        for idx in df.index:
            val = df.loc[idx, col]
            result[key][str(idx)] = None if pd.isna(val) else float(val)
    return result
