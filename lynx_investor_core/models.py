"""Generic shared data classes (used by every Lynx investor agent)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsArticle:
    title: str
    url: str
    published: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    local_path: Optional[str] = None
