"""Shared author / signature footer for every Suite export.

Every report exported from any Suite tool (txt, html, pdf) gets the
same footer block crediting the author. Centralising it here means
there's one place to update when authorship metadata changes.
"""

from __future__ import annotations

AUTHOR_NAME = "Borja Tarraso"
AUTHOR_EMAIL = "borja.tarraso@member.fsf.org"
AUTHOR_LICENSE = "BSD-3-Clause"
SUITE_NAME = "Lince Investor Suite"


def text_footer(suite_label: str | None = None) -> str:
    """Return the author footer formatted for plain-text reports."""
    label = suite_label or SUITE_NAME
    return (
        "\n"
        + ("─" * 78)
        + "\n"
        + f"  {label}\n"
        + f"  Authored by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>\n"
        + f"  License: {AUTHOR_LICENSE}\n"
        + "  All Suite reports are signed by the author for provenance.\n"
        + ("─" * 78)
        + "\n"
    )


def html_footer(suite_label: str | None = None) -> str:
    """Return the author footer formatted as an HTML ``<footer>`` block."""
    label = suite_label or SUITE_NAME
    return (
        "<hr style='border:none;border-top:1px solid #45475a;margin-top:32px;'/>"
        "<footer style='color:#bac2de;font-family:sans-serif;font-size:0.9em;"
        "padding:14px 4px;'>"
        f"<div><strong>{label}</strong></div>"
        f"<div>Authored by: {AUTHOR_NAME} "
        f"&lt;<a style='color:#89b4fa' "
        f"href='mailto:{AUTHOR_EMAIL}'>{AUTHOR_EMAIL}</a>&gt;</div>"
        f"<div>License: {AUTHOR_LICENSE}</div>"
        "<div><em>All Suite reports are signed by the author for provenance.</em></div>"
        "</footer>"
    )


def markdown_footer(suite_label: str | None = None) -> str:
    """Return the author footer for Markdown / RST docs (READMEs)."""
    label = suite_label or SUITE_NAME
    return (
        "\n---\n\n"
        f"## Author and signature\n\n"
        f"This project is part of the **{label}**, authored and signed by\n\n"
        f"> **{AUTHOR_NAME}** &lt;[{AUTHOR_EMAIL}](mailto:{AUTHOR_EMAIL})&gt;\n"
        f"> Licensed under {AUTHOR_LICENSE}.\n\n"
        f"Every report and export emitted by Suite tools includes this same\n"
        f"signature in its footer. The shipped logo PNGs additionally carry the\n"
        f"author's signature via steganography for provenance — please do not\n"
        f"replace or re-encode the logo files.\n"
    )
