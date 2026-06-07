# UI vocabulary

A Suite-wide vocabulary so every agent feels like the same product.
Covers `themes`, `gui_themes`, `pager`, `about`, `author_footer`,
`easter`, `logo`, `lang_widget`.

## The four surfaces

Every Suite tool runs on one of four surfaces, and the same key
contracts hold on each:

| Surface | Framework | Module entry points |
|---|---|---|
| CLI (one-shot) | argparse + Rich console | `about`, `pager.console_pager`, `pager.paged_print` |
| Interactive REPL | Rich console with prompt loop | same as CLI, plus `easter` |
| TUI | Textual | `themes`, `pager.PagingAppMixin`, `pager.tui_paging_bindings` |
| GUI | Tkinter | `gui_themes`, `pager.bind_tk_paging`, `lang_widget` (Tk variant) |

UI imports are kept lazy. `import lynx_investor_core.pager` does
not trigger a `tkinter` or `textual` import — those happen inside
the functions that need them.

## Themes

`themes` is the Textual / Rich palette gallery. The Lynx house
themes (`lynx-mocha`, `lynx-latte`, `lynx-high-contrast`) lead the
rotation; the rest are well-known editor classics (Catppuccin,
Dracula, Gruvbox, Solarized, Tokyo Night, Nord, Monokai Pro, …)
and a small set of nerd / retro picks (Cyberpunk 2077, Fallout
Terminal, Matrix, Synthwave '84).

A Textual app gets the full gallery with:

```python
from lynx_investor_core.themes import register_suite_themes
register_suite_themes(app)
```

`gui_themes` is the Tk counterpart — the same palettes adapted to
ttk styles. Both surfaces share the same theme names so a user's
choice round-trips when switching modes.

`lynx-theme` (the Suite's standalone theme editor app) writes the
default theme to `$XDG_CONFIG_HOME/lynx-theme/default.json`; the
gallery modules read it at startup and apply it before any other
theme is registered.

## Pager contract

The keys are the same on all four surfaces:

| Mode | PageUp / PageDown | Helper |
|---|---|---|
| GUI | scroll the main canvas one page | `bind_tk_paging(root, canvas)` |
| TUI | page the focused scrollable widget | `PagingAppMixin` + `tui_paging_bindings()` |
| Interactive / CLI | page current output through `less` / `more` | `with console_pager(console): …` or `paged_print(console, renderable)` |

`Shift+PageUp` / `Shift+PageDown` are reserved for the terminal
emulator's own scrollback — the Suite never intercepts them.

The CLI pager only owns the *current* page of output: pressing
`PageUp` inside it scrolls within that page, never above it. Older
output stays in the terminal's scrollback, reachable via
`Shift+PageUp`.

## About dialog — `about`

`build_about(...)` returns a dataclass with every field the dialog
shows; per-surface renderers convert it to Rich, Textual, or Tk
output. The same data drives all four surfaces, so the wording stays
in sync.

## Author footer — `author_footer`

`render_author_footer()` is appended to every text / HTML / PDF
export by the consuming agents. The block is the Suite's signature,
keyed to the values in `lynx_investor_core/__init__.py`
(`__author__`, `__author_email__`, `__year__`).

## Easter eggs — `easter`

Three visuals parameterised per agent (rocket, matrix, fortune
cookie). They are intentionally lightweight — a single curses-style
Rich animation each — and are invoked only when the user triggers
the relevant interactive command.

## Language toggle — `lang_widget`

A small bottom-right widget mounted by every GUI / TUI app. Left-
click cycles language, right-click opens a chooser. The widget calls
into `translations.set_language()` and persists the choice via the
same module. The TUI variant binds `g` instead of using a mouse
target.

The cycle button is debounced via `lynx_investor_core.debounce`:
the same click handler used to trigger twice on a fast double-click,
landing the user on the wrong language.
