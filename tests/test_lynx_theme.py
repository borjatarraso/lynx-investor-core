"""Tests for the new Lynx house themes (v5.4)."""

from __future__ import annotations

import pytest

from lynx_investor_core import themes


def _hex_to_rgb(s: str):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def _brightness(hex_color: str) -> float:
    """ITU-R BT.601 luminance of a #RRGGBB color."""
    r, g, b = _hex_to_rgb(hex_color)
    return (r * 299 + g * 587 + b * 114) / 1000


class TestLynxThemeRegistration:
    def test_in_suite_gallery(self) -> None:
        names = {t.name for t in themes.SUITE_THEMES}
        assert "lynx-theme" in names
        assert "lynx-theme-light" in names
        assert "terminal-default" in names

    def test_listed_first_in_rotation(self) -> None:
        # House themes should appear at the head of the rotation so the
        # theme-cycle key finds them quickly.
        first_three = [t.name for t in themes.SUITE_THEMES[:3]]
        assert first_three == ["lynx-theme", "lynx-theme-light", "terminal-default"]


class TestLynxThemePnLContrast:
    """The whole point: success/error must be vivid true green / red."""

    @pytest.mark.parametrize("theme_obj,min_delta", [
        (themes.LYNX_THEME, 100),        # dark bg: very high delta required
        (themes.LYNX_THEME_LIGHT, 80),
        (themes.TERMINAL_DEFAULT, 150),
    ])
    def test_success_is_distinctly_green(self, theme_obj, min_delta: int) -> None:
        r, g, b = _hex_to_rgb(theme_obj.success)
        # Green channel must dominate the other two by a wide margin.
        assert g > r + min_delta, f"{theme_obj.name}: success not green-dominant"
        assert g > b + min_delta, f"{theme_obj.name}: success has too much blue"

    @pytest.mark.parametrize("theme_obj,min_delta", [
        (themes.LYNX_THEME, 100),
        (themes.LYNX_THEME_LIGHT, 70),
        (themes.TERMINAL_DEFAULT, 150),
    ])
    def test_error_is_distinctly_red(self, theme_obj, min_delta: int) -> None:
        r, g, b = _hex_to_rgb(theme_obj.error)
        assert r > g + min_delta, f"{theme_obj.name}: error not red-dominant"
        assert r > b + min_delta, f"{theme_obj.name}: error has too much blue"

    @pytest.mark.parametrize("theme_obj", [
        themes.LYNX_THEME,
        themes.LYNX_THEME_LIGHT,
        themes.TERMINAL_DEFAULT,
    ])
    def test_success_and_error_are_far_apart(self, theme_obj) -> None:
        """A colourblind-adjacent check: success and error must be
        unambiguously different, even ignoring the green/red channels."""
        sr, sg, sb = _hex_to_rgb(theme_obj.success)
        er, eg, eb = _hex_to_rgb(theme_obj.error)
        # Total channel-delta must be sizeable.
        delta = abs(sr - er) + abs(sg - eg) + abs(sb - eb)
        assert delta > 250

    @pytest.mark.parametrize("theme_obj", [
        themes.LYNX_THEME,
        themes.LYNX_THEME_LIGHT,
        themes.TERMINAL_DEFAULT,
    ])
    def test_warning_doesnt_clash_with_success_or_error(self, theme_obj) -> None:
        """Warning should be visually distinct from both gain and loss."""
        for critical in (theme_obj.success, theme_obj.error):
            cr, cg, cb = _hex_to_rgb(critical)
            wr, wg, wb = _hex_to_rgb(theme_obj.warning)
            delta = abs(cr - wr) + abs(cg - wg) + abs(cb - wb)
            assert delta > 80, (
                f"{theme_obj.name}: warning too close to {critical}"
            )


class TestLynxThemeContrast:
    """Foreground vs background must meet a readable contrast ratio."""

    @pytest.mark.parametrize("theme_obj", [
        themes.LYNX_THEME,
        themes.LYNX_THEME_LIGHT,
        themes.TERMINAL_DEFAULT,
    ])
    def test_fg_bg_contrast(self, theme_obj) -> None:
        # Rough brightness-delta check; real WCAG AA needs ratio ≥ 4.5:1.
        fg = _brightness(theme_obj.foreground)
        bg = _brightness(theme_obj.background)
        assert abs(fg - bg) > 150, f"{theme_obj.name}: fg/bg too similar"


class TestLynxThemeNames:
    def test_names_stable(self) -> None:
        assert themes.LYNX_THEME.name == "lynx-theme"
        assert themes.LYNX_THEME_LIGHT.name == "lynx-theme-light"
        assert themes.TERMINAL_DEFAULT.name == "terminal-default"

    def test_dark_flag_correct(self) -> None:
        assert themes.LYNX_THEME.dark is True
        assert themes.LYNX_THEME_LIGHT.dark is False
        assert themes.TERMINAL_DEFAULT.dark is True


class TestEditorClassicsRegistered:
    """v5.5: editor / terminal classics are in the Suite gallery."""

    @pytest.mark.parametrize("name", [
        "black-and-white",
        "emacs-classic",
        "vim-default",
        "sublime-default",
        "vscode-light",
        "github-light",
        "github-dark",
        "ayu-dark",
        "night-owl",
    ])
    def test_present(self, name: str) -> None:
        names = {t.name for t in themes.SUITE_THEMES}
        assert name in names

    def test_black_and_white_is_monochrome(self) -> None:
        t = themes.BLACK_AND_WHITE
        # Every notable color channel identical or near-identical → monochrome.
        for color in (t.primary, t.foreground, t.success, t.error):
            r, g, b = _hex_to_rgb(color)
            assert abs(r - g) <= 5 and abs(g - b) <= 5

    def test_github_dark_is_dark(self) -> None:
        assert themes.GITHUB_DARK.dark is True
        assert _brightness(themes.GITHUB_DARK.background) < 30

    def test_emacs_classic_is_light(self) -> None:
        assert themes.EMACS_CLASSIC.dark is False
        assert _brightness(themes.EMACS_CLASSIC.background) > 240
