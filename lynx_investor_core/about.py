"""Shared About dialogs and metadata assembly.

Every agent has the same About layout; only the app name, tagline, and
description differ. :func:`build_about` returns a uniform dict that the CLI /
interactive / TUI / GUI renderers can consume.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lynx_investor_core import (
    LICENSE_NAME,
    LICENSE_TEXT,
    SUITE_LABEL,
    SUITE_NAME,
    SUITE_VERSION,
    __author__,
    __author_email__,
    __license__,
    __year__,
)


@dataclass(frozen=True)
class AgentMeta:
    """Static agent identity used by About / splash / CLI."""
    app_name: str           # e.g. "Lynx Basic Materials Analysis"
    short_name: str         # e.g. "Basic Materials Analysis"
    tagline: str            # e.g. "Junior Mining & Basic Materials"
    package_name: str       # e.g. "lynx_mining"
    prog_name: str          # e.g. "lynx-mining"
    version: str            # the agent's own __version__
    description: str        # multi-line About description
    scope_description: str  # e.g. "basic materials and commodities"


def build_about(meta: AgentMeta, *, logo_ascii: Optional[str] = None) -> dict:
    """Return a uniform About dict for all renderers."""
    return {
        "name": meta.app_name,
        "short_name": meta.short_name,
        "tagline": meta.tagline,
        "suite": SUITE_NAME,
        "suite_version": SUITE_VERSION,
        "suite_label": SUITE_LABEL,
        "version": meta.version,
        "author": __author__,
        "email": __author_email__,
        "year": __year__,
        "license": __license__,
        "license_name": LICENSE_NAME,
        "license_text": LICENSE_TEXT,
        "description": meta.description,
        "scope_description": meta.scope_description,
        "logo_ascii": logo_ascii or "",
    }


def render_about_cli(console, about: dict) -> None:
    """Render the About block for CLI / interactive modes."""
    from rich.panel import Panel
    logo = about.get("logo_ascii", "")
    if logo:
        console.print(Panel(f"[green]{logo}[/]", border_style="green"))
    console.print(Panel(
        f"[bold blue]{about['name']} v{about['version']}[/]\n"
        f"[dim]Part of {about['suite']} v{about['suite_version']}[/]\n"
        f"[dim]Released {about['year']}[/]\n\n"
        f"[bold]Developed by:[/] {about['author']}\n"
        f"[bold]Contact:[/]      {about['email']}\n"
        f"[bold]License:[/]      {about['license']}\n\n"
        f"[dim]{about['description']}[/]",
        title="[bold]About[/]",
        border_style="blue",
    ))
    console.print(Panel(
        about["license_text"],
        title=f"[bold]{about['license_name']}[/]",
        border_style="dim",
    ))


def render_about_compact(console, about: dict) -> None:
    """One-panel About block — used by the interactive REPL ``about`` command."""
    from rich.panel import Panel
    logo = about.get("logo_ascii", "")
    logo_block = f"[bold green]{logo}[/]\n" if logo else ""
    console.print(Panel(
        f"{logo_block}[bold blue]{about['name']} v{about['version']}[/]\n"
        f"[dim]Part of {about['suite']} v{about['suite_version']}[/]\n\n"
        f"[bold]By:[/] {about['author']}\n\n"
        f"[dim]{about['description']}[/]",
        title="[bold]About[/]",
        border_style="blue",
    ))


def about_static_text(about: dict) -> str:
    """A Rich-markup string suitable for Textual ``Static`` widgets."""
    logo = about.get("logo_ascii", "")
    logo_block = f"[bold green]{logo}[/]\n" if logo else ""
    return (
        f"{logo_block}"
        f"[bold blue]{about['name']} v{about['version']}[/]\n"
        f"[dim]Part of {about['suite']} v{about['suite_version']}[/]\n"
        f"[dim]Released {about['year']}[/]\n\n"
        f"[bold]Developed by:[/] {about['author']}\n"
        f"[bold]Contact:[/]      {about['email']}\n"
        f"[bold]License:[/]      {about['license']}\n\n"
        f"{about['description']}\n\n"
        f"[bold cyan]{about['license_name']}[/]\n"
        f"[dim]{about['license_text']}[/]"
    )
