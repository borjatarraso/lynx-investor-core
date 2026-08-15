---
ep_version: 1
project: lynx-investor-core
title: lynx-investor-core
status: PAUSED
last_touched: 2026-06-08
last_touched_text: 8 June 2026
section: sub
category: investments
generated: 2026-08-15
ep_locked: false   # set true and this file is never regenerated
---

# lynx-investor-core

> Common code shared across the modular sub-projects

🟠 **PAUSED** · last touched **8 June 2026** (last commit)

---

## What this is

Shared runtime for the **Lince Investor Suite** — the common scaffolding used by every `lynx-investor-*` agent and by the three auxiliary apps (`lynx-fundamental`, `lynx-compare`, `lynx-portfolio`).

This package is **not a standalone tool**. Install it alongside one of the Suite packages below.

The Suite (current release: **v4.0**) bundles three families of programs:

Each agent analyzes a company against that sector's fundamentals; the sector gate refuses to analyze companies outside its scope and suggests which other Suite agent to use instead.

`lynx-portfolio` ships a dashboard that turns the raw portfolio into six at-a-glance views, all built on a single `dashboard.py` module so the same numbers flow to every UI (CLI, REPL, TUI, GUI, REST API):

The REST API is **authenticated with a bearer token** that the server generates on first start (stored at `data/api_token`, mode `0600`). The server binds to `127.0.0.1` by default — `--unsafe-bind-all` is required to bind `0.0.0.0`. See [`lynx-portfolio/docs/REST_API.md`](https://github.com/borjatarraso/lynx-portfolio/blob/main/docs/REST_API.md) for the full endpoint reference.

Every program in the Suite — GUI, TUI, interactive REPL, and plain console commands — honors the same keys:

`Shift+PageUp` / `Shift+PageDown` remain reserved for the terminal emulator's own scrollback — the Suite never intercepts them.

`sector_registry.AGENT_REGISTRY` lists every specialized investor and the Yahoo sector / industry / description fingerprints they own. When a sector gate refuses a profile, `format_agent_suggestion(profile, current_agent=...)` returns a ready-to-append line like:

`SectorValidator.build(..., agent_name="lynx-investor-basic-materials")` enables this automatically in every `SectorMismatchError` raised by that agent — the original scope-specific warning text is preserved exactly.

From a fresh clone of an agent repository:

Then install the agent as usual (`pip install -e .` inside the agent repo).

BSD 3-Clause © 2026 Borja Tarraso

This project is part of the **Lince Investor Suite**, authored and signed by

**Borja Tarraso** &lt;[borja.tarraso@member.fsf.org](mailto:borja.tarraso@member.fsf.org)&gt; Licensed under BSD-3-Clause.

Every report and export emitted by Suite tools includes this same signature in its footer. The shipped logo PNGs additionally carry the author's signature via steganography for provenance — please do not replace or re-encode the logo files.

<!-- LYNX-EP-FOOTER:BEGIN -->

New here, or coming back after a while? Read [`index.ep.md`](index.ep.md) (or open [`index.ep.html`](index.ep.html) in a browser) — the standard card that answers what this is, where to look first, and how to run it, in the same shape for every project.

🟠 **PAUSED** · last touched **8 June 2026**

<img src="https://www.cortex-university.com/static/brand/lince-logo.png" alt="Lince" width="96" height="96" align="left" style="margin-right:16px" />

**lynx-investor-core is proudly part of Lince.**

Part of the LINCE company · © All rights reserved

<!-- LYNX-EP-FOOTER:END -->

## Start here

- [`README.md`](README.md) — what the project is, in its own words
- [`CLAUDE.md`](CLAUDE.md) — working agreement for a session in this repo
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — module map and how the pieces fit
- [`ROADMAP.md`](ROADMAP.md) — where this is heading
- [`docs/README.md`](docs/README.md) — documentation index

## Run it

```bash
cd ~/claude/lince-investor/lynx-investor-core
python3 -m lynx_investor_core         # run the package
```

## The rest of it

**Directories**

- `docs/` — 7 entries
- `lynx_investor_core/` — 31 entries
- `lynx_investor_core.egg-info/` — 5 entries
- `tests/` — 17 entries

**Other documentation**

- [`AGENTS.md`](AGENTS.md)
- [`CHANGELOG.md`](CHANGELOG.md)
- [`DESIGN.md`](DESIGN.md)

**`docs/`** holds 7 files.

**Build / config**: `pyproject.toml`

---

## Ownership

<img src="https://www.cortex-university.com/static/brand/lince-logo.png" alt="Lince" width="96" height="96" align="left" style="margin-right:16px" />

**lynx-investor-core is proudly part of Lince.**

| Company ID | Headquarters |
|---|---|
| 3015071-2 | Helsinki, Finland |

Part of the LINCE company · © All rights reserved


<sub>Standard entry-point card (`index.ep.md`, format v1) — generated 2026-08-15 by Lynx Factory. Regenerating overwrites this file unless `ep_locked: true`.</sub>
