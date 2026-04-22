"""Shared PageUp / PageDown scrolling helpers for the Lince Investor Suite.

Every program in the suite — the graphical GUI, the Textual TUI, the
interactive REPL, and the plain console commands — honors the same
``PageUp`` / ``PageDown`` contract:

* **TUI** — ``PageUp``/``PageDown`` page the currently focused scrollable
  widget (typically the report view). ``ctrl+home`` / ``ctrl+end`` jump to
  the extremes.

* **Interactive & console** — long output is funneled through a pager
  (``less`` on POSIX, ``more`` on Windows, or a built-in fallback). Inside
  that pager ``PageUp`` / ``PageDown`` walk up and down the current output
  but never scroll *above* it, because the pager only knows about that
  page. The terminal's native ``shift+PageUp`` / ``shift+PageDown``
  (which the terminal emulator implements) still reach the scrollback
  buffer for older output.

* **Graphical** — ``PageUp`` / ``PageDown`` call ``yview_scroll(±1, "pages")``
  on the main scrollable canvas of the window.

The module is intentionally framework-agnostic; every helper is optional
and only imports its dependency (``textual``, ``rich``, ``tkinter``) when
actually invoked.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Any, Iterable, List, Optional

__all__ = [
    "terminal_height",
    "terminal_width",
    "should_paginate",
    "console_pager",
    "paged_print",
    "tui_paging_bindings",
    "PagingAppMixin",
    "bind_tk_paging",
]


# ---------------------------------------------------------------------------
# Terminal geometry
# ---------------------------------------------------------------------------

def terminal_height(default: int = 24) -> int:
    """Return the current terminal height in rows (fallback: *default*)."""
    try:
        return os.get_terminal_size().lines
    except OSError:
        return default


def terminal_width(default: int = 80) -> int:
    """Return the current terminal width in columns (fallback: *default*)."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default


def should_paginate(line_count: int, *, margin: int = 2) -> bool:
    """Return True when *line_count* lines would overflow the terminal."""
    return (line_count + margin) >= terminal_height()


# ---------------------------------------------------------------------------
# Console / interactive pager
# ---------------------------------------------------------------------------

@contextmanager
def console_pager(console: Any, *, force: bool = False, styles: bool = True):
    """Context manager that funnels rich prints through an interactive pager.

    ``console`` must be a :class:`rich.console.Console` (or compatible)
    instance. Long output (or anything printed while *force* is True) is
    captured and handed to the system pager (``less`` / ``more``).

    The pager page always starts at the top of the captured output, so
    ``PageUp`` inside the pager never goes above that start — which is the
    behavior the suite promises for interactive and console mode.

    When stdout is not a TTY (piped to a file, run from CI, ``--export``
    target), the context manager becomes a no-op and printing happens
    straight to stdout so log redirection keeps working.
    """
    if not getattr(console, "is_terminal", True) and not force:
        yield console
        return
    if not sys.stdout.isatty() and not force:
        yield console
        return
    try:
        with console.pager(styles=styles):
            yield console
    except Exception:
        # Rich raises on exotic terminals; fall back to regular printing
        # rather than losing the user's output.
        yield console


def paged_print(console: Any, renderable: Any, *, force: bool = False) -> None:
    """Print *renderable* through a pager if its rendered height overflows.

    Cheap shortcut for ``with console_pager(...): console.print(renderable)``
    that first measures *renderable* so short output (a single line, a
    small table) never triggers the pager spuriously.
    """
    try:
        lines = console.render_lines(renderable, pad=False)
        line_count = len(lines)
    except Exception:
        line_count = terminal_height()  # err on the side of paging
    if force or should_paginate(line_count):
        with console_pager(console, force=True):
            console.print(renderable)
    else:
        console.print(renderable)


# ---------------------------------------------------------------------------
# Textual TUI bindings
# ---------------------------------------------------------------------------

