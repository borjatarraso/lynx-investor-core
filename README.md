# lynx-investor-core

Shared runtime for the **Lince Investor Suite** — the common scaffolding used by
every `lynx-investor-*` agent (basic materials, energy, information technology,
and future sector agents).

This package is **not a standalone tool**. Install it alongside one of the agent
packages:

- [lynx-investor-basic-materials](https://github.com/borjatarraso/lynx-investor-basic-materials)
- [lynx-investor-energy](https://github.com/borjatarraso/lynx-investor-energy)
- …

## What lives here

| Module | Purpose |
|---|---|
| `lynx_investor_core` (top level) | Suite metadata: `SUITE_NAME`, `SUITE_VERSION`, `SUITE_LABEL`, license text, author info |
| `storage` | Data-directory management for production/testing modes, JSON/text/binary helpers, cache lookup |
| `fetcher` | yfinance-backed company profile & financial-statement fetcher |
| `news` | Yahoo + Google-News-RSS news aggregation with per-agent sector keyword |
| `reports` | SEC EDGAR filing discovery + download helpers with per-agent User-Agent |
| `ticker` | Ticker / ISIN / name resolution with ambiguity fallbacks |
| `sector_gate` | `SectorValidator` base class + `SectorMismatchError` — each agent declares its allowed sectors, industries, and description patterns |
| `about` | `build_about()` plus rendering helpers for CLI / interactive / TUI / GUI About dialogs |
| `cli` | `add_standard_args()` — argparse boilerplate shared across every agent |
| `logo` | ASCII logo loader |
| `easter` | Shared easter-egg visuals (rocket / matrix / fortune cookie) parameterized per agent |
| `export.pdf` | PDF export via weasyprint |
| `export.ExportFormat` | Enum for export dispatch |

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
