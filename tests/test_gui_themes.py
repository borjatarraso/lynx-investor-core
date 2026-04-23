"""Unit tests for :mod:`lynx_investor_core.gui_themes`."""

from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")

from lynx_investor_core.gui_themes import (  # noqa: E402
    SUITE_GUI_THEMES,
    SUITE_GUI_THEME_NAMES,
    ThemeCycler,
    apply_theme,
    list_themes_by_family,
    theme_by_name,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tk_root():
    """Create a hidden Tk root; skip when no display is available."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - depends on CI
        pytest.skip(f"no DISPLAY available for Tk: {exc}")
    root.withdraw()
    try:
        yield root
    finally:
        try:
            root.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Registry / lookup
# ---------------------------------------------------------------------------


def test_theme_by_name_known_returns_theme() -> None:
    theme = theme_by_name("catppuccin-mocha")
    assert theme is not None
    assert theme.name == "catppuccin-mocha"
    assert theme.background.startswith("#")


def test_theme_by_name_unknown_returns_none() -> None:
    assert theme_by_name("not-a-real-theme") is None


def test_suite_registry_has_expected_count() -> None:
    # Mirror of SUITE_THEMES — at least the core 22 palettes plus any
    # additions (lynx-theme family, etc.).
    assert len(SUITE_GUI_THEMES) >= 22
    assert len(SUITE_GUI_THEME_NAMES) == len(SUITE_GUI_THEMES)
    assert "catppuccin-mocha" in SUITE_GUI_THEME_NAMES
    assert "dracula" in SUITE_GUI_THEME_NAMES
    assert "lynx-theme" in SUITE_GUI_THEME_NAMES


# ---------------------------------------------------------------------------
# apply_theme
# ---------------------------------------------------------------------------


def test_apply_theme_works_headless(tk_root) -> None:
    from tkinter import ttk

    frame = tk.Frame(tk_root)
    frame.pack()
    label = tk.Label(frame, text="hello")
    label.pack()
    button = tk.Button(frame, text="click")
    button.pack()
    entry = tk.Entry(frame)
    entry.pack()
    text = tk.Text(frame)
    text.pack()
    canvas = tk.Canvas(frame)
    canvas.pack()
    listbox = tk.Listbox(frame)
    listbox.pack()
    _ttk_button = ttk.Button(frame, text="ttk")
    _ttk_button.pack()

    theme = theme_by_name("catppuccin-mocha")
    assert theme is not None

    apply_theme(tk_root, theme="catppuccin-mocha")

    assert frame.cget("bg").lower() == theme.background.lower()
    assert label.cget("bg").lower() == theme.background.lower()
    assert label.cget("fg").lower() == theme.foreground.lower()
    assert entry.cget("bg").lower() == theme.surface.lower()
    assert entry.cget("fg").lower() == theme.foreground.lower()
    assert text.cget("bg").lower() == theme.surface.lower()
    assert text.cget("fg").lower() == theme.foreground.lower()
    assert canvas.cget("bg").lower() == theme.background.lower()
    assert listbox.cget("bg").lower() == theme.surface.lower()
    # Button should be painted with a non-empty bg/fg from the theme palette.
    assert button.cget("bg").lower() in (
        theme.panel.lower(),
        theme.background.lower(),
        theme.surface.lower(),
    )
    assert button.cget("fg").lower() == theme.foreground.lower()


def test_apply_theme_unknown_raises(tk_root) -> None:
    with pytest.raises(ValueError):
        apply_theme(tk_root, theme="not-a-real-theme")


def test_apply_theme_hot_swap(tk_root) -> None:
    label = tk.Label(tk_root, text="hi")
    label.pack()

    apply_theme(tk_root, theme="catppuccin-mocha")
    mocha = theme_by_name("catppuccin-mocha")
    assert label.cget("bg").lower() == mocha.background.lower()

    apply_theme(tk_root, theme="dracula")
    dracula = theme_by_name("dracula")
    assert label.cget("bg").lower() == dracula.background.lower()
    assert label.cget("fg").lower() == dracula.foreground.lower()


# ---------------------------------------------------------------------------
# ThemeCycler
# ---------------------------------------------------------------------------


def test_theme_cycler_next_previous_wraps(tk_root) -> None:
    cycler = ThemeCycler(tk_root, start="catppuccin-mocha")
    cycler.apply_current()
    assert cycler.current_name == "catppuccin-mocha"

    # next() advances through the registry in order.
    second = cycler.next().name
    assert second != "catppuccin-mocha"
    assert cycler.current_name == second

    # previous() returns us to the starting theme.
    assert cycler.previous().name == "catppuccin-mocha"

    # Cycle all the way around: next() wraps back to the start.
    seen = [cycler.current_name]
    for _ in range(len(SUITE_GUI_THEMES)):
        seen.append(cycler.next().name)
    assert seen[-1] == seen[0]  # wrap-around confirmed

    # previous() also wraps: starting at theme[0] and going back lands
    # on the last theme in the list, regardless of how many are in it.
    first_name = SUITE_GUI_THEMES[0].name
    fresh = ThemeCycler(tk_root, start=first_name)
    fresh.apply_current()
    wrapped = fresh.previous().name
    assert wrapped == SUITE_GUI_THEMES[-1].name


def test_theme_cycler_unknown_start_defaults_to_first(tk_root) -> None:
    cycler = ThemeCycler(tk_root, start="does-not-exist")
    assert cycler.current_name == SUITE_GUI_THEMES[0].name


def test_theme_cycler_set_jumps_to_theme(tk_root) -> None:
    cycler = ThemeCycler(tk_root)
    cycler.set("nord")
    assert cycler.current_name == "nord"
    with pytest.raises(ValueError):
        cycler.set("not-a-theme")


# ---------------------------------------------------------------------------
# list_themes_by_family
# ---------------------------------------------------------------------------


def test_list_themes_by_family_all_nonempty() -> None:
    families = list_themes_by_family()
    assert families, "expected at least one family"
    for family, names in families.items():
        assert names, f"family {family!r} is empty"


def test_list_themes_by_family_covers_all_themes_exactly_once() -> None:
    families = list_themes_by_family()
    seen: List[str] = []
    for names in families.values():
        seen.extend(names)

    # Every Suite theme appears in exactly one family.
    for name in SUITE_GUI_THEME_NAMES:
        assert seen.count(name) == 1, (
            f"theme {name!r} should appear in exactly one family, "
            f"found {seen.count(name)}"
        )

    # No family contains a theme that is not in the registry.
    for name in seen:
        assert name in SUITE_GUI_THEME_NAMES, (
            f"family contains unknown theme {name!r}"
        )

    # The totals match.
    assert len(seen) == len(SUITE_GUI_THEME_NAMES)


def test_list_themes_by_family_deterministic_order() -> None:
    first = list_themes_by_family()
    second = list_themes_by_family()
    assert list(first.keys()) == list(second.keys())
    for family in first:
        assert first[family] == second[family]


def test_list_themes_by_family_expected_families() -> None:
    families = list_themes_by_family()
    assert list(families.keys()) == [
        "Lynx",
        "Editor classics",
        "Catppuccin",
        "Popular dark",
        "Light",
        "Retro / nerd",
    ]