def tui_paging_bindings() -> List[Any]:
    """Return the standard PageUp / PageDown bindings for a Textual App.

    The returned bindings delegate to :meth:`PagingAppMixin.action_page_up`
    and :meth:`PagingAppMixin.action_page_down` (which any App can expose
    by mixing in :class:`PagingAppMixin`).
    """
    from textual.binding import Binding  # lazy import
    return [
        Binding("pageup", "page_up", "PgUp", show=False),
        Binding("pagedown", "page_down", "PgDn", show=False),
        Binding("ctrl+home", "page_home", "Top", show=False),
        Binding("ctrl+end", "page_end", "Bottom", show=False),
    ]


class PagingAppMixin:
    """Adds suite-wide PageUp / PageDown handling to a Textual ``App``.

    The mixin first looks at the currently focused widget — Textual's
    :class:`ScrollableContainer` subclasses already define ``action_page_up``
    / ``action_page_down`` so keeping the key at the focused widget respects
    the user's intent when multiple scrollable panels are visible.

    When the focused widget doesn't support paging, the mixin falls back to
    the app-wide "main" scroll view (the attribute whose name is given by
    :attr:`_paging_main_view_attr`, defaulting to ``_report_view``).
    """

    #: Name of the ``self`` attribute that holds the primary scrollable
    #: container. Apps override this (or set ``_paging_main_view_attr =
    #: "my_view"``) when their main view is named differently.
    _paging_main_view_attr: str = "_report_view"

    def _paging_target(self):
        """Return the widget that page actions should scroll, or None."""
        focused = getattr(self, "focused", None)
        if focused is not None and hasattr(focused, "action_page_up"):
            return focused
        main = getattr(self, self._paging_main_view_attr, None)
        if main is not None and hasattr(main, "action_page_up"):
            return main
        # Last resort: the screen itself exposes scroll actions in Textual.
        screen = getattr(self, "screen", None)
        if screen is not None and hasattr(screen, "action_page_up"):
            return screen
        return None

    def action_page_up(self) -> None:  # pragma: no cover - thin shim
        target = self._paging_target()
        if target is not None:
            target.action_page_up()

    def action_page_down(self) -> None:  # pragma: no cover - thin shim
        target = self._paging_target()
        if target is not None:
            target.action_page_down()

    def action_page_home(self) -> None:  # pragma: no cover - thin shim
        target = self._paging_target()
        if target is None:
            return
        if hasattr(target, "scroll_home"):
            target.scroll_home(animate=False)
        elif hasattr(target, "action_scroll_home"):
            target.action_scroll_home()

    def action_page_end(self) -> None:  # pragma: no cover - thin shim
        target = self._paging_target()
        if target is None:
            return
        if hasattr(target, "scroll_end"):
            target.scroll_end(animate=False)
        elif hasattr(target, "action_scroll_end"):
            target.action_scroll_end()


# ---------------------------------------------------------------------------
# Tkinter / graphical bindings
# ---------------------------------------------------------------------------

def bind_tk_paging(root: Any, scroll_target: Any) -> None:
    """Bind ``<Prior>`` / ``<Next>`` (PageUp / PageDown) on *root*.

    ``scroll_target`` must expose ``yview_scroll`` (a ``tk.Canvas``,
    ``tk.Text``, or any Ttk scrollable). Pressing PageUp scrolls one page
    up, PageDown one page down. The binding is installed via
    :meth:`bind_all` so it works regardless of which child widget currently
    owns the focus.
    """
    def _page_up(_event=None) -> None:
        try:
            scroll_target.yview_scroll(-1, "pages")
        except Exception:
            pass

    def _page_down(_event=None) -> None:
        try:
            scroll_target.yview_scroll(1, "pages")
        except Exception:
            pass

    def _page_home(_event=None) -> None:
        try:
            scroll_target.yview_moveto(0.0)
        except Exception:
            pass

    def _page_end(_event=None) -> None:
        try:
            scroll_target.yview_moveto(1.0)
        except Exception:
            pass

    # <Prior> is Tk's event name for PageUp; <Next> is PageDown.
    root.bind_all("<Prior>", _page_up)
    root.bind_all("<Next>", _page_down)
    root.bind_all("<Control-Home>", _page_home)
    root.bind_all("<Control-End>", _page_end)
