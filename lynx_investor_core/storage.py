"""Local data storage management.

Two isolated data directories:
  - Production: ``<base_dir>/data/``      (cache-enabled, persistent)
  - Testing:    ``<base_dir>/data_test/`` (always fresh, disposable)

Each agent calls :func:`set_base_dir` at import time, pointing to its own
project root, so ``data/`` and ``data_test/`` live next to the agent package.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_MODE: str = "production"
_DATA_DIR_NAMES = {"production": "data", "testing": "data_test"}
_BASE_DIR: Optional[Path] = None


def set_base_dir(path: str | Path) -> None:
    """Set the directory under which ``data/`` and ``data_test/`` live.

    Called by each agent's ``__init__.py`` so caches stay isolated per-agent.
    """
    global _BASE_DIR
    _BASE_DIR = Path(path)


def get_base_dir() -> Path:
    if _BASE_DIR is None:
        raise RuntimeError(
            "lynx_investor_core.storage: base directory not configured. "
            "The agent must call storage.set_base_dir(path) at import time."
        )
    return _BASE_DIR


def set_mode(mode: str) -> None:
    global _MODE
    if mode not in _DATA_DIR_NAMES:
        raise ValueError(f"Unknown mode '{mode}'. Use 'production' or 'testing'.")
    _MODE = mode


def get_mode() -> str:
    return _MODE


def is_testing() -> bool:
    return _MODE == "testing"


def get_data_root() -> Path:
    dir_name = _DATA_DIR_NAMES[_MODE]
    root = get_base_dir() / dir_name
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sanitize_ticker(ticker: str) -> str:
    """Sanitize ticker to prevent path traversal."""
    import re
    safe = re.sub(r'[^A-Z0-9.\-]', '_', ticker.upper())
    safe = safe.replace('..', '_').strip('_. ')
    return safe or "UNKNOWN"


def get_company_dir(ticker: str) -> Path:
    safe = _sanitize_ticker(ticker)
    d = get_data_root() / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_reports_dir(ticker: str) -> Path:
    d = get_company_dir(ticker) / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_news_dir(ticker: str) -> Path:
    d = get_company_dir(ticker) / "news"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_financials_dir(ticker: str) -> Path:
    d = get_company_dir(ticker) / "financials"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_json(path: Path, data: Any) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(path: Path, text: str) -> Path:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def save_binary(path: Path, content: bytes) -> Path:
    with open(path, "wb") as f:
        f.write(content)
    return path


def save_analysis_report(ticker: str, report_dict: dict) -> Path:
    d = get_company_dir(ticker)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = d / f"analysis_{ts}.json"
    save_json(path, report_dict)
    latest = d / "analysis_latest.json"
    save_json(latest, report_dict)
    return path


def load_cached_report(ticker: str) -> Optional[dict]:
    if is_testing():
        return None
    latest = get_company_dir(ticker) / "analysis_latest.json"
    if latest.exists():
        try:
            return load_json(latest)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def get_cache_age_hours(ticker: str) -> Optional[float]:
    latest = get_company_dir(ticker) / "analysis_latest.json"
    if not latest.exists():
        return None
    try:
        data = load_json(latest)
        fetched = data.get("fetched_at")
        if fetched:
            ts = datetime.fromisoformat(fetched)
            now = datetime.now(ts.tzinfo)
            return max((now - ts).total_seconds() / 3600, 0)
    except Exception:
        pass
    try:
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)
        return max((datetime.now() - mtime).total_seconds() / 3600, 0)
    except Exception:
        return None


def has_cache(ticker: str) -> bool:
    if is_testing():
        return False
    return (get_company_dir(ticker) / "analysis_latest.json").exists()


def list_saved_analyses(ticker: str) -> list[Path]:
    return sorted(get_company_dir(ticker).glob("analysis_*.json"), reverse=True)


def drop_cache_ticker(ticker: str) -> bool:
    safe = _sanitize_ticker(ticker)
    d = get_data_root() / safe
    if d.exists() and d.is_dir():
        shutil.rmtree(d)
        return True
    return False


def drop_cache_all() -> int:
    root = get_data_root()
    count = 0
    for d in root.iterdir():
        if d.is_dir():
            shutil.rmtree(d)
            count += 1
    return count


def list_cached_tickers() -> list[dict]:
    root = get_data_root()
    if not root.exists():
        return []
    tickers = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        latest = d / "analysis_latest.json"
        info: dict = {"ticker": d.name, "path": str(d)}
        if latest.exists():
            try:
                data = load_json(latest)
                profile = data.get("profile", {})
                info["name"] = profile.get("name", "")
                info["tier"] = profile.get("tier", "")
                info["stage"] = profile.get("stage", "")
                info["fetched_at"] = data.get("fetched_at", "")
                age = get_cache_age_hours(d.name)
                info["age_hours"] = round(age, 1) if age is not None else None
            except Exception:
                pass
        info["files"] = sum(1 for _ in d.rglob("*") if _.is_file())
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        info["size_mb"] = round(size / (1024 * 1024), 2)
        tickers.append(info)
    return tickers
