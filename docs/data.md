# Data sourcing

How the data-layer modules cooperate: `storage`, `fetcher`, `news`,
`reports`, `ticker`, `models`.

## On-disk layout — `storage`

`storage` owns one decision: where on disk a cached blob lives. The
layout is two-tier:

```
<base_dir>/
├── data/                       (production mode)
│   └── <SAFE_TICKER>/
│       ├── analysis_latest.json
│       ├── analysis_<timestamp>.json
│       ├── financials/
│       ├── news/
│       └── reports/
└── data_test/                  (testing mode — never read cache)
    └── <SAFE_TICKER>/...
```

`<base_dir>` is set once per process by the consuming agent's
`__init__.py`:

```python
from pathlib import Path
import lynx_investor_core.storage as storage
storage.set_base_dir(Path(__file__).parent.parent)
```

`<SAFE_TICKER>` is the user-supplied ticker run through
`_sanitize_ticker()` — uppercased, non-alphanumeric replaced with
`_`, `..` neutralised. This is the only line that stands between a
hostile ticker string and a path-traversal write.

Mode (`production` / `testing`) flips the directory name (`data/`
vs `data_test/`) and also disables cache reads in testing mode so
the suite cannot accidentally serve stale fixtures in CI.

## yfinance wrapper — `fetcher`

Two entry points:

- `fetch_info(ticker)` — returns the raw `yf.Ticker(ticker).info`
  dict (or `{}` if the call fails). Pure read-through.
- `fetch_company_profile(ticker, profile_factory, *, info=None)` —
  builds the agent's own `CompanyProfile` dataclass. `profile_factory`
  is the agent's dataclass constructor; core never imports it.

This split is the layering rule for the whole project: core knows
shapes (dicts, dataclasses with a known field set) but not domain
enums. If you need a sector-specific field, add it to the agent's
factory call site, not to `fetcher`.

## News — `news`

Two sources merged:

1. `fetch_news_yfinance(ticker)` — Yahoo's own news list (via
   `yf.Ticker(ticker).news`). The Yahoo payload shape changes every
   few months; the module defends with `isinstance` checks at every
   level rather than `dict.get`-chained assumptions.
2. Google News RSS, parameterised by a `sector_keyword` the agent
   passes in (`"mining stock"` for basic materials, `"energy stock"`
   for energy, etc.). This is what makes the headline list relevant
   instead of generic ticker-quote spam.

Output is a list of `NewsArticle` dataclasses (`models.NewsArticle`)
saved as JSON under `storage.get_news_dir(ticker)`.

## Filings — `reports`

SEC EDGAR client with a SEDAR fallback for Canadian issuers. Two
HTTP headers are constructed per fetch — one for EDGAR's JSON
endpoint, one for the actual filing download. SEC's access policy
requires a unique product identifier, so each agent passes its own
`user_agent_product` (`"LynxMining"`, `"LynxEnergy"`, …); core
embeds it in the `User-Agent` strings.

`TARGET_FORMS` is the filing whitelist (`10-K`, `10-Q`, `20-F`,
`6-K`, `8-K`, plus the amended `/A` variants). Filings are downloaded
into `storage.get_reports_dir(ticker)` and the local path is stored
back into the filing record.

## Resolution — `ticker`

`ticker.resolve_ticker(user_input)` walks a fallback chain:

1. If the input already looks like a Yahoo symbol (`XOM`, `BHP.AX`),
   try it directly.
2. ISIN-shaped input (`US…`, `GB…`) gets the ISIN-to-Yahoo lookup.
3. Otherwise treat it as a company name and search yfinance.

Failure is non-fatal — the caller decides whether to fall back to
the user-typed string or surface an error.

## Cache freshness

`storage.get_cache_age_hours(ticker)` returns the age of the
`analysis_latest.json` file. None of the fetcher paths currently
consult it; the consuming agent decides whether to honour
`--refresh` or fall back to cache. Centralising this rule is on
`ROADMAP.md`.
