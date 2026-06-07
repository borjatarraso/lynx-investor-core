# Roadmap

What is intentionally still open in `lynx-investor-core`. Grounded in
the current codebase — no speculative features.

This is a shared runtime, so almost every item below is driven by a
need surfaced in one of the consuming repos (`lynx-investor-*`,
`lynx-fundamental`, `lynx-compare`, `lynx-portfolio`). The Suite
version (`SUITE_VERSION` in `lynx_investor_core/__init__.py`) is
6.0.0; the items below are post-6.0.0.

## Near term — gaps in the current modules

- **Translations parity.** `locales/extensive/` ships an English pool
  only; Spanish / Italian / German / French / Farsi entries fall back
  silently. Filling each pool to parity with `core/` is a data-only
  change.
- **Locale build tooling.** `.po` → `.mo` is documented but not
  automated. `scripts/compile_locales.py` is the planned entry point;
  the wheel still ships pre-built `.mo` files for now.
- **`reports` rate-limit handling.** The EDGAR client respects SEC's
  User-Agent requirement but does not back off on 429 responses; a
  retry-with-jitter helper would be a small, local improvement.
- **`fetcher` cache age awareness.** `storage.get_cache_age_hours()`
  exists but no fetcher path consults it; refreshing decisions are
  pushed to the consuming agent today. A `max_age` keyword on
  `fetch_company_profile()` would let core own the freshness rule.
- **Two-stack i18n consolidation.** `i18n` (gettext) and
  `translations` (JSON pool) coexist for historical reasons. A future
  cleanup may collapse one onto the other, but only once every
  consumer has migrated off the gettext entry points.

## Documented but unfinished surfaces

- **`openapi.mount_openapi()`** ships the schema layer used by
  `lynx-portfolio`'s REST server. The dashboard endpoint set is now
  stable; an auth-flow helper (bearer-token issuance, rotation) could
  reasonably move into core but is currently agent-side.
- **`plugins`** discovers sector plugin modules but the plugin contract
  is documented only through example. A short `docs/plugins.md` would
  unblock third-party screeners.
- **`charts`** uses plotext for ASCII charts. A Rich-renderable wrapper
  for the same data series would make GUI / TUI usage uniform with
  the console.

## Deliberately out of scope

These come up regularly and the answer is the same each time — they
belong in the consuming agents, not in core:

- **Domain enums (`stage`, `tier`, `commodity`).** Each agent owns
  its own taxonomy. Core takes profile factory callables exactly to
  keep these out.
- **Scoring rules.** Sector-specific weights and thresholds belong in
  the agent. Core ships the gate and the fetched data only.
- **An HTTP server.** Only the OpenAPI mount helper lives in core;
  the server is `lynx-portfolio`'s.
- **A CLI entry point.** The package exposes argparse helpers, not a
  console script.

## How to propose work

Open an issue at
<https://github.com/borjatarraso/lynx-investor-core/issues> with the
consuming repo and the use case. Cross-repo breakage budget is small
— any change to a public name in `lynx_investor_core/<module>.py`
needs to land here together with the matching update in every
sibling repo.
