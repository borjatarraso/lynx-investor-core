# Sector logic

How `sector_gate` and `sector_registry` cooperate, with the analysis
utilities (`screener`, `backtest`, `charts`) that compose on top.

## The gate — `sector_gate.SectorValidator`

Each specialized agent ships one immutable `SectorValidator`,
constructed at agent import time:

```python
from lynx_investor_core.sector_gate import SectorValidator

VALIDATOR = SectorValidator.build(
    allowed_sectors={"Energy"},
    allowed_industries={"oil & gas", "midstream", "refining"},
    description_patterns=(r"\bcrude\b", r"\bnatural gas\b"),
    scope_description="energy",
    agent_name="lynx-investor-energy",
)
```

`validate(profile)` walks a three-step allow chain:

1. **Sector exact match** — Yahoo's `sector` field (e.g. `"Energy"`)
   is compared, case-insensitively, against `allowed_sectors`.
2. **Industry substring match** — Yahoo's `industry` is matched as a
   substring in either direction (`"oil & gas integrated"` contains
   `"oil & gas"`, and `"oil"` is contained in `"oil & gas"`).
3. **Description regex match** — the business description is searched
   for each `description_patterns` regex. Word boundaries are required
   so `\bore\b` does not match `store` — that is the agent's
   responsibility, not the gate's.

A pass at any step returns; a failure at all three raises
`SectorMismatchError` with a stable message:

```
{Company} ({TICKER}) is in the '{Sector}' / '{Industry}'
sector/industry, which is outside {scope_description}.
Suggestion: use 'lynx-investor-energy' from the Lince Investor Suite instead.
```

The trailing `Suggestion:` line is appended only when the validator
knows `agent_name` *and* the registry can identify a sibling agent
the profile fits better. Validators without an `agent_name` raise the
same message without the suggestion — the older suite-internal
behaviour, preserved on purpose.

## The registry — `sector_registry.AGENT_REGISTRY`

A frozen table of the eleven specialized agents, each entry an
`AgentEntry`:

```python
AgentEntry(
    name="lynx-investor-energy",
    display_name="Lince Investor — Energy",
    sectors=frozenset({"energy"}),
    industries=frozenset({"oil & gas", "midstream", ...}),
    description_patterns=("\\bcrude\\b", "\\bnatural gas\\b", ...),
)
```

`suggest_agent(profile, current_agent=...)` walks the registry and
returns the first entry whose `matches(profile)` is True, skipping
`current_agent` (so a misfire inside the right agent does not loop).
`format_agent_suggestion(profile, current_agent=...)` is the thin
formatter consumed by `sector_gate` — it returns either an empty
string (no suggestion available) or the canonical line.

The registry is the single source of truth for "what agent owns this
sector". When a new sector agent is added to the Suite:

1. Add an `AgentEntry` to `AGENT_REGISTRY`.
2. Ship the new agent repo with its own `SectorValidator.build(
   …, agent_name="lynx-investor-<new>")` call.

Nothing else in core needs to change.

## Why both pieces, separately

The split is deliberate. `sector_gate` is the runtime check used by
the agent that is *currently running*. `sector_registry` is the
universe — every agent the Suite ships, regardless of which one is
installed locally. A user with only `lynx-investor-energy` installed
who points it at a copper miner still gets a useful "use
`lynx-investor-basic-materials` instead" message, because the
registry knows about the other agent even though its package is not
on `sys.path`.

## Analytical helpers

These modules compose with the gate but do not depend on it:

- **`screener`** — `run_screener(universe, filters)` walks a
  user-supplied list of tickers and returns the rows that pass a tiny
  filter DSL (`(field, op, value)` triples). yfinance is queried per
  ticker; large universes should be screened in chunks, the module
  does not batch.
- **`backtest`** — historical replay against a strategy callable.
  Used by the specialized agents to validate their scoring rules.
- **`charts`** — ASCII charts built on plotext. Consumed by both the
  REPL and the TUI; the GUI uses a different chart stack.
