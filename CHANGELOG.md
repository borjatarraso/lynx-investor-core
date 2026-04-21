# Changelog

All notable changes to **lynx-investor-core** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
