# Design

Design rationale and invariants. `ARCHITECTURE.md` describes *what*
is here; this file explains *why* the pieces have the shape they
have. Treat anything below as a load-bearing decision — propose
changes via an issue before refactoring across the seam.

## Guiding constraints

1. **Library, not application.** The package ships zero console
   entry points, zero background threads, zero import-time IO. The
   eleven sector agents and the four auxiliary apps are the
   applications; core is the runtime they share.
2. **Stable public surface across eleven consumer repos.** Every
   public name in `lynx_investor_core/<module>.py` is reached by
   `from lynx_investor_core.<module> import …` in at least one
   sibling repo. Renaming a module or function is a coordinated
   change across the Suite.
3. **No domain types in core.** Sector-specific dataclasses, enums,
   and scoring rules belong in the agents. Core exchanges plain
   dicts and dataclasses with a fixed field set.
4. **Lazy UI imports.** `tkinter`, `textual`, and even `rich` (in
   some helpers) are imported inside the function that needs them.
   This keeps `import lynx_investor_core` cheap and lets the
   package be installed in headless environments without dragging a
   GUI stack along.

## Module-shape rules

### `storage` is pull-configured, not push-configured

`storage.set_base_dir(path)` is called by the consuming agent's
`__init__.py`. Core never decides where the base directory lives —
it cannot, because each agent has its own project root and would
otherwise step on its sibling's cache. Code inside core must never
call `set_base_dir()`; it can only call `get_base_dir()` and is
required to raise the existing `RuntimeError` if the consumer
forgot to configure it.

`_sanitize_ticker` is the only line standing between a hostile
ticker string and a path-traversal write. Keep its uppercase ASCII /
`.` / `-` whitelist as is; widening it requires a security review.

### `fetcher` uses factory callables, not domain dataclasses

`fetch_company_profile(ticker, profile_factory, *, info=None)`
takes the agent's `CompanyProfile` constructor as a callable and
hands it raw fields. This is the seam that keeps domain enums
(`stage`, `tier`, `commodity`) out of core. If a future feature
needs to inspect a domain-specific field inside `fetcher`, that
feature belongs in the agent, not in core.

### `sector_gate` and `sector_registry` are deliberately split

`sector_gate` is the runtime check used by the agent that is
*currently running*. `sector_registry` is the universe — every
agent the Suite ships, regardless of which one is installed
locally. A user with only `lynx-investor-energy` installed who
points it at a copper miner still gets a useful "use
`lynx-investor-basic-materials` instead" message, because the
registry knows about the other agent even though its package is
not on `sys.path`.

### Two i18n stacks coexist

`i18n` (gettext) and `translations` (JSON pool) are separate stacks
on purpose:

- `i18n` is the older, gettext-based path used by `cli` and the
  older parts of every consumer.
- `translations` is the JSON pool used by the GUI and TUI label
  paths, optimised for live-reload as the user switches language.

Collapsing the two is on the roadmap but not until every consumer
has migrated off `i18n`. Until then, never delete one assuming the
other replaces it. See `docs/i18n.md` for the migration shape.

### `logging` shadows the stdlib name on purpose

The package contains a module called `logging`. Inside core,
`from .logging import get_logger` works because the relative
import never looks at `sys.modules['logging']`. Outside core,
consumers reach for `from lynx_investor_core.logging import …`.
Renaming the module would force every consumer to change its
import — not worth the cleanliness.

### Optional UI imports go inside functions

```python
# Wrong:
import tkinter as tk
def bind_tk_paging(root, canvas): ...

# Right:
def bind_tk_paging(root, canvas):
    import tkinter as tk
    ...
```

`pager.py`, `about.py`, `themes.py`, `gui_themes.py`, and the
easter-egg helpers all follow the second form. Hoisting a UI
framework to module level breaks headless installs.

## What we do not do

- **No persistent state at import time.** No singletons constructed
  in module bodies, no I/O during import, no environment scanning
  except the documented `LYNX_LOCALE` / `LYNX_LANG` reads inside
  the relevant translator constructors.
- **No silent network fallbacks.** When yfinance / EDGAR / news RSS
  fails, the module returns an empty list or `{}` and lets the
  consumer decide what to render. We do not retry behind the
  caller's back.
- **No HTTP server in core.** `openapi.mount_openapi()` exists to
  let `lynx-portfolio` attach a schema layer; the Flask app itself
  is the consumer's.
- **No CLI in core.** `cli.add_standard_args()` is argparse
  boilerplate; the entry point is the consuming agent's.

## Compatibility policy

Versioning follows the Suite (`SUITE_VERSION` in `__init__.py`).
Public-name changes are major version bumps. New optional keyword
arguments are minor. Bug fixes are patch. The Suite ships the
sibling repos in lockstep, so a new public name should land here
*and* in every agent that needs it in the same release cycle.
