"""ASCII logo loader."""

from __future__ import annotations

from pathlib import Path


def load_logo_ascii(package_dir: str | Path, *, filename: str = "logo_ascii.txt") -> str:
    """Load ``img/<filename>`` relative to the agent's project root.

    ``package_dir`` is typically ``Path(__file__).resolve().parent`` of the
    agent's ``__init__.py`` — the parent of *that* is the project root that
    holds the ``img/`` directory.
    """
    project_root = Path(package_dir).resolve().parent
    logo_path = project_root / "img" / filename
    try:
        return logo_path.read_text(encoding="utf-8").rstrip("\n")
    except (FileNotFoundError, OSError):
        return ""
