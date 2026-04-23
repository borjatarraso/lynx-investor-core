"""Shared URL-safety helpers for the Lince Investor Suite.

Every downstream fetch in the suite (RSS-sourced news URLs, EDGAR download
links, user-clicked article links) runs user-influenced URLs through this
module first. The helpers block the two classes of abuse that recur across
the codebase:

* **SSRF** — an attacker who can inject a URL into an RSS feed or search
  result should not be able to make the Suite request an internal endpoint
  (``http://127.0.0.1:5000/api/cache``, cloud metadata services, LAN hosts).

* **Scheme injection** — passing a URL to ``webbrowser.open`` on Linux
  invokes ``xdg-open`` which registers handlers for ``file://``,
  ``javascript:``, ``smb://``, custom ``vscode://``/``slack://`` schemes,
  and more. An RSS feed pointing at ``file:///home/user/.ssh/id_rsa``
  would open the user's private key in their browser.

The module is dependency-light — only ``urllib`` and ``ipaddress`` from the
stdlib — so it is safe to import everywhere.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

__all__ = [
    "SAFE_SCHEMES",
    "UnsafeURLError",
    "is_safe_url",
    "validate_safe_url",
    "safe_webbrowser_open",
]


SAFE_SCHEMES: frozenset[str] = frozenset({"http", "https"})


class UnsafeURLError(ValueError):
    """Raised when a URL fails suite safety checks.

    Callers that want to surface the reason to the user should ``str(exc)``
    — the messages are short and free of PII.
    """


def _host_is_private(host: str) -> bool:
    """True if *host* resolves to a loopback, RFC1918, or link-local address.

    DNS lookup is performed so an attacker can't bypass the filter by
    registering a public name that resolves to ``127.0.0.1`` or
    ``169.254.169.254``. On lookup failure the host is treated as *unsafe*
    — the Suite does not open URLs whose safety cannot be established.
    """
    if not host:
        return True

    # Bracketed IPv6 literals
    host = host.strip("[]")

    # Fast path: literal IPs
    try:
        ip = ipaddress.ip_address(host)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        pass  # not a literal IP — fall through to DNS resolution

    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, socket.herror, UnicodeError, OSError):
        return True  # cannot verify → treat as unsafe

    for family, _type, _proto, _canonname, sockaddr in infos:
        if family in (socket.AF_INET, socket.AF_INET6):
            addr = sockaddr[0]
            # Strip scope id from IPv6 if present
            addr = addr.split("%")[0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return True
    return False


def _explain(url: str, reason: str) -> str:
    """Short, PII-free description for error messages / logs."""
    return f"refusing URL ({reason}): {url[:80]}"


def is_safe_url(
    url: Optional[str],
    *,
    allowed_schemes: frozenset[str] = SAFE_SCHEMES,
) -> bool:
    """Return ``True`` when *url* is safe for the Suite to open or fetch.

    Rejects: empty / None values, non-allowed schemes (``file://``,
    ``javascript:``, ``smb://``, ``ftp://``, …), URLs without a host, and
    hosts that resolve to loopback / RFC1918 / link-local / multicast /
    reserved addresses.
    """
    try:
        validate_safe_url(url, allowed_schemes=allowed_schemes)
    except UnsafeURLError:
        return False
    return True


def validate_safe_url(
    url: Optional[str],
    *,
    allowed_schemes: frozenset[str] = SAFE_SCHEMES,
) -> Tuple[str, str]:
    """Return ``(scheme, host)`` for *url*, raising :class:`UnsafeURLError`.

    Useful for callers that want to reuse the parsed host (for logging) and
    have the validation fail fast with a message.
    """
    if not url or not isinstance(url, str):
        raise UnsafeURLError(_explain(str(url), "empty or non-string"))
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in allowed_schemes:
        raise UnsafeURLError(_explain(url, f"scheme {scheme!r} not allowed"))
    host = (parsed.hostname or "").lower()
    if not host:
        raise UnsafeURLError(_explain(url, "no host"))
    if _host_is_private(host):
        raise UnsafeURLError(_explain(url, f"host {host!r} resolves to private/loopback"))
    return scheme, host


def safe_webbrowser_open(url: Optional[str]) -> bool:
    """Open *url* in the default browser only if it passes safety checks.

    Returns ``True`` when the URL was opened, ``False`` when it was refused.
    Callers can log / warn the user on ``False``. Failures inside
    :mod:`webbrowser` itself are also swallowed — unopenable URLs are not
    a hard error.
    """
    if not is_safe_url(url):
        return False
    try:
        import webbrowser
        return bool(webbrowser.open(url))
    except Exception:
        return False
