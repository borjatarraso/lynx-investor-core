"""Unit tests for :mod:`lynx_investor_core.urlsafe`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lynx_investor_core import urlsafe


class TestIsSafeURL:
    @pytest.mark.parametrize("url", [
        "https://www.nytimes.com/article",
        "http://example.com/page?q=1",
        "https://finance.yahoo.com/quote/AAPL",
    ])
    def test_public_https_passes(self, url: str) -> None:
        assert urlsafe.is_safe_url(url)

    @pytest.mark.parametrize("url", [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "smb://server/share",
        "ftp://ftp.example.com/file",
        "mailto:victim@example.com",
        "vscode://file/etc/passwd",
        "slack://open",
    ])
    def test_dangerous_scheme_blocked(self, url: str) -> None:
        assert not urlsafe.is_safe_url(url)

    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/api",
        "http://localhost:5000/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://[::1]/",
    ])
    def test_private_hosts_blocked(self, url: str) -> None:
        assert not urlsafe.is_safe_url(url)

    def test_none_blocked(self) -> None:
        assert not urlsafe.is_safe_url(None)

    def test_empty_blocked(self) -> None:
        assert not urlsafe.is_safe_url("")

    def test_no_host_blocked(self) -> None:
        assert not urlsafe.is_safe_url("https://")


class TestValidateSafeURL:
    def test_returns_scheme_and_host(self) -> None:
        scheme, host = urlsafe.validate_safe_url("https://www.example.com/foo")
        assert scheme == "https"
        assert host == "www.example.com"

    def test_raises_with_short_reason(self) -> None:
        with pytest.raises(urlsafe.UnsafeURLError, match="scheme"):
            urlsafe.validate_safe_url("file:///etc/passwd")

    def test_raises_on_loopback(self) -> None:
        with pytest.raises(urlsafe.UnsafeURLError, match="private/loopback"):
            urlsafe.validate_safe_url("http://127.0.0.1/")


class TestDNSRebindingProtection:
    """A public hostname that resolves to a private IP must be blocked."""

    def test_dns_resolves_to_private_ip(self) -> None:
        def fake_getaddrinfo(host, port, *_a, **_kw):
            # pretend public-looking host resolves to 127.0.0.1
            return [(2, 1, 6, "", ("127.0.0.1", 0))]

        with patch.object(urlsafe.socket, "getaddrinfo", side_effect=fake_getaddrinfo):
            assert not urlsafe.is_safe_url("http://attacker.example/")

    def test_unresolvable_host_blocked(self) -> None:
        def raise_gaierror(*_a, **_kw):
            import socket as _s
            raise _s.gaierror("not resolvable")

        with patch.object(urlsafe.socket, "getaddrinfo", side_effect=raise_gaierror):
            assert not urlsafe.is_safe_url("http://nonexistent.invalid/")


class TestSafeWebbrowserOpen:
    def test_refuses_unsafe_url(self) -> None:
        assert not urlsafe.safe_webbrowser_open("file:///etc/passwd")

    def test_refuses_javascript(self) -> None:
        assert not urlsafe.safe_webbrowser_open("javascript:alert(1)")

    def test_passes_safe_url_to_webbrowser(self) -> None:
        with patch("webbrowser.open") as mock_open:
            mock_open.return_value = True
            result = urlsafe.safe_webbrowser_open("https://example.com/ok")
            assert result is True
            mock_open.assert_called_once_with("https://example.com/ok")

    def test_webbrowser_exception_swallowed(self) -> None:
        with patch("webbrowser.open", side_effect=RuntimeError("boom")):
            assert not urlsafe.safe_webbrowser_open("https://example.com/ok")
