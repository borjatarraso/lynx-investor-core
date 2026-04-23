"""Suite-wide TUI theme gallery.

A curated collection of the palettes that are most widely loved in the
developer / terminal community. Every Textual app in the Suite can
import :func:`register_suite_themes` and get the full gallery in one
call; the ``t`` key cycles through them.

Themes included (alphabetical within each family):

* **Catppuccin** — *Latte*, *Frappé*, *Macchiato*, *Mocha*. The four
  official variants of one of the most downloaded palettes on GitHub.
* **Dracula** — iconic purple/pink. 50k+ installs across every major
  editor.
* **Everforest Dark** — soft forest greens, easy on the eyes.
* **Gruvbox** — *Dark* and *Light*. Retro warm beige & rust, a cult
  classic.
* **Kanagawa** — inspired by Hokusai's *Great Wave*; muted blues,
  ochres, deep purples.
* **Monokai Pro** — the Sublime Text classic, refined.
* **Nord** — nordic, cold, minimalist blues.
* **One Dark Pro** — Atom/VSCode's flagship theme.
* **Rose Pine** / **Rose Pine Dawn** — natural pastels.
* **Solarized** — *Dark* and *Light*. Ethan Schoonover's timeless
  palette (2011, still beloved).
* **Tokyo Night** / **Tokyo Night Storm** — modern neon-on-indigo.

Nerd / retro picks:

* **Cyberpunk 2077** — neon pink, yellow, and electric blue.
* **Fallout Terminal** — green-amber CRT, Pip-Boy flavor.
* **Matrix** — pure ``#00ff41`` on ``#000000``.
* **Synthwave '84** — magenta sunset and cyan horizon.

All Theme objects are module-level constants so sector packages can
also import them individually to mix-and-match.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from textual.theme import Theme

if TYPE_CHECKING:
    from textual.app import App


__all__ = [
    # Lynx house themes (financial-first)
    "LYNX_THEME",
    "LYNX_THEME_LIGHT",
    "TERMINAL_DEFAULT",
    # Editor / terminal classics
    "BLACK_AND_WHITE",
    "EMACS_CLASSIC",
    "VIM_DEFAULT",
    "SUBLIME_DEFAULT",
    "VSCODE_LIGHT",
    "GITHUB_LIGHT",
    "GITHUB_DARK",
    "AYU_DARK",
    "NIGHT_OWL",
    # Catppuccin
    "CATPPUCCIN_LATTE",
    "CATPPUCCIN_FRAPPE",
    "CATPPUCCIN_MACCHIATO",
    "CATPPUCCIN_MOCHA",
    # Popular dark
    "DRACULA",
    "EVERFOREST_DARK",
    "GRUVBOX_DARK",
    "KANAGAWA",
    "MONOKAI_PRO",
    "NORD",
    "ONE_DARK",
    "ROSE_PINE",
    "SOLARIZED_DARK",
    "TOKYO_NIGHT",
    "TOKYO_NIGHT_STORM",
    # Light
    "GRUVBOX_LIGHT",
    "ROSE_PINE_DAWN",
    "SOLARIZED_LIGHT",
    # Nerd / retro
    "CYBERPUNK_2077",
    "CYBRDOTS",
    "FALLOUT_TERMINAL",
    "MATRIX",
    "SYNTHWAVE_84",
    # Collections + helpers
    "SUITE_THEMES",
    "SUITE_THEME_NAMES",
    "register_suite_themes",
]


# ---------------------------------------------------------------------------
# Lynx house themes — designed for portfolio viewing first
# ---------------------------------------------------------------------------
#
# The problem these solve: most of the beloved developer palettes below
# (Catppuccin, Dracula, Nord, Rose Pine, …) stylise ``success`` and
# ``error`` to harmonise with their overall aesthetic. For a code editor
# that's fine; for a portfolio it's a regression — ``+12.4%`` should
# *scream* green, ``-7.8%`` should *scream* red, and nothing else in the
# chrome should compete. The ``lynx-theme`` pair below deliberately
# keeps the backgrounds neutral and the gain/loss colours unmistakable.
#
# Use them when you're watching markets; use anything else when you
# want to be pretty.

LYNX_THEME = Theme(
    name="lynx-theme",
    primary="#3daee9",        # Lynx blue for headers, borders, selection
    secondary="#7dd3fc",      # softer blue for secondary chrome
    accent="#facc15",         # amber highlight for focus rings / notices
    warning="#f59e0b",        # distinct amber, never mistaken for red/green
    error="#ef4444",          # vivid true red — losses visible at a glance
    success="#22c55e",        # vivid true green — gains visible at a glance
    foreground="#e6eaf0",     # clean light gray, high contrast on dark
    background="#0f1419",     # Bloomberg-adjacent dark neutral (no color tint)
    surface="#171c23",
    panel="#252b33",
    dark=True,
)

LYNX_THEME_LIGHT = Theme(
    name="lynx-theme-light",
    primary="#0369a1",        # deep blue for headers
    secondary="#0891b2",      # teal
    accent="#ca8a04",         # gold
    warning="#d97706",        # orange — distinct from both red and green
    error="#b91c1c",          # deep red, readable on cream
    success="#16a34a",        # green readable on cream, distinctly green-dominant
    foreground="#1c1917",     # near-black
    background="#fafaf9",     # warm off-white (not pure white)
    surface="#f5f5f4",
    panel="#e7e5e4",
    dark=False,
)


# ---------------------------------------------------------------------------
# Terminal default — "no theme" — lets ANSI shine through
# ---------------------------------------------------------------------------
#
# Textual always applies *some* palette; there's no true pass-through.
# This theme picks colours as close to the classic VT100 / 16-color ANSI
# set as possible so the app looks "plain terminal" on most users'
# terminal-emulator colour schemes. In particular:
#
#   * background / surface / panel are black (terminal-typical);
#   * foreground is pure white;
#   * primary / success / error map to ANSI cyan / green / red at their
#     brightest so the user's terminal colour scheme shines through.
#
# It's the cleanest choice for users who've tuned their own terminal
# palette (Solarized, base16, etc.) and want the Suite to follow suit.

TERMINAL_DEFAULT = Theme(
    name="terminal-default",
    primary="#00afff",        # ansi-bright cyan
    secondary="#5fd7ff",
    accent="#ffff5f",         # ansi-bright yellow
    warning="#ffaf00",
    error="#ff0000",          # ansi red
    success="#00ff00",        # ansi green
    foreground="#ffffff",
    background="#000000",
    surface="#0a0a0a",
    panel="#1a1a1a",
    dark=True,
)


# ---------------------------------------------------------------------------
# Editor / terminal classics
# ---------------------------------------------------------------------------

BLACK_AND_WHITE = Theme(
    name="black-and-white",
    primary="#ffffff",
    secondary="#cccccc",
    accent="#ffffff",
    warning="#bbbbbb",
    error="#ffffff",          # B&W keeps PnL readable via bold/brightness
    success="#ffffff",
    foreground="#ffffff",
    background="#000000",
    surface="#0a0a0a",
    panel="#1a1a1a",
    dark=True,
)

# Emacs classic — the default 1985-era palette (light bg, classic primary
# colors). Matches the look of `M-x color-theme-classic` in emacs.
EMACS_CLASSIC = Theme(
    name="emacs-classic",
    primary="#0000ff",        # classic emacs function-name blue
    secondary="#a020f0",      # keyword purple
    accent="#ff00ff",          # string magenta
    warning="#b8860b",         # dark goldenrod for warnings
    error="#ff0000",
    success="#228b22",         # forestgreen for comments / success
    foreground="#000000",
    background="#ffffff",
    surface="#f0f0f0",
    panel="#d0d0d0",
    dark=False,
)

# Vim default — Bram Moolenaar's out-of-the-box colors for dark terminals.
VIM_DEFAULT = Theme(
    name="vim-default",
    primary="#87ceeb",         # vim "Identifier" light-blue
    secondary="#ffff00",        # vim "Statement" yellow
    accent="#ff00ff",           # vim "PreProc" magenta
    warning="#ff8700",
    error="#ff6060",            # vim "Error"
    success="#60ff60",          # vim "String" green (lightgreen on dark)
    foreground="#eeeeee",
    background="#000000",
    surface="#1c1c1c",
    panel="#303030",
    dark=True,
)

# Sublime Text default (Monokai-derived).
SUBLIME_DEFAULT = Theme(
    name="sublime-default",
    primary="#66d9ef",          # sublime function blue
    secondary="#a6e22e",         # sublime class green
    accent="#f92672",            # sublime keyword pink
    warning="#fd971f",           # sublime number orange
    error="#f92672",
    success="#a6e22e",
    foreground="#f8f8f2",
    background="#272822",        # sublime classic background
    surface="#3e3d32",
    panel="#49483e",
    dark=True,
)

# VS Code Light — the out-of-the-box light theme.
VSCODE_LIGHT = Theme(
    name="vscode-light",
    primary="#0070c1",
    secondary="#795e26",         # function name brown
    accent="#af00db",            # keyword purple
    warning="#bf8803",
    error="#a31515",             # string-red
    success="#008000",
    foreground="#000000",
    background="#ffffff",
    surface="#f3f3f3",
    panel="#e7e7e7",
    dark=False,
)

# GitHub Light — the GitHub.com source-view palette.
GITHUB_LIGHT = Theme(
    name="github-light",
    primary="#0550ae",
    secondary="#6f42c1",
    accent="#cf222e",
    warning="#9a6700",
    error="#cf222e",
    success="#1a7f37",
    foreground="#1f2328",
    background="#ffffff",
    surface="#f6f8fa",
    panel="#d0d7de",
    dark=False,
)

# GitHub Dark (aka "Dark Dimmed" classic).
GITHUB_DARK = Theme(
    name="github-dark",
    primary="#58a6ff",
    secondary="#d2a8ff",
    accent="#ff7b72",
    warning="#d29922",
    error="#f85149",
    success="#3fb950",
    foreground="#c9d1d9",
    background="#0d1117",
    surface="#161b22",
    panel="#30363d",
    dark=True,
)

# Ayu Dark — minimalist dark amber accents, a VSCode community favorite.
AYU_DARK = Theme(
    name="ayu-dark",
    primary="#ffb454",          # ayu orange
    secondary="#59c2ff",         # ayu blue
    accent="#d2a6ff",            # ayu purple
    warning="#ff8f40",
    error="#f07178",
    success="#aad94c",
    foreground="#bfbdb6",
    background="#0b0e14",
    surface="#11151c",
    panel="#1c2029",
    dark=True,
)

# Night Owl — Sarah Drasner's late-night coding palette, 1M+ installs.
NIGHT_OWL = Theme(
    name="night-owl",
    primary="#82aaff",
    secondary="#c792ea",
    accent="#ffcb8b",
    warning="#ffeb95",
    error="#ef5350",
    success="#addb67",
    foreground="#d6deeb",
    background="#011627",
    surface="#0b2942",
    panel="#1d3b53",
    dark=True,
)


# ---------------------------------------------------------------------------
# Catppuccin — the four official flavors
# ---------------------------------------------------------------------------

CATPPUCCIN_LATTE = Theme(
    name="catppuccin-latte",
    primary="#1e66f5",      # Blue
    secondary="#7287fd",    # Lavender
    accent="#ea76cb",       # Pink
    warning="#df8e1d",      # Yellow
    error="#d20f39",        # Red
    success="#40a02b",      # Green
    foreground="#4c4f69",   # Text
    background="#eff1f5",   # Base
    surface="#e6e9ef",      # Mantle
    panel="#ccd0da",        # Surface 0
    dark=False,
)

CATPPUCCIN_FRAPPE = Theme(
    name="catppuccin-frappe",
    primary="#8caaee",
    secondary="#babbf1",
    accent="#f4b8e4",
    warning="#e5c890",
    error="#e78284",
    success="#a6d189",
    foreground="#c6d0f5",
    background="#303446",
    surface="#292c3c",
    panel="#414559",
    dark=True,
)

CATPPUCCIN_MACCHIATO = Theme(
    name="catppuccin-macchiato",
    primary="#8aadf4",
    secondary="#b7bdf8",
    accent="#f5bde6",
    warning="#eed49f",
    error="#ed8796",
    success="#a6da95",
    foreground="#cad3f5",
    background="#24273a",
    surface="#1e2030",
    panel="#363a4f",
    dark=True,
)

CATPPUCCIN_MOCHA = Theme(
    name="catppuccin-mocha",
    primary="#89b4fa",
    secondary="#b4befe",
    accent="#f5c2e7",
    warning="#f9e2af",
    error="#f38ba8",
    success="#a6e3a1",
    foreground="#cdd6f4",
    background="#1e1e2e",
    surface="#181825",
    panel="#313244",
    dark=True,
)


# ---------------------------------------------------------------------------
# Dracula
# ---------------------------------------------------------------------------

DRACULA = Theme(
    name="dracula",
    primary="#bd93f9",      # Purple
    secondary="#ff79c6",    # Pink
    accent="#8be9fd",       # Cyan
    warning="#ffb86c",      # Orange
    error="#ff5555",        # Red
    success="#50fa7b",      # Green
    foreground="#f8f8f2",   # Foreground
    background="#282a36",   # Background
    surface="#44475a",      # Current line
    panel="#6272a4",        # Comment
    dark=True,
)


# ---------------------------------------------------------------------------
# Everforest Dark — soft on the eyes, cozy greens
# ---------------------------------------------------------------------------

EVERFOREST_DARK = Theme(
    name="everforest-dark",
    primary="#a7c080",      # Green
    secondary="#83c092",    # Aqua
    accent="#d699b6",       # Purple
    warning="#dbbc7f",      # Yellow
    error="#e67e80",        # Red
    success="#a7c080",      # Green
    foreground="#d3c6aa",   # Foreground
    background="#2d353b",   # Background hard
    surface="#232a2e",      # Background dim
    panel="#475258",        # bg4
    dark=True,
)


# ---------------------------------------------------------------------------
# Gruvbox (dark + light)
# ---------------------------------------------------------------------------

GRUVBOX_DARK = Theme(
    name="gruvbox-dark",
    primary="#83a598",      # Blue
    secondary="#8ec07c",    # Aqua
    accent="#d3869b",       # Purple
    warning="#fabd2f",      # Yellow
    error="#fb4934",        # Red
    success="#b8bb26",      # Green
    foreground="#ebdbb2",   # fg
    background="#282828",   # bg
    surface="#3c3836",      # bg1
    panel="#504945",        # bg2
    dark=True,
)

GRUVBOX_LIGHT = Theme(
    name="gruvbox-light",
    primary="#076678",
    secondary="#427b58",
    accent="#8f3f71",
    warning="#b57614",
    error="#9d0006",
    success="#79740e",
    foreground="#3c3836",
    background="#fbf1c7",
    surface="#ebdbb2",
    panel="#d5c4a1",
    dark=False,
)


# ---------------------------------------------------------------------------
# Kanagawa — muted Japanese watercolor
# ---------------------------------------------------------------------------

KANAGAWA = Theme(
    name="kanagawa",
    primary="#7e9cd8",      # crystalBlue
    secondary="#a3d4d5",    # waveAqua1
    accent="#957fb8",       # oniViolet
    warning="#ff9e3b",      # roninYellow
    error="#e82424",        # samuraiRed
    success="#76946a",      # autumnGreen
    foreground="#dcd7ba",   # fujiWhite
    background="#1f1f28",   # sumiInk1
    surface="#2a2a37",      # sumiInk3
    panel="#363646",        # sumiInk4
    dark=True,
)


# ---------------------------------------------------------------------------
# Monokai Pro
# ---------------------------------------------------------------------------

MONOKAI_PRO = Theme(
    name="monokai-pro",
    primary="#78dce8",      # Blue
    secondary="#a9dc76",    # Green
    accent="#ff6188",       # Red/Pink
    warning="#fc9867",      # Orange
    error="#ff6188",        # Red
    success="#a9dc76",      # Green
    foreground="#fcfcfa",
    background="#2d2a2e",
    surface="#403e41",
    panel="#5b595c",
    dark=True,
)


# ---------------------------------------------------------------------------
# Nord — nordic cold blues
# ---------------------------------------------------------------------------

NORD = Theme(
    name="nord",
    primary="#88c0d0",      # nord8 — frost
    secondary="#81a1c1",    # nord9
    accent="#b48ead",       # nord15 — aurora purple
    warning="#ebcb8b",      # nord13 — aurora yellow
    error="#bf616a",        # nord11 — aurora red
    success="#a3be8c",      # nord14 — aurora green
    foreground="#eceff4",   # nord6 — snow storm
    background="#2e3440",   # nord0 — polar night
    surface="#3b4252",      # nord1
    panel="#434c5e",        # nord2
    dark=True,
)


# ---------------------------------------------------------------------------
# One Dark Pro
# ---------------------------------------------------------------------------

ONE_DARK = Theme(
    name="one-dark",
    primary="#61afef",      # Blue
    secondary="#56b6c2",    # Cyan
    accent="#c678dd",       # Purple
    warning="#e5c07b",      # Yellow
    error="#e06c75",        # Red
    success="#98c379",      # Green
    foreground="#abb2bf",
    background="#282c34",
    surface="#21252b",
    panel="#3e4451",
    dark=True,
)


# ---------------------------------------------------------------------------
# Rose Pine / Rose Pine Dawn
# ---------------------------------------------------------------------------

ROSE_PINE = Theme(
    name="rose-pine",
    primary="#c4a7e7",      # Iris
    secondary="#9ccfd8",    # Foam
    accent="#ebbcba",       # Rose
    warning="#f6c177",      # Gold
    error="#eb6f92",        # Love
    success="#31748f",      # Pine
    foreground="#e0def4",   # Text
    background="#191724",   # Base
    surface="#1f1d2e",      # Surface
    panel="#26233a",        # Overlay
    dark=True,
)

ROSE_PINE_DAWN = Theme(
    name="rose-pine-dawn",
    primary="#907aa9",      # Iris
    secondary="#56949f",    # Foam
    accent="#d7827e",       # Rose
    warning="#ea9d34",      # Gold
    error="#b4637a",        # Love
    success="#286983",      # Pine
    foreground="#575279",   # Text
    background="#faf4ed",   # Base
    surface="#fffaf3",      # Surface
    panel="#f2e9e1",        # Overlay
    dark=False,
)


# ---------------------------------------------------------------------------
# Solarized (dark + light)
# ---------------------------------------------------------------------------

SOLARIZED_DARK = Theme(
    name="solarized-dark",
    primary="#268bd2",      # blue
    secondary="#2aa198",    # cyan
    accent="#d33682",       # magenta
    warning="#b58900",      # yellow
    error="#dc322f",        # red
    success="#859900",      # green
    foreground="#839496",   # base0
    background="#002b36",   # base03
    surface="#073642",      # base02
    panel="#586e75",        # base01
    dark=True,
)

SOLARIZED_LIGHT = Theme(
    name="solarized-light",
    primary="#268bd2",
    secondary="#2aa198",
    accent="#d33682",
    warning="#b58900",
    error="#dc322f",
    success="#859900",
    foreground="#657b83",   # base00
    background="#fdf6e3",   # base3
    surface="#eee8d5",      # base2
    panel="#93a1a1",        # base1
    dark=False,
)


# ---------------------------------------------------------------------------
# Tokyo Night / Storm
# ---------------------------------------------------------------------------

TOKYO_NIGHT = Theme(
    name="tokyo-night",
    primary="#7aa2f7",      # Blue
    secondary="#7dcfff",    # Cyan-blue
    accent="#bb9af7",       # Purple
    warning="#e0af68",      # Yellow
    error="#f7768e",        # Red
    success="#9ece6a",      # Green
    foreground="#c0caf5",
    background="#1a1b26",
    surface="#16161e",
    panel="#292e42",
    dark=True,
)

TOKYO_NIGHT_STORM = Theme(
    name="tokyo-night-storm",
    primary="#7aa2f7",
    secondary="#7dcfff",
    accent="#bb9af7",
    warning="#e0af68",
    error="#f7768e",
    success="#9ece6a",
    foreground="#c0caf5",
    background="#24283b",   # slightly lighter than classic
    surface="#1f2335",
    panel="#343c5b",
    dark=True,
)


# ---------------------------------------------------------------------------
# Nerd / retro / fun
# ---------------------------------------------------------------------------

CYBERPUNK_2077 = Theme(
    name="cyberpunk-2077",
    primary="#fcee0a",      # radioactive yellow
    secondary="#00e5ff",    # electric cyan
    accent="#ff006e",       # neon pink
    warning="#ff8f00",      # glitch orange
    error="#ff0055",        # blood red
    success="#00ff9f",      # green-neon
    foreground="#e6e6e6",
    background="#0a0d11",   # pitch black w/ blue
    surface="#1a1d25",
    panel="#2a2f40",
    dark=True,
)

FALLOUT_TERMINAL = Theme(
    name="fallout-terminal",
    primary="#4dff4d",      # Pip-Boy green
    secondary="#ffb000",    # amber
    accent="#ffd700",
    warning="#ff8c00",
    error="#ff3030",
    success="#4dff4d",
    foreground="#4dff4d",
    background="#001a00",
    surface="#002600",
    panel="#003300",
    dark=True,
)

MATRIX = Theme(
    name="matrix",
    primary="#00ff41",      # iconic green
    secondary="#00cc33",
    accent="#39ff14",
    warning="#ffff00",
    error="#ff0000",
    success="#00ff41",
    foreground="#00ff41",
    background="#000000",
    surface="#0a140a",
    panel="#142814",
    dark=True,
)

SYNTHWAVE_84 = Theme(
    name="synthwave-84",
    primary="#ff7edb",      # magenta pink
    secondary="#36f9f6",    # cyan
    accent="#fede5d",       # sun yellow
    warning="#ff8b39",
    error="#fe4450",
    success="#72f1b8",
    foreground="#f4eee4",
    background="#241b2f",   # deep indigo horizon
    surface="#2a2139",
    panel="#34294f",
    dark=True,
)

# "Cyberpunk Dots" — neon cyan + magenta on a deep-purple background.
# Previously duplicated across lynx-finance/health/tech/comm; promoted
# to core in v5.5.1 so every Suite program can use it.
CYBRDOTS = Theme(
    name="cybrdots",
    primary="#00f0ff",       # electric cyan
    secondary="#ff2bd6",     # hot magenta / neon pink
    accent="#c6ff00",        # lime green
    warning="#ffb000",       # amber
    error="#ff2d5a",         # neon red
    success="#39ff14",       # neon green
    foreground="#e0f7ff",    # pale cyan text
    background="#0a0014",    # deep purple-black
    surface="#140028",       # midnight violet
    panel="#1f0a3c",         # dark indigo panel
    dark=True,
)


# ---------------------------------------------------------------------------
# Registry + helper
# ---------------------------------------------------------------------------

SUITE_THEMES: List[Theme] = [
    # Lynx house (financial-first — vivid green/red, neutral chrome)
    LYNX_THEME,
    LYNX_THEME_LIGHT,
    TERMINAL_DEFAULT,
    # Editor / terminal classics
    BLACK_AND_WHITE,
    GITHUB_DARK,
    GITHUB_LIGHT,
    VSCODE_LIGHT,
    SUBLIME_DEFAULT,
    AYU_DARK,
    NIGHT_OWL,
    VIM_DEFAULT,
    EMACS_CLASSIC,
    # Catppuccin
    CATPPUCCIN_MOCHA,
    CATPPUCCIN_MACCHIATO,
    CATPPUCCIN_FRAPPE,
    CATPPUCCIN_LATTE,
    # Popular dark
    DRACULA,
    TOKYO_NIGHT,
    TOKYO_NIGHT_STORM,
    NORD,
    ONE_DARK,
    GRUVBOX_DARK,
    MONOKAI_PRO,
    ROSE_PINE,
    KANAGAWA,
    EVERFOREST_DARK,
    SOLARIZED_DARK,
    # Light
    ROSE_PINE_DAWN,
    GRUVBOX_LIGHT,
    SOLARIZED_LIGHT,
    # Nerd / retro
    MATRIX,
    CYBERPUNK_2077,
    CYBRDOTS,
    SYNTHWAVE_84,
    FALLOUT_TERMINAL,
]

SUITE_THEME_NAMES: List[str] = [t.name for t in SUITE_THEMES]


def register_suite_themes(app: "App") -> None:
    """Install every Suite theme on *app*.

    Safe to call more than once — Textual silently overwrites an
    existing registration with the same name. After this call, any of
    the names in :data:`SUITE_THEME_NAMES` can be activated via
    ``app.theme = "catppuccin-mocha"`` (or the app's own theme-cycling
    action).
    """
    for theme in SUITE_THEMES:
        app.register_theme(theme)
