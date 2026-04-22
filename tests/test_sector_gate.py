"""Unit tests for :mod:`lynx_investor_core.sector_gate`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from lynx_investor_core.sector_gate import (
    SectorMismatchError,
    SectorValidator,
)


@dataclass
class _Profile:
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    name: str = "Test Co"
    ticker: str = "TEST"


@pytest.fixture()
def mining_validator() -> SectorValidator:
    return SectorValidator.build(
        allowed_sectors=("basic materials",),
        allowed_industries=("gold", "copper"),
        description_patterns=(r"\bmining\b",),
        scope_description="the scope of basic materials",
        agent_name="lynx-investor-basic-materials",
    )


class TestValidate:
    def test_allowed_sector_passes(self, mining_validator: SectorValidator) -> None:
        mining_validator.validate(_Profile(sector="Basic Materials"))

    def test_allowed_industry_passes(self, mining_validator: SectorValidator) -> None:
        mining_validator.validate(_Profile(sector="Other", industry="Gold"))

    def test_description_pattern_passes(self, mining_validator: SectorValidator) -> None:
        mining_validator.validate(_Profile(
            sector="Other", industry="Other",
            description="A gold mining exploration company.",
        ))

    def test_unrelated_profile_raises(self, mining_validator: SectorValidator) -> None:
        with pytest.raises(SectorMismatchError):
            mining_validator.validate(_Profile(
                sector="Healthcare", industry="Biotechnology",
            ))

    def test_is_allowed_returns_bool(self, mining_validator: SectorValidator) -> None:
        assert mining_validator.is_allowed(_Profile(sector="Basic Materials"))
        assert not mining_validator.is_allowed(_Profile(sector="Technology"))


class TestErrorMessage:
    def test_existing_text_preserved(
        self, mining_validator: SectorValidator,
    ) -> None:
        with pytest.raises(SectorMismatchError) as exc:
            mining_validator.validate(_Profile(
                sector="Healthcare", industry="Biotechnology",
            ))
        message = str(exc.value)
        # The historical phrasing must remain intact.
        assert "outside the scope of basic materials" in message
        assert "'Healthcare' / 'Biotechnology'" in message

    def test_suggestion_appended_for_other_agent(
        self, mining_validator: SectorValidator,
    ) -> None:
        with pytest.raises(SectorMismatchError) as exc:
            mining_validator.validate(_Profile(
                sector="Healthcare", industry="Biotechnology",
                description="Biopharmaceutical platform.",
            ))
        message = str(exc.value)
        assert "Suggestion:" in message
        assert "lynx-investor-healthcare" in message

    def test_suggestion_excludes_self(self) -> None:
        validator = SectorValidator.build(
            allowed_sectors=("energy",),
            allowed_industries=("oil & gas",),
            scope_description="the scope of energy",
            agent_name="lynx-investor-energy",
        )
        with pytest.raises(SectorMismatchError) as exc:
            validator.validate(_Profile(sector="Technology"))
        message = str(exc.value)
        # The energy agent itself is not suggested.
        assert "use 'lynx-investor-energy'" not in message

    def test_no_agent_name_still_produces_message(self) -> None:
        validator = SectorValidator.build(
            allowed_sectors=("energy",),
            allowed_industries=(),
            scope_description="the scope of energy",
        )
        with pytest.raises(SectorMismatchError) as exc:
            validator.validate(_Profile(sector="Healthcare"))
        # Without an agent_name we still pull a suggestion from the registry.
        assert "Healthcare" in str(exc.value)
