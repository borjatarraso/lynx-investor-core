"""Tests for the shared i18n module.

Exercises the public contract of :mod:`lynx_investor_core.i18n`:

* default is :class:`gettext.NullTranslations` (identity translation)
* ``set_locale("es")`` activates the bundled Spanish catalog
* ``set_locale(None)`` reverts to the null translator
* unknown locales fall back silently (no exception)
* the ``LYNX_LOCALE`` env var is honored on import

The env-var test runs in a subprocess because the i18n module only reads
``LYNX_LOCALE`` at import time, and the test suite has already imported it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from lynx_investor_core import i18n


# The Spanish catalog ships with the suite; compile it if the pre-built .mo
# is missing so that these tests still work from a pristine checkout.
_LOCALES_DIR = Path(i18n.__file__).resolve().parent / "locales"
_ES_MO = _LOCALES_DIR / "es" / "LC_MESSAGES" / "lynx.mo"


@pytest.fixture(autouse=True)
def _reset_locale():
    """Every test starts from the null-translator baseline."""
    i18n.set_locale(None)
    yield
    i18n.set_locale(None)


def test_default_is_null():
    """With no catalog installed, ``_`` returns its argument unchanged."""
    assert i18n._("hello") == "hello"
    assert i18n.gettext("Positions") == "Positions"
    assert i18n.current_locale() is None


def test_set_locale_activates_catalog():
    """After ``set_locale("es")``, msgids present in the catalog are translated."""
    assert _ES_MO.exists(), (
        f"Compiled Spanish catalog missing at {_ES_MO}. "
        "Run `msgfmt lynx.po -o lynx.mo` in locales/es/LC_MESSAGES/."
    )
    i18n.set_locale("es")
    assert i18n.current_locale() == "es"
    # Core dashboard label — if this breaks, the demo in display.py breaks too.
    assert i18n._("Positions") == "Posiciones"
    # Short common word.
    assert i18n._("Error") == "Error"  # identical text, but it's in the catalog
    # Multi-word conclusion label.
    assert i18n._("Strong Buy") == "Compra Fuerte"
    # A full sentence (error message).
    assert i18n._("Ticker cannot be empty.") == "El símbolo no puede estar vacío."


def test_set_locale_none_reverts_to_null():
    """Passing ``None`` restores identity translation."""
    i18n.set_locale("es")
    assert i18n._("Positions") == "Posiciones"
    i18n.set_locale(None)
    assert i18n.current_locale() is None
    assert i18n._("Positions") == "Positions"


def test_unknown_locale_falls_back_silently():
    """Unknown locales must not raise — they fall back to the null translator."""
    # Should not raise, even though ``xx`` has no catalog.
    i18n.set_locale("xx-nope")
    assert i18n.current_locale() is None
    assert i18n._("Positions") == "Positions"


def test_unknown_msgid_passes_through_unchanged():
    """Strings not present in the catalog come back as the source text."""
    i18n.set_locale("es")
    assert i18n._("This string is definitely not in the catalog.") == (
        "This string is definitely not in the catalog."
    )


def test_ngettext_works_with_null_translator():
    """``ngettext`` should behave like a normal plural selector by default."""
    assert i18n.ngettext("day", "days", 1) == "day"
    assert i18n.ngettext("day", "days", 2) == "days"


def test_env_var_initialises_locale():
    """Setting ``LYNX_LOCALE=es`` before import auto-activates the catalog."""
    script = textwrap.dedent(
        """
        import os
        assert os.environ.get('LYNX_LOCALE') == 'es'
        from lynx_investor_core import i18n
        assert i18n.current_locale() == 'es', i18n.current_locale()
        assert i18n._('Positions') == 'Posiciones', i18n._('Positions')
        print('OK')
        """
    )
    env = dict(os.environ)
    env["LYNX_LOCALE"] = "es"
    # Make sure the child process imports the same source tree we're testing.
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in [str(Path(i18n.__file__).resolve().parents[2]), env.get("PYTHONPATH", "")] if p
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "OK"
