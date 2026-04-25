# Changelog

## 6.0.0 — 2026-04-26

**Major release synchronising the entire Lince Investor Suite.**

### What's new across the Suite

- **lynx-fund** — brand-new mutual / index fund analysis tool, rejecting
  ETFs and stocks at the resolver level. Surfaces share classes, loads,
  12b-1 fees, manager tenure, persistence, capital-gains tax drag, and
  20-rule passive-investor checklist with tailored tips.
- **lynx-compare-fund** — head-to-head comparison for two mutual / index
  funds. Adds a Boglehead-style Passive-Investor Verdict, plus warnings
  for active-vs-passive, UCITS, soft- / hard-close, and distribution-
  policy mismatches.
- **lynx-theme** — visual theme editor for the entire Suite (GUI + TUI
  only). Edit colours, fonts, alignment, bold / italic / underline /
  blink / marquee for 15 styled areas with live preview. Three built-in
  read-only reference themes (`lynx-mocha`, `lynx-latte`,
  `lynx-high-contrast`). Sets the default theme persisted to
  `$XDG_CONFIG_HOME/lynx-theme/default.json`.
- **i18n** — every Suite CLI now accepts `--language=us|es|it|de|fr|fa`
  and persists the user's choice to `$XDG_CONFIG_HOME/lynx/language.json`.
  GUI apps mount a small bottom-right language toggle (left-click
  cycles, right-click opens a chooser); TUI apps bind `g` to cycle.
  Honours `LYNX_LANG` for ad-hoc shells.
- **Author signature footer** — every txt / html / pdf export now ends
  with the Suite-wide author block: *Borja Tarraso
  &lt;borja.tarraso@member.fsf.org&gt;*. Provided by the new
  `lynx_investor_core.author_footer` module.

### Dashboard

- Two new APP launchables (Lynx Fund, Lynx Compare Fund, Lynx Theme),
  raising the catalogue to **8 apps + 11 sector agents = 19
  launchables**.
- Per-app launch dialect (`run_mode_dialect`, `ui_mode_flags`,
  `accepts_identifier`) so the launcher emits argv each app
  understands; lynx-theme + lynx-portfolio launch correctly from every
  mode.
- `--recommend` now rejects empty queries instead of silently passing.

### Bug fixes

- `__main__.py` of every fund / compare-fund / etf / compare-etf entry
  point now propagates `run_cli`'s return code so non-zero exits are
  visible to shell scripts and CI pipelines.
- Stale-install hygiene: pyproject editable installs now overwrite
  cached site-packages copies cleanly.
- Cosmetic clean-up: remaining "ETF" labels in fund / compare-fund
  GUI / TUI / interactive prompts → "Fund".
- Validation: empty positional ticker, missing second comparison
  ticker, and `--recommend ""` now exit non-zero with a clear message.


All notable changes to **lynx-investor-core** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v4.0] — 2026-04-23

Part of **Lince Investor Suite v4.0**.

### Added
- `urlsafe` module with `is_safe_url`, `validate_safe_url`, and
  `safe_webbrowser_open` helpers that block SSRF and URL-scheme abuse
  (`file://`, `javascript:`, private / loopback hosts, DNS-rebind).
- `news.download_article` now routes every RSS-sourced URL through
  `urlsafe` and sets `allow_redirects=False`.
- `rich_lynx()` takes an optional `secondary_art` parameter so each
  specialized investor renders its own ASCII glyph instead of the shared
  pickaxe motif.

### Changed
- Bumped to v4.0 alongside the Suite-wide coordinated release.
- `SUITE_VERSION = "4.0"`.
---

## [v2.0] — 2026-04-22

Part of **Lince Investor Suite v3.0**.

### Added
- `pager` module with uniform PageUp / PageDown handling across every UI
  mode in the suite:
  - `PagingAppMixin` + `tui_paging_bindings()` for Textual apps.
  - `console_pager()` / `paged_print()` for interactive & console mode
    (pages long output through the system pager; Shift+PageUp/Shift+PageDn
    still reach the terminal's scrollback).
  - `bind_tk_paging()` for Tkinter GUIs (maps `<Prior>` / `<Next>` to
    `yview_scroll`).
- `sector_registry` module: single source of truth for the Suite's
  specialized agents. Drives the new "Suggestion: use 'lynx-investor-X'
  instead" line that `SectorValidator` now appends to
  `SectorMismatchError` — while keeping the existing warning text as-is.
- `SectorValidator.agent_name` field so each agent identifies itself to
  the registry and is never suggested to itself.

### Changed
- Bumped to v2.0 alongside the Suite's v3.0 coordinated release.

---

## [v1.0] — 2026-04-20

First release — extracted from the shared scaffolding that had been duplicated
across `lynx-investor-basic-materials` and `lynx-investor-energy`.

### Added
- Suite-level metadata constants (`SUITE_NAME`, `SUITE_VERSION`, `SUITE_LABEL`,
  `LICENSE_TEXT`, author/year/license).
- `storage` with `set_base_dir()` initializer so each agent can point at its
  own data directory.
- `fetcher` for yfinance-backed `CompanyProfile` / `FinancialStatement` retrieval
  (uses `Protocol`-based factories so each agent keeps its own model classes).
- `news` parametrized by a per-agent sector keyword (e.g. `"mining stock"` vs
  `"energy stock"`).
- `reports` parametrized by per-agent User-Agent and EDGAR product identifier.
- `ticker` with ISIN / name / suffix fallback, suggestions parametrized.
- `SectorValidator` + `SectorMismatchError`: each agent declares allowed sectors,
  industries, and description regex patterns.
- `about` helpers: `build_about()` returns a uniform dict, plus CLI / TUI / GUI
  renderers.
- `cli.add_standard_args()` — argparse boilerplate shared across every agent.
- `logo.load_logo_ascii()`.
- `easter` with parametrized agent label + fortune quotes.
- `export.pdf` via weasyprint, `ExportFormat` enum.
- Shared `NewsArticle` data class.
- Part of **Lince Investor Suite v2.0**.

Part of the [Lince Investor Suite](https://github.com/borjatarraso?tab=repositories).
