"""Unit tests for ``lynx_investor_core.plugins``."""

from __future__ import annotations

import sys
import types
from typing import List

import pytest

from lynx_investor_core import plugins
from lynx_investor_core.plugins import (
    ENTRY_POINT_GROUP,
    SectorAgent,
    discover,
    get_by_name,
    launch,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_agent(
    *,
    name: str = "lynx-test-foo",
    short_name: str = "foo",
    sector: str = "Test Sector",
    tagline: str = "Foo tagline",
    prog_name: str = "lynx-foo",
    version: str = "1.0",
    package_module: str = "lynx_foo",
    entry_point_module: str = "lynx_foo.__main__",
    entry_point_function: str = "main",
    icon: str = "*",
) -> SectorAgent:
    return SectorAgent(
        name=name,
        short_name=short_name,
        sector=sector,
        tagline=tagline,
        prog_name=prog_name,
        version=version,
        package_module=package_module,
        entry_point_module=entry_point_module,
        entry_point_function=entry_point_function,
        icon=icon,
    )


class _FakeEntryPoint:
    """Stand-in for :class:`importlib.metadata.EntryPoint` that lets us
    control what ``.load()`` returns without touching site-packages."""

    def __init__(self, loader, name: str = "fake", group: str = ENTRY_POINT_GROUP):
        self.name = name
        self.group = group
        self._loader = loader

    def load(self):
        return self._loader


class _FakeEntryPoints:
    """Mimics the 3.10+ EntryPoints object that supports .select(group=...)."""

    def __init__(self, eps):
        self._eps = list(eps)

    def select(self, group=None):
        if group is None:
            return list(self._eps)
        return [e for e in self._eps if getattr(e, "group", None) == group]


@pytest.fixture
def patch_entry_points(monkeypatch):
    """Return a factory that replaces ``importlib.metadata.entry_points``."""

    def _patch(eps_list):
        import importlib.metadata as md

        fake = _FakeEntryPoints(eps_list)
        monkeypatch.setattr(md, "entry_points", lambda: fake)
        return fake

    return _patch


# ---------------------------------------------------------------------------
# discover()
# ---------------------------------------------------------------------------


def test_discover_returns_empty_when_nothing_installed(patch_entry_points):
    patch_entry_points([])
    assert discover() == []


def test_discover_returns_sector_agent_from_fake_entry_point(patch_entry_points):
    agent = _make_agent()
    ep = _FakeEntryPoint(lambda: agent)
    patch_entry_points([ep])

    result = discover()

    assert result == [agent]
    assert isinstance(result[0], SectorAgent)


def test_discover_collects_multiple_entry_points(patch_entry_points):
    a = _make_agent(name="lynx-a", short_name="a", package_module="lynx_a")
    b = _make_agent(name="lynx-b", short_name="b", package_module="lynx_b")
    patch_entry_points([_FakeEntryPoint(lambda: a), _FakeEntryPoint(lambda: b)])

    result = discover()

    assert [ag.short_name for ag in result] == ["a", "b"]


def test_discover_skips_broken_plugins(patch_entry_points):
    good = _make_agent()

    def _boom():
        raise RuntimeError("plugin exploded on register()")

    patch_entry_points([
        _FakeEntryPoint(_boom),
        _FakeEntryPoint(lambda: good),
    ])

    result = discover()

    # The broken plugin is silently dropped; the good one still appears.
    assert result == [good]


def test_discover_ignores_wrong_type(patch_entry_points):
    """register() that returns something other than a SectorAgent is dropped."""
    patch_entry_points([_FakeEntryPoint(lambda: {"not": "an agent"})])
    assert discover() == []


# ---------------------------------------------------------------------------
# get_by_name()
# ---------------------------------------------------------------------------


def test_get_by_name_matches_canonical_name(patch_entry_points):
    agent = _make_agent(name="lynx-investor-foo", short_name="foo")
    patch_entry_points([_FakeEntryPoint(lambda: agent)])

    assert get_by_name("lynx-investor-foo") == agent


def test_get_by_name_matches_short_name(patch_entry_points):
    agent = _make_agent(name="lynx-investor-foo", short_name="foo")
    patch_entry_points([_FakeEntryPoint(lambda: agent)])

    assert get_by_name("foo") == agent


def test_get_by_name_is_case_insensitive(patch_entry_points):
    agent = _make_agent(name="lynx-investor-foo", short_name="foo")
    patch_entry_points([_FakeEntryPoint(lambda: agent)])

    assert get_by_name("FOO") == agent
    assert get_by_name("Lynx-Investor-Foo") == agent


def test_get_by_name_returns_none_on_miss(patch_entry_points):
    agent = _make_agent(short_name="foo")
    patch_entry_points([_FakeEntryPoint(lambda: agent)])

    assert get_by_name("nonexistent") is None


def test_get_by_name_returns_none_on_empty(patch_entry_points):
    patch_entry_points([])
    assert get_by_name("") is None
    assert get_by_name("anything") is None


# ---------------------------------------------------------------------------
# launch()
# ---------------------------------------------------------------------------


def test_launch_raises_when_entry_point_module_missing():
    agent = _make_agent(entry_point_module="definitely_not_installed_xyz.__main__")
    with pytest.raises(ModuleNotFoundError) as exc:
        launch(agent, [])
    assert "definitely_not_installed_xyz" in str(exc.value)


def test_launch_raises_when_function_missing(monkeypatch):
    # Build a throwaway module in sys.modules with no "main".
    mod = types.ModuleType("plugin_test_empty_mod")
    monkeypatch.setitem(sys.modules, "plugin_test_empty_mod", mod)

    agent = _make_agent(
        entry_point_module="plugin_test_empty_mod",
        entry_point_function="main",
    )
    with pytest.raises(AttributeError) as exc:
        launch(agent, [])
    assert "main" in str(exc.value)


def test_launch_calls_entry_function_with_argv(monkeypatch):
    captured = {}

    def fake_main(argv: List[str]) -> int:
        captured["argv"] = list(argv)
        return 0

    mod = types.ModuleType("plugin_test_fake_ok")
    mod.main = fake_main  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "plugin_test_fake_ok", mod)

    agent = _make_agent(
        entry_point_module="plugin_test_fake_ok",
        entry_point_function="main",
    )

    rc = launch(agent, ["-t", "-i", "AAPL"])

    assert rc == 0
    assert captured["argv"] == ["-t", "-i", "AAPL"]


def test_launch_propagates_nonzero_exit_code(monkeypatch):
    mod = types.ModuleType("plugin_test_fake_err")
    mod.main = lambda argv: 7  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "plugin_test_fake_err", mod)

    agent = _make_agent(
        entry_point_module="plugin_test_fake_err",
        entry_point_function="main",
    )
    assert launch(agent, []) == 7


def test_launch_treats_none_return_as_zero(monkeypatch):
    mod = types.ModuleType("plugin_test_fake_none")
    mod.main = lambda argv: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "plugin_test_fake_none", mod)

    agent = _make_agent(
        entry_point_module="plugin_test_fake_none",
        entry_point_function="main",
    )
    assert launch(agent, []) == 0


# ---------------------------------------------------------------------------
# SectorAgent dataclass sanity
# ---------------------------------------------------------------------------


def test_sector_agent_is_frozen():
    agent = _make_agent()
    with pytest.raises(Exception):
        # dataclass(frozen=True) raises FrozenInstanceError (subclass of AttributeError).
        agent.name = "mutated"  # type: ignore[misc]


def test_entry_point_group_constant_is_namespaced():
    # Sanity: the group name is what our pyproject files point at.
    assert plugins.ENTRY_POINT_GROUP == "lynx_investor_suite.agents"
