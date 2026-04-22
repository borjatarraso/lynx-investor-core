"""Unit tests for :mod:`lynx_investor_core.pager`."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from lynx_investor_core import pager


class TestTerminalGeometry:
    def test_height_returns_positive_int(self) -> None:
        assert pager.terminal_height() > 0

    def test_width_returns_positive_int(self) -> None:
        assert pager.terminal_width() > 0

    def test_height_honors_default_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _raise(*_args, **_kw) -> None:
            raise OSError("no tty")
        monkeypatch.setattr(pager.os, "get_terminal_size", _raise)
        assert pager.terminal_height(default=42) == 42

    def test_width_honors_default_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _raise(*_args, **_kw) -> None:
            raise OSError("no tty")
        monkeypatch.setattr(pager.os, "get_terminal_size", _raise)
        assert pager.terminal_width(default=120) == 120


class TestShouldPaginate:
    def test_short_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pager, "terminal_height", lambda default=24: 30)
        assert not pager.should_paginate(5)

    def test_long_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pager, "terminal_height", lambda default=24: 30)
        assert pager.should_paginate(100)

    def test_boundary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pager, "terminal_height", lambda default=24: 30)
        # Add the default +2 margin
        assert pager.should_paginate(28)
        assert not pager.should_paginate(27)


class TestConsolePager:
    def test_no_op_when_not_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        console = MagicMock()
        console.is_terminal = False
        console.pager = MagicMock()
        with pager.console_pager(console) as c:
            c.print("hello")
        console.pager.assert_not_called()

    def test_invokes_pager_when_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        console = MagicMock()
        console.is_terminal = True
        pager_cm = MagicMock()
        pager_cm.__enter__ = MagicMock(return_value=None)
        pager_cm.__exit__ = MagicMock(return_value=False)
        console.pager = MagicMock(return_value=pager_cm)
        monkeypatch.setattr(pager.sys.stdout, "isatty", lambda: True)
        with pager.console_pager(console) as _c:
            pass
        console.pager.assert_called_once()


class TestPagedPrint:
    def test_prints_without_pager_for_short(self, monkeypatch: pytest.MonkeyPatch) -> None:
        console = MagicMock()
        console.render_lines = MagicMock(return_value=[[], []])  # 2 lines
        monkeypatch.setattr(pager, "should_paginate", lambda n, **kw: False)
        pager.paged_print(console, "hi")
        console.print.assert_called_once_with("hi")

    def test_uses_pager_for_long(self, monkeypatch: pytest.MonkeyPatch) -> None:
        console = MagicMock()
        console.is_terminal = True
        console.render_lines = MagicMock(return_value=[[]] * 1000)
        pager_cm = MagicMock()
        pager_cm.__enter__ = MagicMock(return_value=None)
        pager_cm.__exit__ = MagicMock(return_value=False)
        console.pager = MagicMock(return_value=pager_cm)
        monkeypatch.setattr(pager.sys.stdout, "isatty", lambda: True)
        pager.paged_print(console, "lots of text", force=True)
        console.pager.assert_called_once()


class TestTuiPagingBindings:
    def test_returns_four_bindings(self) -> None:
        pytest.importorskip("textual")
        bindings = pager.tui_paging_bindings()
        assert len(bindings) == 4
        keys = [b.key for b in bindings]
        assert "pageup" in keys
        assert "pagedown" in keys
        assert "ctrl+home" in keys
        assert "ctrl+end" in keys

    def test_action_names(self) -> None:
        pytest.importorskip("textual")
        bindings = pager.tui_paging_bindings()
        actions = {b.key: b.action for b in bindings}
        assert actions["pageup"] == "page_up"
        assert actions["pagedown"] == "page_down"
        assert actions["ctrl+home"] == "page_home"
        assert actions["ctrl+end"] == "page_end"


class TestPagingAppMixin:
    def _app(self, focused=None, main=None):
        app = SimpleNamespace()
        app.focused = focused
        app._report_view = main
        app.screen = None
        app._paging_main_view_attr = "_report_view"
        # Attach mixin methods.
        app._paging_target = lambda: pager.PagingAppMixin._paging_target(app)
        app.action_page_up = lambda: pager.PagingAppMixin.action_page_up(app)
        app.action_page_down = lambda: pager.PagingAppMixin.action_page_down(app)
        return app

    def test_focus_wins_over_main(self) -> None:
        focused = MagicMock(spec=["action_page_up", "action_page_down"])
        main = MagicMock(spec=["action_page_up", "action_page_down"])
        app = self._app(focused=focused, main=main)
        app.action_page_up()
        focused.action_page_up.assert_called_once()
        main.action_page_up.assert_not_called()

    def test_falls_back_to_main(self) -> None:
        main = MagicMock(spec=["action_page_up", "action_page_down"])
        app = self._app(focused=None, main=main)
        app.action_page_up()
        main.action_page_up.assert_called_once()

    def test_no_target_is_noop(self) -> None:
        app = self._app(focused=None, main=None)
        app.action_page_up()  # must not raise


class TestBindTkPaging:
    def test_bindings_installed(self) -> None:
        root = MagicMock()
        scroll = MagicMock()
        pager.bind_tk_paging(root, scroll)
        bound_keys = [call.args[0] for call in root.bind_all.call_args_list]
        assert "<Prior>" in bound_keys
        assert "<Next>" in bound_keys
        assert "<Control-Home>" in bound_keys
        assert "<Control-End>" in bound_keys

    def test_page_up_scrolls(self) -> None:
        root = MagicMock()
        scroll = MagicMock()
        pager.bind_tk_paging(root, scroll)
        # The first bind_all call installed PageUp; invoke its handler.
        for call in root.bind_all.call_args_list:
            if call.args[0] == "<Prior>":
                handler = call.args[1]
                handler()
                scroll.yview_scroll.assert_called_with(-1, "pages")
                break
        else:  # pragma: no cover
            pytest.fail("PageUp binding not installed")

    def test_page_down_scrolls(self) -> None:
        root = MagicMock()
        scroll = MagicMock()
        pager.bind_tk_paging(root, scroll)
        for call in root.bind_all.call_args_list:
            if call.args[0] == "<Next>":
                handler = call.args[1]
                handler()
                scroll.yview_scroll.assert_called_with(1, "pages")
                break
        else:  # pragma: no cover
            pytest.fail("PageDown binding not installed")
