# AGENTS.md — `lynx_investor_core` package

Scoped guidance for the package source files. Read the repo-root
`AGENTS.md` first for context.

## Responsibility

This is the single Python package shipped by the project. It is
imported as `lynx_investor_core` and provides the shared runtime that
every Suite agent and auxiliary app links against. The package is a
library — it must not start servers, write to stdout at import time,
or assume a CLI process owns the interpreter.

## Public interface

Every top-level module is part of the public API. Consumers in the
`lynx-investor-*` repos and the auxiliary apps reach into them as
`from lynx_investor_core.<module> import <name>`. The interface that
must not silently break:

| Module | Notable public names |
|---|---|
| `__init__` | `__version__`, `SUITE_NAME`, `SUITE_VERSION`, `SUITE_LABEL`, `LICENSE_TEXT` |
| `about` | `build_about()`, plus CLI / interactive / TUI / GUI renderers |
| `author_footer` | `render_author_footer()` |
| `backtest` | `run_backtest()`, `BacktestResult` |
| `charts` | ASCII chart helpers built on plotext |
| `cli` | `add_standard_args()`, `positive_int`, `apply_locale()` |
| `debounce` | `ClickDebouncer`, `DEFAULT_COOLDOWN_MS`, `LAUNCH_COOLDOWN_MS` |
| `easter` | rocket / matrix / fortune visuals (parameterised per agent) |
| `fetcher` | `fetch_info()`, `fetch_company_profile()`, statement helpers |
| `gui_themes` | Tk theme registry built on the same palettes as `themes` |
| `i18n` | `set_locale()`, `current_locale()`, `gettext`, `ngettext`, `_` |
| `lang_widget` | Suite language picker (Tk + Textual variants) |
| `logging` | `get_logger()` |
| `logo` | ASCII logo loader |
| `models` | tiny shared dataclasses (`NewsArticle`) |
| `news` | Yahoo + Google News RSS aggregation |
| `openapi` | `mount_openapi()` for the lynx-portfolio REST surface |
| `pager` | `PagingAppMixin`, `tui_paging_bindings`, `console_pager`, `paged_print`, `bind_tk_paging` |
| `plugins` | sector / agent plugin loader |
| `reports` | SEC EDGAR + SEDAR discovery and download |
| `screener` | sector-aware ticker screening helpers |
| `sector_gate` | `SectorValidator`, `SectorMismatchError` |
| `sector_registry` | `AgentEntry`, `AGENT_REGISTRY`, `suggest_agent`, `format_agent_suggestion` |
| `storage` | base-dir / mode management + JSON / text / binary helpers + cache |
| `themes` | Textual / Rich theme gallery and Lynx house themes |
| `ticker` | `resolve_ticker()` with ISIN / name fallbacks |
| `translations` | JSON-pool translator (`t()`, `set_language()`, `current_language()`) |
| `urlsafe` | safe encoding helpers for filenames and URLs |

## Local conventions

- **No `import lynx_investor_core.<x>` cycles.** Internal cross-module
  imports use the relative form (`from .storage import …`) only where
  already established. New cross-module references should follow the
  pattern of the surrounding file.
- **Optional UI frameworks (Textual / Tk / Rich) are imported inside
  functions**, not at module level, so `import lynx_investor_core` is
  cheap and doesn't require those packages to be present.
- **`logging` shadows the standard library** in this package. Inside
  the package, prefer `from .logging import get_logger`; from outside,
  it is `from lynx_investor_core.logging import get_logger`. Don't
  rename the module.
- **`storage` is configured by the consumer.** Do not call
  `set_base_dir()` from inside core — that is the agent's job.
- **`locales/` is package data.** Keep it inside this directory and
  keep the `pyproject.toml` `package-data` glob in sync if you add a
  new locale subdir.
- **JSON pool keys are stable identifiers**, not English text. Adding
  a key means adding it to `locales/core/us.json` (or `extensive/us.json`)
  first; other languages can lag.
- **Two parallel translation stacks.** Never delete one assuming the
  other replaces it — `i18n` (gettext) is used by `cli` and by older
  consumer code; `translations` is used by the GUI / TUI label paths.
  See `docs/i18n.md` for the split.

## Tests

Tests for this package live at the repo root in `tests/` and import
the modules directly. Add a `tests/test_<new_module>.py` alongside any
new module here.
