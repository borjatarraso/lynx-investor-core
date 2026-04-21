"""Shared argparse boilerplate for every Lynx investor agent.

Call :func:`add_standard_args` after creating the parser in your agent's
``cli.build_parser()``. It registers every argument that is identical across
agents (``-p``/``-t`` run mode, UI mode group, refresh/cache flags, export,
``--about``, ``--version``, ``--explain`` family, etc.).

Agent-specific argparse behavior (program name, description, epilog examples)
stays in the agent's own ``build_parser`` — just add those before/after the
call to :func:`add_standard_args`.
"""

from __future__ import annotations

import argparse


def positive_int(value: str) -> int:
    """argparse ``type=`` helper that rejects 0 / negatives."""
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return n


def add_standard_args(
    parser: argparse.ArgumentParser,
    *,
    version_string: str,
) -> None:
    """Register every argument shared across investor agents."""
    run_mode = parser.add_mutually_exclusive_group(required=True)
    run_mode.add_argument(
        "-p", "--production-mode",
        action="store_const", const="production", dest="run_mode",
        help="Production mode: use data/ for persistent cache",
    )
    run_mode.add_argument(
        "-t", "--testing-mode",
        action="store_const", const="testing", dest="run_mode",
        help="Testing mode: use data_test/ (isolated, always fresh)",
    )

    parser.add_argument(
        "identifier", nargs="?",
        help="Ticker symbol, ISIN, or company name",
    )

    ui_mode = parser.add_mutually_exclusive_group()
    ui_mode.add_argument("-i", "--interactive-mode", action="store_true", dest="interactive")
    ui_mode.add_argument("-tui", "--textual-ui", action="store_true", dest="tui")
    ui_mode.add_argument("-s", "--search", action="store_true")
    ui_mode.add_argument("-x", "--gui", action="store_true",
                         help="Launch the graphical user interface (Tkinter)")

    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--drop-cache", metavar="TICKER", nargs="?", const="__prompt__")
    parser.add_argument("--list-cache", action="store_true")
    parser.add_argument("--no-reports", action="store_true",
                        help="Skip fetching SEC/SEDAR filings")
    parser.add_argument("--no-news", action="store_true",
                        help="Skip fetching news articles")

    parser.add_argument("--max-filings", type=positive_int, default=10, metavar="N",
                        help="Maximum filings to download (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--export", choices=["txt", "html", "pdf"], metavar="FORMAT")
    parser.add_argument("--output", metavar="PATH")
    parser.add_argument("--version", action="version", version=version_string)
    parser.add_argument("--about", action="store_true")
    parser.add_argument("--explain", metavar="METRIC", nargs="?", const="__list__")
    parser.add_argument("--explain-section", metavar="SECTION", nargs="?", const="__list__")
    parser.add_argument("--explain-conclusion", metavar="CATEGORY", nargs="?", const="overall")
