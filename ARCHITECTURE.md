# Architecture

A module-by-module tour of `lynx-investor-core` — how the pieces fit
together, where data flows, and which third parties they touch.

## One-line summary

A pip-installable Python library that supplies a shared runtime — data
fetching, sector validation, UI vocabulary, i18n, on-disk storage — to
every member of the Lince Investor Suite (eleven sector-specialized
`lynx-investor-*` agents and four auxiliary apps).

## Top-down view

```
                            ┌──────────────────────────────┐
                            │  Suite agents and apps       │
                            │  lynx-investor-*             │
                            │  lynx-fundamental            │
                            │  lynx-compare / -fund        │
                            │  lynx-portfolio              │
                            └──────────────┬───────────────┘
                                           │ from lynx_investor_core
                                           ▼
   ┌────────────────────────────────────────────────────────────────┐
   │                       lynx_investor_core                       │
   │                                                                │
   │  Data           Sector            UI vocabulary    i18n        │
   │  ────           ──────            ─────────────    ────        │
   │  fetcher        sector_gate       about            i18n        │
   │  news           sector_registry   author_footer    translations│
   │  reports        screener          easter           debounce    │
   │  ticker         backtest          logo             locales/    │
   │  storage        charts            pager                        │
   │  models                           themes                       │
   │                                   gui_themes                   │
   │                                   lang_widget                  │
   │                                                                │
   │  Runtime utilities                                             │
   │  ─────────────────                                             │
   │  cli   logging   plugins   openapi   urlsafe                   │
   └─────────────┬──────────────────────────────────────────────────┘
                 │
   ┌─────────────▼──────────┐   ┌──────────────────┐   ┌────────────┐
   │ yfinance / Yahoo       │   │ SEC EDGAR        │   │ Google News│
   │ Google News RSS        │   │ SEDAR            │   │ RSS feed   │
   └────────────────────────┘   └──────────────────┘   └────────────┘
```

There is no daemon or background thread; everything is request-driven.
A consuming agent calls into core, core calls out to one of the three
external services (yfinance, EDGAR, news RSS), the result is cached on
disk under `data/<TICKER>/` and returned.

## Logical module groups

The package is a flat directory of single-file modules. The groups
below are *logical*, not physical — they describe how the code is
intended to be reasoned about. The repo-level `AGENTS.md` lists every
public name.

### 1. Data sourcing — `fetcher`, `news`, `reports`, `ticker`, `storage`, `models`

`storage` owns the on-disk layout. Every other data module writes
JSON / text / binary blobs into `<base>/data/<TICKER>/{financials,
news,reports}/`. `set_base_dir()` is called by each consuming agent
at import time, pointing at the agent's own project root.

`fetcher` is yfinance-only. It is deliberately agnostic about the
agent's `CompanyProfile` dataclass: callers pass a `profile_factory`
callable, fetcher hands it raw fields. That keeps domain enums
(`stage`, `tier`, `commodity`) out of core.

`news` merges Yahoo Finance's own news list with a sector-scoped
Google News RSS query. `reports` discovers SEC EDGAR filings (and the
SEDAR fallback for Canadian issuers) and downloads them with a
per-agent User-Agent. `ticker` resolves the user's free-text input
(ticker / ISIN / company name) into a Yahoo symbol.

### 2. Sector logic — `sector_gate`, `sector_registry`, `screener`, `backtest`, `charts`

`sector_registry` is a frozen table of which Yahoo sector / industry
strings belong to which specialized agent. `sector_gate` is the
runtime check: each agent constructs a `SectorValidator` from its
own allow-lists; when a company is out of scope, the validator raises
`SectorMismatchError` *and* — because it knows its `agent_name` —
appends a `Suggestion: use 'lynx-investor-energy' instead.` line drawn
from the registry.

`screener`, `backtest`, and `charts` are analytical utilities that
operate on the same shared schema and are commonly composed in the
same workflow as the gate, hence the grouping.

### 3. UI vocabulary — `about`, `author_footer`, `easter`, `logo`, `pager`, `themes`, `gui_themes`, `lang_widget`

Every agent shows the same About dialog, the same logo, and the same
PageUp / PageDown contract across all four surfaces (CLI, REPL, TUI,
GUI). The relevant modules:

- `pager` — `PagingAppMixin` for Textual apps, `tui_paging_bindings()`,
  `console_pager()` / `paged_print()` for the REPL, `bind_tk_paging()`
  for Tk.
- `themes` — Textual / Rich palettes (Lynx house themes plus
  Catppuccin, Dracula, Gruvbox, Solarized, Tokyo Night, etc.).
