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
