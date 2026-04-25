"""Tests for the shared in-memory translation registry."""

from __future__ import annotations

import argparse
import os

import pytest

from lynx_investor_core import translations as tr


@pytest.fixture(autouse=True)
def _isolated_lang_home(tmp_path, monkeypatch):
    """Point XDG_CONFIG_HOME at a tmpdir so persistence never leaks."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # Clear any LYNX_LANG override from the host shell.
    monkeypatch.delenv("LYNX_LANG", raising=False)
    # Reset the active language to default for isolation.
    tr.set_language(tr.DEFAULT_LANGUAGE, persist=False)
    yield


def test_supported_codes_match_tables():
    for code in tr.SUPPORTED_LANGUAGES:
        assert code in tr.TRANSLATIONS
        assert code in tr.LANG_LABELS
        assert code in tr.LANG_FULL_NAMES


def test_default_language_is_us():
    assert tr.DEFAULT_LANGUAGE == "us"
    assert tr.current_language() == "us"


def test_set_language_persists_and_lookup_translates():
    tr.set_language("es")
    assert tr.current_language() == "es"
    assert tr.t("buy") == "Compra"
    assert tr.t("sell", default="Vender") == "Vender"


def test_set_language_normalises_aliases():
    tr.set_language("English")
    assert tr.current_language() == "us"
    tr.set_language("Español")
    assert tr.current_language() == "es"
    tr.set_language("persian")
    assert tr.current_language() == "fa"


def test_set_language_falls_back_for_unknown():
    tr.set_language("klingon")
    assert tr.current_language() == "us"


def test_persistence_round_trips(tmp_path):
    # Force a known XDG_CONFIG_HOME so we can read the file ourselves.
    tr.set_language("de", persist=True)
    saved = tr.language_storage_path()
    assert saved.exists()
    assert "de" in saved.read_text()


def test_cycle_language_round_robin():
    tr.set_language("us", persist=False)
    seen = [tr.current_language()]
    for _ in tr.SUPPORTED_LANGUAGES:
        seen.append(tr.cycle_language(persist=False))
    # We should have visited every supported language at least once.
    assert set(seen) == set(tr.SUPPORTED_LANGUAGES)


def test_t_falls_back_to_us_for_missing_keys():
    tr.set_language("fa")
    # "license_text" only exists in US; t() should fall back to that.
    assert tr.t("license", default="License") == "مجوز"


def test_lookup_with_explicit_lang_does_not_change_state():
    tr.set_language("us")
    assert tr.t("buy", lang="es") == "Compra"
    assert tr.current_language() == "us"


def test_label_helpers():
    tr.set_language("fr")
    assert tr.language_code_label() == "FR"
    assert tr.language_full_name() == "Français"
    options = list(tr.supported_language_options())
    assert ("us", "English (US)") in options


# ---------------------------------------------------------------------------
# argparse helper
# ---------------------------------------------------------------------------

def test_add_language_argument_parses_codes():
    p = argparse.ArgumentParser()
    tr.add_language_argument(p)
    args = p.parse_args(["--language", "es"])
    assert args.language == "es"


def test_add_language_argument_rejects_unknown():
    p = argparse.ArgumentParser()
    tr.add_language_argument(p)
    with pytest.raises(SystemExit):
        p.parse_args(["--language", "klingon"])


def test_apply_args_switches_language():
    p = argparse.ArgumentParser()
    tr.add_language_argument(p)
    args = p.parse_args(["--language", "it"])
    tr.apply_args(args)
    assert tr.current_language() == "it"
    assert tr.t("buy") == "Acquista"
