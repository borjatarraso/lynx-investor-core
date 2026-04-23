"""Plugin protocol for the Lince Investor Suite.

Every sector agent (and the core apps: fundamental, compare, portfolio)
publishes a small descriptor via a Python ``entry_points`` group so the
dashboard can discover them without hard-coded imports.

Entry-point group
-----------------

Agents register themselves under the group ``lynx_investor_suite.agents``.
Each entry point points at a module-level ``register()`` function that
returns a :class:`SectorAgent`::

    [project.entry-points."lynx_investor_suite.agents"]
    mining = "lynx_mining.plugin:register"

Discovery is lazy: importing :mod:`lynx_investor_core` is cheap; the
agent packages are only imported when :func:`discover` (or
:func:`launch`) is called.

Dev environment note
--------------------

Entry points are registered at install time. In a dev checkout where
``pip install -e .`` has not been re-run after adding a plugin entry,
``discover()`` may return an empty list. Re-run the editable install
for every affected package to make the new plugins visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

__all__ = [
    "SectorAgent",
    "ENTRY_POINT_GROUP",
    "discover",
    "get_by_name",
    "launch",
]


ENTRY_POINT_GROUP = "lynx_investor_suite.agents"


@dataclass(frozen=True)
class SectorAgent:
    """Descriptor returned by an agent entry point.

    Third-party plugins build one of these in their ``register()``
    function. The dashboard uses the values to render launcher tables
    and resolve the CLI entry point.
    """

    name: str                       # e.g. "lynx-investor-basic-materials"
    short_name: str                 # e.g. "mining"
    sector: str                     # e.g. "Basic Materials"
    tagline: str                    # e.g. "Junior Mining & Basic Materials"
    prog_name: str                  # CLI binary name: "lynx-mining"
    version: str                    # package version
    package_module: str             # "lynx_mining"
    entry_point_module: str         # "lynx_mining.__main__"
    entry_point_function: str       # "main"
    icon: str = ""                  # single glyph or emoji


def _iter_entry_points():
    """Return the entry points registered under our group.

    Uses :mod:`importlib.metadata` lazily so importing this module is
    cheap even when plugins are not installed.
    """
    from importlib import metadata

    eps = metadata.entry_points()
    # Python 3.10+: ``entry_points()`` returns an ``EntryPoints`` object
    # supporting ``.select(group=...)``. Older 3.9-style dict fallback
    # kept for safety even though the project targets 3.10+.
    select = getattr(eps, "select", None)
    if callable(select):
        return list(select(group=ENTRY_POINT_GROUP))
    return list(eps.get(ENTRY_POINT_GROUP, []))  # pragma: no cover - 3.9 path


def discover() -> List[SectorAgent]:
    """Return every installed Suite agent via entry-points.

    Order follows the order :mod:`importlib.metadata` yields the entry
    points (installation order / distribution order). Broken plugins
    whose ``register()`` raises are skipped — discovery never crashes
    the whole dashboard because one plugin is misbehaving.

    Returns an empty list if nothing is installed; that is expected in
    a dev checkout before ``pip install -e .`` has been re-run against
    the plugin packages.
    """
    agents: List[SectorAgent] = []
    for ep in _iter_entry_points():
        try:
            register: Callable[[], SectorAgent] = ep.load()
            agent = register()
        except Exception:
            # Skip broken plugins silently — discovery must stay robust.
            continue
        if isinstance(agent, SectorAgent):
            agents.append(agent)
    return agents


def get_by_name(name: str) -> Optional[SectorAgent]:
    """Look up an agent by canonical ``name`` or ``short_name``.

    Returns ``None`` on miss. Matching is case-insensitive so the
    dashboard can accept user-typed identifiers directly.
    """
    if not name:
        return None
    needle = name.strip().lower()
    for agent in discover():
        if agent.name.lower() == needle or agent.short_name.lower() == needle:
            return agent
    return None


def launch(agent: SectorAgent, argv: List[str]) -> int:
    """Import the agent's entry point and invoke ``main(argv)``.

    The return value is the int exit code produced by the plugin's
    ``main`` function. If ``main`` returns ``None`` we treat that as a
    clean exit (``0``) — matching the convention most agents already
    use.

    Raises
    ------
    ModuleNotFoundError
        If the agent's ``entry_point_module`` cannot be imported.
    AttributeError
        If the module imports but does not expose
        ``entry_point_function``.
    """
    from importlib import import_module

    try:
        module = import_module(agent.entry_point_module)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"Plugin '{agent.name}' declares entry-point module "
            f"'{agent.entry_point_module}' but it is not importable: {exc}"
        ) from exc

    try:
        func: Callable[[List[str]], Optional[int]] = getattr(
            module, agent.entry_point_function
        )
    except AttributeError as exc:
        raise AttributeError(
            f"Plugin '{agent.name}' declares entry-point function "
            f"'{agent.entry_point_function}' but it is missing from "
            f"module '{agent.entry_point_module}'."
        ) from exc

    result = func(argv)
    if result is None:
        return 0
    return int(result)
