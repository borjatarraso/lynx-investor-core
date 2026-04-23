"""Shared easter-egg visuals.

Agent-specific strings (label, sub-label, fortune quotes) are injected via
``AgentEasterEgg`` — core keeps the generic ASCII art and animations.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field


GENERIC_FORTUNES: tuple[str, ...] = (
    '"Price is what you pay. Value is what you get." \u2014 Warren Buffett',
    '"The stock market is filled with individuals who know the price of everything, '
    'but the value of nothing." \u2014 Philip Fisher',
    '"Be fearful when others are greedy and greedy when others are fearful." \u2014 Warren Buffett',
    '"In the short run, the market is a voting machine; in the long run, it is a weighing machine." '
    '\u2014 Benjamin Graham',
    '"Risk comes from not knowing what you are doing." \u2014 Warren Buffett',
    '"The four most dangerous words in investing are: This time it is different." '
    '\u2014 Sir John Templeton',
    '"Never invest in a business you cannot understand." \u2014 Warren Buffett',
    '"Time in the market beats timing the market." \u2014 Kenneth Fisher',
    '"The best time to buy is when there is blood in the streets." \u2014 Baron Rothschild',
)


@dataclass(frozen=True)
class AgentEasterEgg:
    """Agent-provided strings used by the shared easter-egg visuals."""
    label: str        # shown as the lynx-ASCII sub-label, e.g. "Basic Materials Analysis"
    sublabel: str     # shown under the pickaxe, e.g. "Junior Mining Research"
    banner_prog: str  # appears in the tk fireworks banner, e.g. "lynx-mining"
    extra_fortunes: tuple[str, ...] = field(default_factory=tuple)


ROCKET_ASCII = r"""
[bold yellow]
        /\
       /  \
      | {} |
      | {} |
     /| /\ |\
    / |/  \| \
   |  / /\ \  |
   |_/ /  \ \_|
    |_/    \_|
     ||    ||
     ||    ||
    /||\  /||\
   /_||_\/_||_\
[bold red]   \  /  \  /
    \/    \/
   ~ ~  ~ ~ ~
    ~ ~~ ~ ~
[/bold red][/bold yellow]
"""

WOLF_ASCII = r"""
[bold green]
        __
       / _)
 .-^^^-/ /
__/       /         [bold white]The Wolf of Wall Street[/bold white]
<__.|_|-|_|         [dim]"Buy low, sell high."[/dim]
[/bold green]
"""

BULL_ASCII = r"""
[bold yellow]
         (__)
         (oo)
   /------\/
  / |    ||         [bold white]B U L L   R U N[/bold white]
 *  /\---/\         [dim]To the moon![/dim]
    ~~   ~~
[/bold yellow]
"""


def _lynx_ascii(label: str) -> str:
    return (
        "\n[bold green]       /\\               /\\\n"
        "      /  \\  /-------\\  /  \\\n"
        "     / .  \\/         \\/  . \\\n"
        "    |  .  /  [/][bold yellow]o[/][bold green]     "
        "[/][bold yellow]o[/][bold green]  \\  .  |\n"
        "    |  . |     v     |  .  |\n"
        "     \\./  --\\ _ /--  \\. /      [/][bold white]L Y N X[/]\n"
        f"[bold green]      | |  --/ V \\--   |  |      [/][dim]{label}[/]\n"
        "[bold green]       \\ \\    ___    / /\n"
        "        \\ \\---------/ /\n"
        "         \\___________/[/]\n"
    )


def _pickaxe_ascii(sublabel: str) -> str:
    return (
        r"""
[bold yellow]
      ___T_
     | o o |
     |__-__|
     /| [] |\        [bold white]D I G   D E E P[/bold white]
""" + f"   (d  b--b  b)      [dim]{sublabel}[/dim]\n" +
        r"""     |__|__|
