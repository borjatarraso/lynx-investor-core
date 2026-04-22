"""Sector validation gate.

Each specialized investor agent (mining, energy, IT, …) refuses to analyze
companies outside its scope. The rules are identical in structure:

1. Allow if Yahoo Finance's ``sector`` field is one of a small whitelist.
2. Else, allow if the Yahoo ``industry`` label matches (substring) a list of
   agent-specific industries.
3. Else, allow if the business description mentions any domain-specific term
   (matched with word boundaries so ``"ore"`` does not match inside ``"store"``).
4. Else, raise :class:`SectorMismatchError`.

Agents instantiate :class:`SectorValidator` with their own config. When the
validator knows its own agent name (via ``agent_name``) it automatically
appends a "Suggestion: use '<other-agent>' instead" line — sourced from
:mod:`lynx_investor_core.sector_registry` — to the exception message,
while keeping the existing warning text exactly as it was.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional, Protocol

from .sector_registry import format_agent_suggestion


class _ProfileLike(Protocol):
    name: str
    ticker: str
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]


class SectorMismatchError(Exception):
    """Raised when a company does not belong to the agent's allowed scope."""
    pass


@dataclass(frozen=True)
class SectorValidator:
    """Immutable validator configured once per agent."""

    allowed_sectors: frozenset[str]
    allowed_industries: frozenset[str]
    description_patterns: tuple[str, ...] = ()
    scope_description: str = "this sector"  # used in the error message
    agent_name: Optional[str] = None        # enables suite-aware suggestions

    @classmethod
    def build(
        cls,
        *,
        allowed_sectors: Iterable[str],
        allowed_industries: Iterable[str],
        description_patterns: Iterable[str] = (),
        scope_description: str = "this sector",
        agent_name: Optional[str] = None,
    ) -> "SectorValidator":
        return cls(
            allowed_sectors=frozenset(s.lower() for s in allowed_sectors),
            allowed_industries=frozenset(s.lower() for s in allowed_industries),
            description_patterns=tuple(description_patterns),
            scope_description=scope_description,
            agent_name=agent_name,
        )

    def validate(self, profile: _ProfileLike) -> None:
        """Raise :class:`SectorMismatchError` if *profile* is out of scope."""
        sector = (profile.sector or "").lower().strip()
        industry = (profile.industry or "").lower().strip()

        if sector in self.allowed_sectors:
            return

        if industry:
            for allowed in self.allowed_industries:
                if allowed in industry or industry in allowed:
                    return

        desc = (profile.description or "").lower()
        if self.description_patterns and any(
            re.search(pattern, desc) for pattern in self.description_patterns
        ):
            return

        message = (
            f"{profile.name} ({profile.ticker}) is in the "
            f"'{profile.sector or 'Unknown'}' / '{profile.industry or 'Unknown'}' "
            f"sector/industry, which is outside {self.scope_description}."
        )
        message += format_agent_suggestion(
            profile, current_agent=self.agent_name,
        )
        raise SectorMismatchError(message)

    def is_allowed(self, profile: _ProfileLike) -> bool:
        try:
            self.validate(profile)
            return True
        except SectorMismatchError:
            return False
