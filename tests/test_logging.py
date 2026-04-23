"""Tests for :mod:`lynx_investor_core.logging`."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from lynx_investor_core import logging as lg


@pytest.fixture(autouse=True)
def isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Every test gets a fresh log dir and empty logger cache."""
    monkeypatch.setenv("LYNX_LOG_DIR", str(tmp_path))
    monkeypatch.delenv("LYNX_LOG_LEVEL", raising=False)
    monkeypatch.delenv("LYNX_LOG_STDERR", raising=False)
    lg._LOGGERS.clear()
    yield


class TestJSONFormatter:
    def _format(self, rec_attrs, **extras) -> dict:
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="x.py", lineno=1,
            msg="hello %s", args=("world",), exc_info=None,
        )
        for k, v in rec_attrs.items():
            setattr(record, k, v)
        for k, v in extras.items():
            setattr(record, k, v)
        out = lg.JSONFormatter().format(record)
        return json.loads(out)

    def test_includes_standard_fields(self) -> None:
        obj = self._format({})
        assert obj["level"] == "INFO"
        assert obj["logger"] == "test"
        assert obj["msg"] == "hello world"

    def test_extra_fields_propagate(self) -> None:
        obj = self._format({}, ticker="AAPL", shares=10)
        assert obj["ticker"] == "AAPL"
        assert obj["shares"] == 10

    def test_non_json_extra_is_repr(self) -> None:
        class NotJson:
            def __repr__(self) -> str:
                return "<NotJson>"
        obj = self._format({}, weird=NotJson())
        assert obj["weird"] == "<NotJson>"


class TestGetLogger:
    def test_returns_configured_logger(self, tmp_path: Path) -> None:
        log = lg.get_logger("test-agent")
        log.info("hello world", extra={"ticker": "NEM"})
        # File should now exist with one JSON line
        path = tmp_path / "test-agent.log"
        assert path.exists()
        line = path.read_text().strip().splitlines()[-1]
        obj = json.loads(line)
        assert obj["msg"] == "hello world"
        assert obj["ticker"] == "NEM"
        assert obj["level"] == "INFO"

    def test_is_cached(self) -> None:
        a = lg.get_logger("dup")
        b = lg.get_logger("dup")
        assert a is b

    def test_respects_level_env_var(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LYNX_LOG_LEVEL", "WARNING")
        lg._LOGGERS.clear()
        log = lg.get_logger("level-test")
        assert log.level == logging.WARNING

    def test_unknown_level_falls_back_to_info(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LYNX_LOG_LEVEL", "not-a-level")
        lg._LOGGERS.clear()
        log = lg.get_logger("fallback")
        assert log.level == logging.INFO

    def test_stderr_mirror_when_env(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("LYNX_LOG_STDERR", "1")
        lg._LOGGERS.clear()
        log = lg.get_logger("stderr-test")
        # Two handlers: file + stderr
        stderr_handlers = [
            h for h in log.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(stderr_handlers) == 1

    def test_non_writable_dir_does_not_crash(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        monkeypatch.setenv("LYNX_LOG_DIR", "/definitely/not/writable/anywhere")
        lg._LOGGERS.clear()
        log = lg.get_logger("ro")
        log.info("no file handler but we don't crash")
        assert isinstance(log, logging.Logger)


class TestGetLogDir:
    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LYNX_LOG_DIR", "/tmp/somewhere")
        assert lg.get_log_dir() == Path("/tmp/somewhere")

    def test_xdg_state_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LYNX_LOG_DIR", raising=False)
        monkeypatch.setenv("XDG_STATE_HOME", "/opt/state")
        assert lg.get_log_dir() == Path("/opt/state/lynx")

    def test_default_home_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LYNX_LOG_DIR", raising=False)
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        assert lg.get_log_dir() == Path.home() / ".local" / "state" / "lynx"
