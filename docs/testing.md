# Testing

How the test suite is laid out and what the conventions are.

## Where the tests live

```
tests/
├── __init__.py
├── test_backtest.py
├── test_charts.py
├── test_debounce.py
├── test_gui_themes.py
├── test_i18n.py
├── test_logging.py
├── test_lynx_theme.py
├── test_openapi.py
├── test_pager.py
├── test_plugins.py
├── test_screener.py
├── test_sector_gate.py
├── test_sector_registry.py
├── test_translations.py
└── test_urlsafe.py
```

The layout mirrors the package. Adding a new module to
`lynx_investor_core/` means adding a new `tests/test_<module>.py`.
Anything that has not yet earned a test file is "untested" — there
is no implicit catch-all.

## Running

```sh
pytest -q
```

That's it. No fixtures bootstrap, no `conftest.py` magic, no
`tox.ini`. The full suite is fast (a few seconds) — keep it that
way by mocking network calls.

## What to mock and what to import

- **yfinance** is mocked everywhere. Tests that need a profile
  pass either a stub object satisfying the `_ProfileLike` protocol
  (see `test_sector_gate.py`) or a small dict matching `yf.Ticker.info`
  shape (`test_screener.py`).
- **SEC EDGAR / Google News RSS / Yahoo News** are mocked.
  `test_screener.py` patches the yfinance call sites; the same
  pattern applies if a new module reaches for the network.
- **Tk and Textual** are imported lazily inside the production code.
  Tests should not start a real Tk root or a Textual `App.run`; use
  `test_gui_themes.py` and `test_lynx_theme.py` as references for the
  patterns that avoid spawning a real event loop.
- **Filesystem** — `storage.set_base_dir(tmp_path)` at the top of any
  test that touches the cache, with `storage.set_mode("testing")`
  so the cache-read short-circuit kicks in.

## Snapshots and golden files

There aren't any. The suite favours behavioural assertions over
freezing rendered output, since terminal renderings (themes, charts,
about dialog) are surface-specific and brittle.

## Adding a test

1. Create `tests/test_<module>.py`.
2. Import the module under test directly:
   `from lynx_investor_core import <module>`.
3. Mock external IO at the import site of the module under test.
4. Run `pytest tests/test_<module>.py -q` locally before opening a
   commit.
