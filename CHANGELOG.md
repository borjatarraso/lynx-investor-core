# Changelog

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