[/bold yellow]
"""
    )


MATRIX_CHARS = "01"
MATRIX_KANJI = (
    "\uff66\uff67\uff68\uff69\uff6a\uff6b\uff6c\uff6d\uff6e\uff6f"
    "\uff70\uff71\uff72\uff73\uff74\uff75\uff76\uff77\uff78\uff79"
)


def rich_matrix(console, duration: float = 3.0) -> None:
    from rich.live import Live
    from rich.text import Text
    width = min(console.width, 120)
    cols = width
    drops = [random.randint(-20, 0) for _ in range(cols)]
    start = time.monotonic()
    with Live(console=console, refresh_per_second=15, transient=True) as live:
        while time.monotonic() - start < duration:
            lines = []
            for row in range(24):
                line = Text()
                for col in range(cols):
                    if drops[col] == row:
                        ch = random.choice(MATRIX_KANJI)
                        line.append(ch, style="bold white on #003300")
                    elif 0 < drops[col] - row < 6:
                        ch = random.choice(MATRIX_KANJI + MATRIX_CHARS)
                        intensity = max(0, 255 - (drops[col] - row) * 40)
                        line.append(ch, style=f"#{0:02x}{intensity:02x}{0:02x}")
                    else:
                        line.append(" ")
                lines.append(line)
            live.update(Text("\n").join(lines))
            for i in range(cols):
                if drops[i] > 24 + random.randint(0, 20):
                    drops[i] = random.randint(-10, 0)
                drops[i] += 1
            time.sleep(0.07)


def rich_fortune(console, egg: AgentEasterEgg) -> None:
    from rich.panel import Panel
    quotes = list(GENERIC_FORTUNES) + list(egg.extra_fortunes)
    console.print()
    console.print(Panel(
        f"[bold italic]{random.choice(quotes)}[/]",
        title="[bold yellow]\u2728 Fortune Cookie \u2728[/]",
        border_style="yellow", padding=(1, 3),
    ))
    console.print()


def rich_rocket(console) -> None:
    from rich.panel import Panel
    console.print(Panel(ROCKET_ASCII,
                        title="[bold red]\U0001f680 TO THE MOON \U0001f680[/]",
                        border_style="bold red"))


def rich_lynx(console, egg: AgentEasterEgg, *, secondary_art: str | None = None) -> None:
    from rich.panel import Panel
    if secondary_art is None:
        secondary_art = _pickaxe_ascii(egg.sublabel)
    arts = [_lynx_ascii(egg.label), WOLF_ASCII, BULL_ASCII, secondary_art]
    console.print(Panel(random.choice(arts), border_style="bold cyan"))


def tk_fireworks(root, egg: AgentEasterEgg) -> None:
    import tkinter as tk
    BANNER_COLORS = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff",
                     "#ff79c6", "#bd93f9", "#50fa7b", "#f1fa8c"]
    GLYPHS = "\u2605\u2726\u2728\u2736\u272A\u2756\u2734\u2733\u25C6"
    overlay = tk.Frame(root, bg="#0a0a1a")
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
    overlay.lift()
    canvas = tk.Canvas(overlay, bg="#0a0a1a", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    particles = []
    step = [0]

    def _spawn_burst():
        cx = random.randint(100, max(root.winfo_width() - 100, 200))
        cy = random.randint(80, max(root.winfo_height() - 80, 200))
        color = random.choice(BANNER_COLORS)
        for _ in range(18):
            dx, dy = random.uniform(-6, 6), random.uniform(-6, 6)
            tid = canvas.create_text(cx, cy, text=random.choice(GLYPHS), fill=color,
                                     font=("Noto Sans", random.randint(14, 28), "bold"))
            particles.append((tid, dx, dy, 0))

    def _animate():
        nonlocal particles
        step[0] += 1
        if step[0] > 80:
            try:
                overlay.destroy()
            except tk.TclError:
                pass
            return
        if step[0] % 8 == 1 and step[0] < 50:
            _spawn_burst()
        alive = []
        for tid, dx, dy, age in particles:
            try:
                canvas.move(tid, dx, dy * 0.8 + age * 0.15)
                if age > 10:
                    canvas.itemconfig(tid, fill="#333355")
                if age > 18:
                    canvas.delete(tid)
                    continue
            except tk.TclError:
                continue
            alive.append((tid, dx * 0.96, dy, age + 1))
        particles = alive
        if step[0] == 1:
            messages = [
                f"\u2605  {egg.banner_prog}  \u2605",
                egg.label,
                "\U0001f680 To the Moon! \U0001f680",
            ]
            for i, msg in enumerate(messages):
                canvas.create_text(root.winfo_width() // 2, 40 + i * 36, text=msg,
                                   fill=BANNER_COLORS[i % len(BANNER_COLORS)],
                                   font=("Noto Sans", 20 - i * 3, "bold"), tags="banner_text")
        try:
            root.after(40, _animate)
        except tk.TclError:
            pass

    _animate()


def tk_rainbow_title(root, egg: AgentEasterEgg, count: int = 20) -> None:
    import tkinter as tk
    try:
        original_title = root.title()
    except tk.TclError:
        return
    colors = ["\U0001f534", "\U0001f7e0", "\U0001f7e1",
              "\U0001f7e2", "\U0001f535", "\U0001f7e3"]
    sparkles = ["\u2728", "\U0001f31f", "\u2b50", "\U0001f4ab"]

    def _step(remaining, idx):
        if remaining <= 0:
            try:
                root.title(original_title)
            except tk.TclError:
                pass
            return
        try:
            root.title(
                f"{random.choice(sparkles)} {colors[idx % len(colors)]} "
                f"{egg.banner_prog} {colors[idx % len(colors)]} {random.choice(sparkles)}"
            )
        except tk.TclError:
            return
        root.after(150, _step, remaining - 1, idx + 1)

    _step(count, 0)
