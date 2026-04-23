"""Shared internationalization (i18n) plumbing for the Lince Investor Suite.

This module exposes a tiny ``gettext``-based API that every package in the
suite can import without pulling in any third-party dependency (``gettext``
ships in the Python standard library).

Typical usage::

    from lynx_investor_core.i18n import _, set_locale

    set_locale("es")
    print(_("Positions"))   # → "Posiciones" when the catalog is compiled

Catalogs live at::

    <core-package-dir>/locales/<code>/LC_MESSAGES/lynx.mo

and are compiled from the accompanying ``.po`` files with ``msgfmt``.

If the requested locale does not have a compiled catalog available, the
module falls back silently to :class:`gettext.NullTranslations` (identity
translation) so that calling code never raises.

Environment variable ``LYNX_LOCALE`` is honored at import time, so an end
user can run::

    LYNX_LOCALE=es lynx-portfolio -p -i

without touching any CLI flag.
"""

from __future__ import annotations

import gettext as _gettext_stdlib
import os
from pathlib import Path
from typing import Callable, Optional

__all__ = [
    "set_locale",
    "current_locale",
    "gettext",
    "ngettext",
    "_",
    "LOCALES_DIR",
    "DOMAIN",
]


#: Domain name used for the compiled ``.mo`` files (``lynx.mo``).
DOMAIN = "lynx"

#: Absolute path to the bundled ``locales/`` tree.
LOCALES_DIR: Path = Path(__file__).resolve().parent / "locales"


# ---------------------------------------------------------------------------
# Module-level translator state
# ---------------------------------------------------------------------------

_translation: _gettext_stdlib.NullTranslations = _gettext_stdlib.NullTranslations()
_current_locale: Optional[str] = None


def _install(translator: _gettext_stdlib.NullTranslations, code: Optional[str]) -> None:
    """Swap the active translator and refresh the module-level callables.

    Rebinding ``gettext`` / ``ngettext`` / ``_`` on the module object means
    callers that imported the names (``from ...i18n import _``) still get the
    old reference — that's a well-known gettext gotcha. The agreed contract
    here is that callers should *always* use the functions defined below
    (which delegate to ``_translation``) rather than caching a bound method
    of a specific catalog. The :func:`gettext`, :func:`ngettext` and
    :func:`_` functions defined further down do exactly that.
    """
    global _translation, _current_locale
    _translation = translator
    _current_locale = code


def set_locale(code: Optional[str]) -> None:
    """Install the catalog for *code* (e.g. ``"es"``).

    Passing ``None`` reverts to :class:`gettext.NullTranslations`, so every
    string is returned as its English source form.

    Unknown locales (no ``.mo`` file available) also silently fall back to
    the null translator — callers never have to handle a ``FileNotFoundError``.
    """
    if code is None:
        _install(_gettext_stdlib.NullTranslations(), None)
        return

    try:
        translator = _gettext_stdlib.translation(
            DOMAIN,
            localedir=str(LOCALES_DIR),
            languages=[code],
            fallback=False,
        )
    except (FileNotFoundError, OSError):
        # No catalog available — fall back silently to the null translator.
        _install(_gettext_stdlib.NullTranslations(), None)
        return

    _install(translator, code)


def current_locale() -> Optional[str]:
    """Return the currently-active locale code, or ``None`` if unset."""
    return _current_locale


# ---------------------------------------------------------------------------
# Public translation callables
# ---------------------------------------------------------------------------
#
# These must always delegate to the *current* ``_translation`` object, never
# capture a bound method, so that :func:`set_locale` takes effect for callers
# that did ``from lynx_investor_core.i18n import _``.


def gettext(message: str) -> str:
    """Translate *message* using the currently-installed catalog."""
    return _translation.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate a count-aware message using the active catalog."""
    return _translation.ngettext(singular, plural, n)


#: Idiomatic gettext alias. Imported by callers as ``from ... import _``.
_: Callable[[str], str] = gettext


# ---------------------------------------------------------------------------
# Environment bootstrap
# ---------------------------------------------------------------------------

def _bootstrap_from_env() -> None:
    """Honor ``LYNX_LOCALE`` on first import."""
    env = os.environ.get("LYNX_LOCALE")
    if env:
        set_locale(env.strip() or None)


_bootstrap_from_env()
