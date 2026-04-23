"""Suite-wide Tkinter theme gallery.

Mirror of :mod:`lynx_investor_core.themes` for the Tkinter GUIs in the
Lince Investor Suite. The 22 palettes defined in the TUI registry are
reused here verbatim; this module knows how to walk a live Tk widget
tree and paint every widget with the right colors.

Typical usage inside a Tkinter application::

    from lynx_investor_core.gui_themes import ThemeCycler, apply_theme

    cycler = ThemeCycler(root)
    cycler.apply_current()
    root.bind_all("<Control-t>", lambda _: cycler.next())
    root.bind_all("<Control-T>", lambda _: cycler.previous())

Callers may also do a one-shot paint by importing :func:`apply_theme`
directly.

The module imports ``tkinter`` lazily so it can be imported in
headless / test environments that do not have a display.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from textual.theme import Theme

from lynx_investor_core.themes import SUITE_THEMES, SUITE_THEME_NAMES


__all__ = [
    "SUITE_GUI_THEMES",
    "SUITE_GUI_THEME_NAMES",
    "apply_theme",
    "list_themes_by_family",
    "theme_by_name",
    "ThemeCycler",
]


# Re-export (same Theme instances, the palette spec is identical between TUI/GUI)
SUITE_GUI_THEMES: List[Theme] = list(SUITE_THEMES)
SUITE_GUI_THEME_NAMES: List[str] = list(SUITE_THEME_NAMES)

DEFAULT_THEME_NAME = "catppuccin-mocha"


def theme_by_name(name: str) -> Optional[Theme]:
    """Return the :class:`Theme` matching *name* or ``None``."""
    for theme in SUITE_GUI_THEMES:
        if theme.name == name:
            return theme
    return None


def list_themes_by_family() -> Dict[str, List[str]]:
    """Group Suite themes into a family → [theme-name] dict for menus.

    The order within each list is the rotation order so menu items
    visibly follow the ``Ctrl+T`` cycle. Families:

    - "Lynx"               — lynx-theme, lynx-theme-light, terminal-default
    - "Editor classics"    — black-and-white, github-dark, github-light,
                              vscode-light, sublime-default, ayu-dark,
                              night-owl, vim-default, emacs-classic
    - "Catppuccin"         — mocha, macchiato, frappé, latte
    - "Popular dark"       — dracula, tokyo-night, tokyo-night-storm,
                              nord, one-dark, gruvbox-dark, monokai-pro,
                              rose-pine, kanagawa, everforest-dark,
                              solarized-dark
    - "Light"              — gruvbox-light, rose-pine-dawn, solarized-light
    - "Retro / nerd"       — matrix, cyberpunk-2077, synthwave-84,
                              fallout-terminal
    """
    return {
        "Lynx": [
            "lynx-theme",
            "lynx-theme-light",
            "terminal-default",
        ],
        "Editor classics": [
            "black-and-white",
            "github-dark",
            "github-light",
            "vscode-light",
            "sublime-default",
            "ayu-dark",
            "night-owl",
            "vim-default",
            "emacs-classic",
        ],
        "Catppuccin": [
            "catppuccin-mocha",
            "catppuccin-macchiato",
            "catppuccin-frappe",
            "catppuccin-latte",
        ],
        "Popular dark": [
            "dracula",
            "tokyo-night",
            "tokyo-night-storm",
            "nord",
            "one-dark",
            "gruvbox-dark",
            "monokai-pro",
            "rose-pine",
            "kanagawa",
            "everforest-dark",
            "solarized-dark",
        ],
        "Light": [
            "gruvbox-light",
            "rose-pine-dawn",
            "solarized-light",
        ],
        "Retro / nerd": [
            "matrix",
            "cyberpunk-2077",
            "synthwave-84",
            "fallout-terminal",
        ],
    }


def _resolve(theme: Union[str, Theme]) -> Optional[Theme]:
    if isinstance(theme, Theme):
        return theme
    return theme_by_name(theme)


# ---------------------------------------------------------------------------
# Widget painter
# ---------------------------------------------------------------------------


def _safe_configure(widget, **kwargs) -> None:
    """Configure *widget* ignoring options it does not support."""
    for key, value in kwargs.items():
        try:
            widget.configure(**{key: value})
        except Exception:
            # Option not supported on this widget class — skip silently.
            continue


def _paint_tk_widget(widget, theme: Theme) -> None:
    """Apply *theme* to a classic (non-ttk) Tk widget."""
    import tkinter as tk

    cls = widget.winfo_class()
    bg = theme.background
    fg = theme.foreground
    surface = theme.surface or bg
    panel = theme.panel or surface
    primary = theme.primary or fg
    accent = theme.accent or primary

    if cls in ("Tk", "Toplevel"):
        _safe_configure(widget, bg=bg)
        return

    if cls == "Frame" or cls == "Labelframe":
        _safe_configure(widget, bg=bg)
        return

    if cls == "Label":
        _safe_configure(widget, bg=bg, fg=fg)
        return

    if cls == "Button":
        _safe_configure(
            widget,
            bg=panel,
            fg=fg,
            activebackground=primary,
            activeforeground=bg,
            highlightbackground=accent,
            highlightcolor=accent,
        )
        return

    if cls == "Checkbutton" or cls == "Radiobutton":
        _safe_configure(
            widget,
            bg=bg,
            fg=fg,
            activebackground=panel,
            activeforeground=fg,
            selectcolor=surface,
        )
        return

    if cls == "Entry":
        _safe_configure(
            widget,
            bg=surface,
            fg=fg,
            insertbackground=fg,
            selectbackground=primary,
            selectforeground=bg,
            highlightbackground=accent,
            highlightcolor=accent,
            disabledbackground=surface,
            disabledforeground=fg,
        )
        return

    if cls == "Text":
        _safe_configure(
            widget,
            bg=surface,
            fg=fg,
            insertbackground=fg,
            selectbackground=primary,
            selectforeground=bg,
            highlightbackground=accent,
            highlightcolor=accent,
        )
        return

    if cls == "Canvas":
        _safe_configure(
            widget,
            bg=bg,
            highlightbackground=accent,
            highlightcolor=accent,
        )
        return

    if cls == "Listbox":
        _safe_configure(
            widget,
            bg=surface,
            fg=fg,
            selectbackground=primary,
            selectforeground=bg,
            highlightbackground=accent,
            highlightcolor=accent,
        )
        return

    if cls == "Menu":
        _safe_configure(
            widget,
            bg=panel,
            fg=fg,
            activebackground=primary,
            activeforeground=bg,
            selectcolor=accent,
        )
        return

    if cls == "Menubutton":
        _safe_configure(
            widget,
            bg=panel,
            fg=fg,
            activebackground=primary,
            activeforeground=bg,
        )
        return

    if cls == "Scale":
        _safe_configure(
            widget,
            bg=bg,
            fg=fg,
            troughcolor=surface,
            activebackground=primary,
            highlightbackground=accent,
        )
        return

    if cls == "Scrollbar":
        _safe_configure(
            widget,
            bg=panel,
            troughcolor=surface,
            activebackground=primary,
            highlightbackground=accent,
        )
        return

    if cls == "Spinbox":
        _safe_configure(
            widget,
            bg=surface,
            fg=fg,
            insertbackground=fg,
            selectbackground=primary,
            selectforeground=bg,
            buttonbackground=panel,
            highlightbackground=accent,
            highlightcolor=accent,
        )
        return

    if cls == "PanedWindow":
        _safe_configure(widget, bg=panel)
        return

    # Fallback — try the common bg/fg combo.
    _safe_configure(widget, bg=bg, fg=fg)


def _configure_ttk(root, theme: Theme) -> None:
    """Configure ttk named styles to match *theme*."""
    import tkinter as tk
    from tkinter import ttk

    bg = theme.background
    fg = theme.foreground
    surface = theme.surface or bg
    panel = theme.panel or surface
    primary = theme.primary or fg
    accent = theme.accent or primary

    # Switch to a theme that honours color overrides.
    try:
        root.tk.call("::ttk::style", "theme", "use", "clam")
    except tk.TclError:
        pass

    style = ttk.Style(root)

    # Base Lynx styles (so callers can opt-in explicitly)
    style.configure("Lynx.TFrame", background=bg)
    style.configure("Lynx.TLabel", background=bg, foreground=fg)
    style.configure(
        "Lynx.TButton",
        background=panel,
        foreground=fg,
        bordercolor=accent,
        lightcolor=panel,
        darkcolor=panel,
    )
    style.map(
        "Lynx.TButton",
        background=[("active", primary), ("pressed", primary)],
        foreground=[("active", bg), ("pressed", bg)],
    )
    style.configure(
        "Lynx.TEntry",
        fieldbackground=surface,
        foreground=fg,
        insertcolor=fg,
        bordercolor=accent,
    )
    style.configure(
        "Lynx.Treeview",
        background=surface,
        fieldbackground=surface,
        foreground=fg,
    )
    style.map(
        "Lynx.Treeview",
        background=[("selected", primary)],
        foreground=[("selected", bg)],
    )
    style.configure("Lynx.TCombobox", fieldbackground=surface, foreground=fg)

    # Also paint the *default* ttk element names so widgets that were
    # created without a ``style="Lynx.*"`` assignment still pick up the
    # palette.
    style.configure(".", background=bg, foreground=fg, fieldbackground=surface)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure(
        "TButton",
        background=panel,
        foreground=fg,
        bordercolor=accent,
    )
    style.map(
        "TButton",
        background=[("active", primary), ("pressed", primary)],
        foreground=[("active", bg), ("pressed", bg)],
    )
    style.configure(
        "TEntry",
        fieldbackground=surface,
        foreground=fg,
        insertcolor=fg,
        bordercolor=accent,
    )
    style.configure(
        "TCombobox",
        fieldbackground=surface,
        foreground=fg,
        background=panel,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", surface)],
        foreground=[("readonly", fg)],
    )
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.configure("TNotebook", background=bg, bordercolor=accent)
    style.configure(
        "TNotebook.Tab",
        background=panel,
        foreground=fg,
        padding=(10, 4),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", primary)],
        foreground=[("selected", bg)],
    )
    style.configure(
        "Treeview",
        background=surface,
        fieldbackground=surface,
        foreground=fg,
    )
    style.map(
        "Treeview",
        background=[("selected", primary)],
        foreground=[("selected", bg)],
    )
    style.configure(
        "Treeview.Heading",
        background=panel,
        foreground=fg,
    )
    style.configure(
        "TScrollbar",
        background=panel,
        troughcolor=surface,
        bordercolor=accent,
        arrowcolor=fg,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=panel,
        troughcolor=surface,
        bordercolor=accent,
        arrowcolor=fg,
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=panel,
        troughcolor=surface,
        bordercolor=accent,
        arrowcolor=fg,
    )
    style.configure(
        "TProgressbar",
        background=primary,
        troughcolor=surface,
        bordercolor=accent,
    )
    style.configure("TSeparator", background=panel)
    style.configure("TPanedwindow", background=panel)


def _walk(widget, theme: Theme) -> None:
    """Depth-first walk painting each widget with *theme*."""
    try:
        _paint_tk_widget(widget, theme)
    except Exception:
        pass

    try:
        children = widget.winfo_children()
    except Exception:
        children = []
    for child in children:
        _walk(child, theme)


def apply_theme(root, *, theme: Union[str, Theme]) -> None:
    """Apply a Suite theme to every widget beneath *root*.

    Parameters
    ----------
    root:
        The Tk root (``tk.Tk`` or ``tk.Toplevel``) whose subtree will be
        painted.
    theme:
        Either the theme *name* (e.g. ``"dracula"``) or a
        :class:`textual.theme.Theme` instance.
    """
    resolved = _resolve(theme)
    if resolved is None:
        raise ValueError(f"Unknown Suite GUI theme: {theme!r}")

    _configure_ttk(root, resolved)
    _walk(root, resolved)


# ---------------------------------------------------------------------------
# Cycler
# ---------------------------------------------------------------------------


class ThemeCycler:
    """Cycle the Suite theme gallery on a Tk root.

    Parameters
    ----------
    root:
        The Tk root instance.
    start:
        Name of the initial theme to apply. Defaults to
        ``"catppuccin-mocha"``.
    """

    def __init__(self, root, start: str = DEFAULT_THEME_NAME) -> None:
        self._root = root
        self._themes: List[Theme] = list(SUITE_GUI_THEMES)
        names = [t.name for t in self._themes]
        try:
            self._index = names.index(start)
        except ValueError:
            self._index = 0
        self._applied = False

    # ----- state ----------------------------------------------------------

    @property
    def current(self) -> Theme:
        return self._themes[self._index]

    @property
    def current_name(self) -> str:
        return self.current.name

    @property
    def themes(self) -> List[Theme]:
        return list(self._themes)

    # ----- actions --------------------------------------------------------

    def apply_current(self) -> Theme:
        """Paint the root with the currently-selected theme."""
        apply_theme(self._root, theme=self.current)
        self._applied = True
        return self.current

    def next(self) -> Theme:
        """Advance to the next palette (wraps) and apply it."""
        self._index = (self._index + 1) % len(self._themes)
        return self.apply_current()

    def previous(self) -> Theme:
        """Step to the previous palette (wraps) and apply it."""
        self._index = (self._index - 1) % len(self._themes)
        return self.apply_current()

    def set(self, name: str) -> Theme:
        """Jump to a specific theme by name and apply it."""
        for idx, theme in enumerate(self._themes):
            if theme.name == name:
                self._index = idx
                return self.apply_current()
        raise ValueError(f"Unknown Suite GUI theme: {name!r}")