- `gui_themes` — the same palettes adapted for Tk's ttk styles.
- `lang_widget` — Suite-wide language picker (Tk widget + Textual
  variant) that calls into `translations.set_language()`.
- `easter` — shared rocket / matrix / fortune visuals parameterised
  per agent.

UI framework imports (`textual`, `tkinter`, `rich`) are kept lazy
inside the functions that use them.

### 4. Internationalisation — `i18n`, `translations`, `debounce`, `locales/`

Two parallel translation stacks coexist on purpose:

- `i18n` — a thin wrapper over the stdlib `gettext`. Used by `cli` for
  parser strings and by the older parts of the consuming agents.
  Catalogues live at `locales/<lang>/LC_MESSAGES/lynx.{po,mo}`.
- `translations` — a small JSON-pool translator used by the GUI / TUI
  label paths. Two pools: `locales/core/<lang>.json` (UI labels) and
  `locales/extensive/<lang>.json` (long-form copy). The chosen
  language persists under `$XDG_CONFIG_HOME/lynx/language.json` and
  is overridable via `LYNX_LANG=…`.

`debounce` lives in this group because its main user is the language-
toggle widget — rapid double-clicks on the cycle button used to
launch two language-change side effects. It's a generic click gate
(`ClickDebouncer`) usable wherever Tk / Textual events arrive faster
than the handler can respond.

### 5. Runtime utilities — `cli`, `logging`, `plugins`, `openapi`, `urlsafe`

- `cli.add_standard_args()` adds the argparse boilerplate shared by
  every Suite entry point (`-p` / `-t`, ticker positional, UI mode
  group, `--refresh`, `--export`, `--locale`, `--explain`, etc.).
- `logging.get_logger()` is the package-wide accessor for the shared
  logger configuration.
- `plugins` discovers per-sector plugin modules — currently used by
  the screener and backtest paths.
- `openapi.mount_openapi()` exposes a small OpenAPI surface for the
  REST endpoint shipped by `lynx-portfolio`.
- `urlsafe` is a tiny encoder used by `storage` and a few CLI helpers
  to turn arbitrary tickers into filesystem-safe names.

## Dataflow — a typical agent call

```
   user types:   lynx-investor-energy -p XOM
                          │
                          ▼
   agent entry point parses argv (cli.add_standard_args)
                          │
                          ▼
   ticker.resolve_ticker("XOM")              ──► yfinance
                          │
                          ▼
   fetcher.fetch_company_profile(...)        ──► yfinance
                          │  + agent profile_factory
                          ▼
   sector_gate.SectorValidator.validate(profile)
       │   pass: continue
       │   fail: SectorMismatchError (+ registry-driven suggestion)
                          │
                          ▼
   reports.fetch_filings(...)                ──► SEC EDGAR
   news.fetch_news(...)                      ──► Yahoo + Google News
                          │
                          ▼
   storage.save_analysis_report(ticker, ...)
                          │
                          ▼
   UI render (about, themes, pager, charts)
```

## External dependencies

Declared in `pyproject.toml`:

- `yfinance>=0.2` — Yahoo Finance data.
- `pandas>=2.0` — used by `fetcher`, `screener`, `backtest` and the
  consuming agents' analysis code.
- `requests>=2.31` — direct HTTP for `reports` (EDGAR) and `news`.
- `feedparser>=6.0` — Google News RSS parsing in `news`.
- `beautifulsoup4>=4.12` — HTML scraping in `reports`.
- `rich>=13.7` — console rendering used by `about`, `pager`,
  `charts`, `themes`.
- `textual>=0.60` — TUI framework used by `themes`, `pager`,
  `lang_widget`.
- `plotext>=5.2` — ASCII charts in `charts`.

Optional (only loaded when used): `tkinter` (stdlib) for the GUI
surfaces, `weasyprint` for PDF export from consuming agents.

## What is *not* here

- No HTTP server or REST API. `openapi.mount_openapi()` is a helper
  for the server that `lynx-portfolio` ships; the server itself is
  not in core.
- No CLI entry point. The package has no `[project.scripts]` block.
- No domain-specific scoring. Each agent computes its own scores
  using its own dataclasses; core only provides the plumbing.
- No persistent state at module import time. Everything starts from
  the consuming agent's `set_base_dir()`.

## Where to look next

- `docs/data.md` — fetcher / storage / cache layout.
- `docs/sector.md` — gate + registry interaction in detail.
- `docs/ui.md` — themes, pager contract, easter visuals.
- `docs/i18n.md` — the two-stack i18n design.
- `docs/runtime.md` — cli / logging / plugins / openapi / urlsafe.
- `ROADMAP.md` — what is intentionally not yet built.
