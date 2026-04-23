# lynx-investor-core

Shared runtime for the **Lince Investor Suite** — the common scaffolding used by
every `lynx-investor-*` agent and by the three auxiliary apps
(`lynx-fundamental`, `lynx-compare`, `lynx-portfolio`).

This package is **not a standalone tool**. Install it alongside one of the
Suite packages below.

## The Lince Investor Suite

The Suite (current release: **v4.0**) bundles three families of programs:

### Specialized investor agents — one per GICS sector

Each agent analyzes a company against that sector's fundamentals; the
sector gate refuses to analyze companies outside its scope and suggests
which other Suite agent to use instead.

| Agent | Sector |
|---|---|
| [`lynx-investor-basic-materials`](https://github.com/borjatarraso/lynx-investor-basic-materials) | Junior mining, metals, uranium, basic materials |
| [`lynx-investor-energy`](https://github.com/borjatarraso/lynx-investor-energy) | Oil & gas, midstream, refining, energy equipment |
| [`lynx-investor-industrials`](https://github.com/borjatarraso/lynx-investor-industrials) | Aerospace, defense, transportation, machinery |
| [`lynx-investor-utilities`](https://github.com/borjatarraso/lynx-investor-utilities) | Regulated electric / gas / water utilities |
| [`lynx-investor-healthcare`](https://github.com/borjatarraso/lynx-investor-healthcare) | Pharma, biotech, medical devices, healthcare services |
| [`lynx-investor-financials`](https://github.com/borjatarraso/lynx-investor-financials) | Banks, insurers, asset managers, capital markets |
| [`lynx-investor-information-technology`](https://github.com/borjatarraso/lynx-investor-information-technology) | Software, semiconductors, hardware, IT services |
| [`lynx-investor-communication-services`](https://github.com/borjatarraso/lynx-investor-communication-services) | Telecom, media, entertainment, interactive platforms |
| [`lynx-investor-consumer-discretionary`](https://github.com/borjatarraso/lynx-investor-consumer-discretionary) | Autos, apparel, retail, restaurants, leisure |
| [`lynx-investor-consumer-staples`](https://github.com/borjatarraso/lynx-investor-consumer-staples) | Food, beverage, household products, staples retail |
| [`lynx-investor-real-estate`](https://github.com/borjatarraso/lynx-investor-real-estate) | REITs — residential, retail, office, industrial, specialty |

### Auxiliary apps

| App | Purpose |
|---|---|
| [`lynx-fundamental`](https://github.com/borjatarraso/lynx-fundamental) | Generic fundamental-analysis tool for companies that don't fit a specialized agent. |
| [`lynx-compare`](https://github.com/borjatarraso/lynx-compare) | Side-by-side comparison of two tickers across every metric; text / HTML / PDF export; Flask server. |
| [`lynx-portfolio`](https://github.com/borjatarraso/lynx-portfolio) | Portfolio tracker with an encrypted vault, live Yahoo Finance data, **dashboard analytics**, and a secured REST API. See the dashboard feature below. |

### Suite-wide Portfolio Dashboard (v4.0)

`lynx-portfolio` ships a dashboard that turns the raw portfolio into
six at-a-glance views, all built on a single `dashboard.py` module so
the same numbers flow to every UI (CLI, REPL, TUI, GUI, REST API):

| View | Interactive command | REST endpoint | What you see |
|---|---|---|---|
| Summary card | `stats` | `GET /api/dashboard/stats` | positions, market value (EUR), invested, total PnL %, day change |
| Sector allocation | `sectors` | `GET /api/dashboard/sectors` | per-sector value (EUR) with % bar |
| Top movers | `movers` | `GET /api/dashboard/movers?limit=N` | gainers & losers of the day |
| Dividend income | `income` | `GET /api/dashboard/income` | annual + monthly projection, yield on cost, per-position breakdown |
| Alerts | `alerts` | `GET /api/dashboard/alerts?drawdown_pct=…&concentration_pct=…` | drawdown, concentration, stale-data, missing-cost-basis |
| Benchmark | `benchmark [ticker]` | `GET /api/dashboard/benchmark?ticker=^GSPC` | portfolio vs index return (alpha) |
| Full snapshot | `dashboard` | `GET /api/dashboard` | all of the above in one response |

The REST API is **authenticated with a bearer token** that the server
generates on first start (stored at `data/api_token`, mode `0600`).
The server binds to `127.0.0.1` by default — `--unsafe-bind-all` is
required to bind `0.0.0.0`. See
[`lynx-portfolio/docs/REST_API.md`](https://github.com/borjatarraso/lynx-portfolio/blob/main/docs/REST_API.md)
for the full endpoint reference.

## What lives here

| Module | Purpose |
|---|---|
| `lynx_investor_core` (top level) | Suite metadata: `SUITE_NAME`, `SUITE_VERSION`, `SUITE_LABEL`, license text, author info |
| `storage` | Data-directory management for production/testing modes, JSON/text/binary helpers, cache lookup |
| `fetcher` | yfinance-backed company profile & financial-statement fetcher |
| `news` | Yahoo + Google-News-RSS news aggregation with per-agent sector keyword |
| `reports` | SEC EDGAR filing discovery + download helpers with per-agent User-Agent |
| `ticker` | Ticker / ISIN / name resolution with ambiguity fallbacks |
| `sector_gate` | `SectorValidator` base class + `SectorMismatchError` — each agent declares its allowed sectors, industries, and description patterns; auto-suggests which other agent to use when a company is out of scope |
| `sector_registry` | Single source of truth for every specialized investor in the Suite — powers the "use `lynx-investor-<other>` instead" suggestion |
| `pager` | Suite-wide PageUp / PageDown helpers: `PagingAppMixin` + `tui_paging_bindings()` for Textual, `console_pager()` / `paged_print()` for interactive + console, `bind_tk_paging()` for Tkinter |
| `about` | `build_about()` plus rendering helpers for CLI / interactive / TUI / GUI About dialogs |
| `cli` | `add_standard_args()` — argparse boilerplate shared across every agent |
| `logo` | ASCII logo loader |
| `easter` | Shared easter-egg visuals (rocket / matrix / fortune cookie) parameterized per agent |
| `export.pdf` | PDF export via weasyprint |
| `export.ExportFormat` | Enum for export dispatch |

## PageUp / PageDown contract

Every program in the Suite — GUI, TUI, interactive REPL, and plain console
commands — honors the same keys:

| Mode | PageUp / PageDown | Notes |
|---|---|---|
| **Graphical** (Tk) | Scroll the main canvas by one page | `bind_tk_paging(root, canvas)` |
| **TUI** (Textual) | Page the focused scrollable widget or the main report view | Mix `PagingAppMixin` into the `App`, add `tui_paging_bindings()` to `BINDINGS` |
| **Interactive & console** | Page the current output through the system pager; never scrolls *above* the current output | `with console_pager(console): ...` or `paged_print(console, renderable)` |

`Shift+PageUp` / `Shift+PageDown` remain reserved for the terminal emulator's
own scrollback — the Suite never intercepts them.

## Sector registry

`sector_registry.AGENT_REGISTRY` lists every specialized investor and the
Yahoo sector / industry / description fingerprints they own. When a sector
gate refuses a profile, `format_agent_suggestion(profile, current_agent=...)`
returns a ready-to-append line like:

```
Suggestion: use 'lynx-investor-energy' from the Lince Investor Suite instead.
```

`SectorValidator.build(..., agent_name="lynx-investor-basic-materials")`
enables this automatically in every `SectorMismatchError` raised by that
agent — the original scope-specific warning text is preserved exactly.

## Installation (for agents)

From a fresh clone of an agent repository:

```bash
# sibling checkout so agents can reference it with an editable install
git clone https://github.com/borjatarraso/lynx-investor-core.git
cd lynx-investor-core
pip install -e .
```

Then install the agent as usual (`pip install -e .` inside the agent repo).

## License

BSD 3-Clause © 2026 Borja Tarraso
