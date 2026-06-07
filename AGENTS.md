# AGENTS.md — lynx-investor-core

Shared runtime for the Lince Investor Suite. This file is the entry
point for any contributor (or scripted assistant) working in this
repository. Read this first, then the scoped `AGENTS.md` inside the
module you intend to touch.

## What this project is

`lynx-investor-core` is a Python library — not an end-user tool. It is
installed alongside one of the Suite agents (`lynx-investor-*`) or
auxiliary apps (`lynx-fundamental`, `lynx-compare`, `lynx-portfolio`)
and provides:

- Data sourcing helpers built on yfinance (`fetcher`, `news`,
  `reports`, `ticker`).
- A sector-gate / sector-registry pair so each specialized agent can
  refuse out-of-scope tickers and point the user at a better-fit
  sibling agent.
- A Suite-wide UI vocabulary: themes (Rich / Textual / Tkinter),
  About dialog, language widget, pager, easter eggs, ASCII logo.
- Two parallel i18n stacks (`i18n` for gettext PO/MO and
  `translations` for the JSON pool used by the UI).
- Cross-cutting runtime utilities: argparse boilerplate (`cli`),
  logging, OpenAPI mount helper, plugin loader, click debouncer,
  URL-safe encoder, on-disk storage for cached analyses.

It does not ship a console entry point of its own.

## Repository layout

```
lynx-investor-core/
├── AGENTS.md                 ← this file
├── ARCHITECTURE.md           ← module-by-module tour + dataflow
├── ROADMAP.md                ← what's next
├── README.md                 ← user-facing intro
├── CHANGELOG.md              ← release notes
├── pyproject.toml            ← build + dependency manifest
├── lynx_investor_core/       ← the actual package (see its AGENTS.md)
│   └── locales/              ← gettext + JSON translation catalogues
├── docs/                     ← deep-dive per-area docs
├── examples/                 ← short runnable demos (see its AGENTS.md)
├── scripts/                  ← dev utilities (see its AGENTS.md)
└── tests/                    ← pytest suite (mirrors package layout)
```

Each top-level source directory has its own `AGENTS.md` describing the
narrower contract.

## Build, install, test

The project is a plain setuptools package. For local development
against a Suite agent in a sibling checkout:

```sh
pip install -e .
pytest -q
```

That's it — there is no compile step. The gettext `.mo` files under
`lynx_investor_core/locales/<lang>/LC_MESSAGES/` are checked in; if
you edit a `.po` file run `scripts/compile_locales.py` to refresh the
matching `.mo`. The JSON translation pools under
`lynx_investor_core/locales/core/` and `…/extensive/` are loaded
directly and need no compile step.

## Conventions worth knowing before editing

- **Stability of the public surface.** Every Suite agent imports this
  package as `from lynx_investor_core.<name> import …`. Treat every
  module-level name exported by `lynx_investor_core/*.py` as public.
  Don't rename, move, or change the signature without a matching
  update in every consumer repo (see the `lynx-investor-*` siblings).
- **No domain types in core.** `fetcher` takes a `profile_factory`
  callable rather than importing the agent's `CompanyProfile`
  dataclass directly. Keep it that way — the moment core imports a
  sector-specific enum, the suite stops being layerable.
- **Storage is pull-configured.** `storage.set_base_dir()` is called
  by each consuming agent's `__init__.py`. Code inside core must
  never assume a base dir is configured; raise the existing
  `RuntimeError` if it is not.
- **Two i18n stacks coexist.** `i18n` (gettext) and `translations`
  (JSON pool) serve different surfaces. Read
  `docs/i18n.md` before touching either.
- **Optional imports.** `pager`, `about`, `themes`, and the easter-egg
  helpers all import their UI framework lazily inside the function
  that needs it. Keep import-time side effects to zero.
- **Tests live in `tests/`** and are named `test_<module>.py`. Use
  `pytest` (no fixtures-heavy framework on top). Mocking yfinance is
  preferred over hitting the network in CI; see `test_screener.py`.
- **Locale files are data.** Editing the JSON pools is a data change,
  not a code change. Keep keys identical across languages — missing
  keys fall back to English silently.

## Commit and PR style

- Imperative subject under ~70 chars, title-case ("Add", "Fix",
  "Refactor", "Tighten").
- No co-author trailers, no tool-generated trailers.
- Keep each commit focused — the recent history shows tight, single-
  intent commits and the same applies here.

## When you finish a change

Run `pytest -q`. If you touched anything UI-adjacent (themes,
`gui_themes`, `lang_widget`, pager) also exercise it from one of the
consuming agents because the test suite cannot drive Tk / Textual
end-to-end.
