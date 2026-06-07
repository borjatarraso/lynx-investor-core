# docs/

Deep-dive documentation for the `lynx-investor-core` runtime. The
repo-level `README.md` is the user-facing intro; `ARCHITECTURE.md`
is the top-down tour; the files in this directory zoom in on one
logical group at a time.

| File | Scope |
|---|---|
| [`data.md`](data.md) | Fetcher, news, reports, ticker, storage, cache layout |
| [`sector.md`](sector.md) | `SectorValidator` + `AGENT_REGISTRY` interaction |
| [`ui.md`](ui.md) | Themes, pager contract, about dialog, easter visuals |
| [`i18n.md`](i18n.md) | The two parallel i18n stacks (gettext + JSON pool) |
| [`runtime.md`](runtime.md) | `cli`, `logging`, `plugins`, `openapi`, `urlsafe` |
| [`testing.md`](testing.md) | How the test suite is laid out and what to mock |
