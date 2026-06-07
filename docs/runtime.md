# Runtime utilities

Cross-cutting modules that aren't owned by data, sector, UI, or i18n:
`cli`, `logging`, `plugins`, `openapi`, `urlsafe`, `debounce`.

## `cli` — argparse boilerplate

Every Suite agent's `cli.build_parser()` calls one helper:

```python
from lynx_investor_core.cli import add_standard_args

parser = argparse.ArgumentParser(prog="lynx-investor-energy", ...)
add_standard_args(parser, version_string=f"lynx-investor-energy {VERSION}")
```

That registers the entire shared argument surface:

- Run mode: `-p` / `--production-mode`, `-t` / `--testing-mode`
  (mutually exclusive, required).
- Positional `identifier` (ticker / ISIN / company name).
- UI mode group: `-i` / `--interactive-mode`, `-tui` /
  `--textual-ui`, `-s` / `--search`, `-x` / `--gui`.
- Cache / refresh: `--refresh`, `--drop-cache [TICKER]`,
  `--list-cache`.
- Skip flags: `--no-reports`, `--no-news`.
- Output: `--max-filings N`, `--verbose` / `-v`, `--export {txt,
  html,pdf}`, `--output PATH`.
- Help-style: `--version`, `--about`, `--explain [METRIC]`,
  `--explain-section [SECTION]`, `--explain-conclusion
  [CATEGORY]`.
- Locale: `-L` / `--locale CODE` for the gettext stack.

`positive_int` is the argparse `type=` helper that rejects 0 and
negatives — used wherever a count argument has to be ≥1.

`apply_locale(args)` is called by the agent right after
`parse_args`, before any user-visible output, so banners come out
already translated.

## `logging` — package logger accessor

`get_logger(name)` returns a configured logger. The module shadows
the stdlib `logging` name inside the package — inside core, prefer
`from .logging import get_logger`; from outside, it is
`from lynx_investor_core.logging import get_logger`. Don't rename
the module — every consumer imports it that way.

## `plugins` — entry-point discovery

Every sector agent and auxiliary app registers itself under the
`lynx_investor_suite.agents` entry-point group:

```toml
[project.entry-points."lynx_investor_suite.agents"]
mining = "lynx_mining.plugin:register"
```

The pointed-at `register()` returns a `SectorAgent` descriptor. The
dashboard calls `plugins.discover()` to list installed agents and
`plugins.launch(name, ...)` to start one.

Discovery is lazy: `import lynx_investor_core` is cheap and does
not import any agent. Editable installs (`pip install -e .`) must
be re-run after adding a new entry point, or `discover()` will not
see it.

## `openapi` — Flask OpenAPI mount

`mount_openapi(app, ...)` attaches a small schema layer to a Flask
application. The only current consumer is `lynx-portfolio`'s REST
server. The helper lives in core so the schema definitions stay in
one place even if a second app eventually exposes a REST surface.

## `urlsafe` — filesystem-safe encoding

Tiny helpers used by `storage` (the `_sanitize_ticker` path) and by
the CLI when constructing output file names from arbitrary user
input. Standalone tested (`tests/test_urlsafe.py`) so the round-trip
behaviour is locked in.

## `debounce` — click cooldown gate

`ClickDebouncer(cooldown_ms=600)` is a thread-safe per-key cooldown:

```python
debounce = ClickDebouncer(cooldown_ms=600)
button = ttk.Button(parent, command=debounce.wrap(self._launch_app))
```

Subsequent calls within `cooldown_ms` of the most recent are
dropped silently. Two constants set the conventional values:

- `DEFAULT_COOLDOWN_MS = 600` — for in-window button reuse.
- `LAUNCH_COOLDOWN_MS = 1500` — for detached subprocess launches,
  where the new window takes a moment to appear and the user is
  very likely to click again before they see it.

Time source is `time.monotonic` — immune to mid-run NTP
adjustments. The module is framework-agnostic (no Tk / Textual /
Rich imports) so it can wrap handlers on any surface.
