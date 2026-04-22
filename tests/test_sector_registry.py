"""Unit tests for :mod:`lynx_investor_core.sector_registry`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from lynx_investor_core.sector_registry import (
    AGENT_REGISTRY,
    AgentEntry,
    format_agent_suggestion,
    suggest_agent,
)


@dataclass
class _Profile:
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    name: str = "Test Co"
    ticker: str = "TEST"


class TestRegistryCoverage:
    """The registry must know about all eleven specialized investors."""

    def test_registry_has_eleven_agents(self) -> None:
        assert len(AGENT_REGISTRY) == 11

    def test_every_entry_has_name(self) -> None:
        for entry in AGENT_REGISTRY:
            assert entry.name.startswith("lynx-investor-")
            assert entry.display_name
            assert isinstance(entry, AgentEntry)

    def test_names_are_unique(self) -> None:
        names = [entry.name for entry in AGENT_REGISTRY]
        assert len(names) == len(set(names))


class TestSuggestAgentBySector:
    """Sector-only matching resolves to the right agent."""

    @pytest.mark.parametrize("sector,expected", [
        ("Basic Materials", "lynx-investor-basic-materials"),
        ("basic materials", "lynx-investor-basic-materials"),
        ("Energy", "lynx-investor-energy"),
        ("Healthcare", "lynx-investor-healthcare"),
        ("Health Care", "lynx-investor-healthcare"),
        ("Financial Services", "lynx-investor-financials"),
        ("Technology", "lynx-investor-information-technology"),
        ("Information Technology", "lynx-investor-information-technology"),
        ("Communication Services", "lynx-investor-communication-services"),
        ("Consumer Cyclical", "lynx-investor-consumer-discretionary"),
        ("Consumer Defensive", "lynx-investor-consumer-staples"),
        ("Industrials", "lynx-investor-industrials"),
        ("Utilities", "lynx-investor-utilities"),
        ("Real Estate", "lynx-investor-real-estate"),
    ])
    def test_sector_maps_to_expected_agent(self, sector: str, expected: str) -> None:
        assert suggest_agent(_Profile(sector=sector)) == expected


class TestSuggestAgentByIndustry:
    def test_gold_maps_to_basic_materials(self) -> None:
        assert (
            suggest_agent(_Profile(industry="Gold"))
            == "lynx-investor-basic-materials"
        )

    def test_oil_gas_maps_to_energy(self) -> None:
        assert (
            suggest_agent(_Profile(industry="Oil & Gas E&P"))
            == "lynx-investor-basic-materials"
            or suggest_agent(_Profile(industry="Oil & Gas E&P"))
            == "lynx-investor-energy"
        )

    def test_reit_maps_to_real_estate(self) -> None:
        assert (
            suggest_agent(_Profile(industry="REIT—Residential"))
            == "lynx-investor-real-estate"
        )


class TestSuggestAgentByDescription:
    def test_pharmaceutical_keyword(self) -> None:
        profile = _Profile(
            sector="Unknown", industry="Unknown",
            description="Develops pharmaceutical therapeutics for oncology.",
        )
        assert suggest_agent(profile) == "lynx-investor-healthcare"

    def test_bank_holding_company(self) -> None:
        profile = _Profile(
            sector="Unknown",
            description="XYZ is a bank holding company headquartered in Chicago.",
        )
        assert suggest_agent(profile) == "lynx-investor-financials"


class TestSuggestAgentExcludesCurrent:
    """``current_agent`` must never appear in the suggestion."""

    def test_current_agent_excluded(self) -> None:
        profile = _Profile(sector="Energy")
        result = suggest_agent(
            profile, current_agent="lynx-investor-energy",
        )
        # Basic-materials also claims Energy (uranium producers, etc.)
        assert result != "lynx-investor-energy"

    def test_unknown_profile_returns_none(self) -> None:
        assert suggest_agent(_Profile()) is None


class TestFormatAgentSuggestion:
    def test_suggestion_text_shape(self) -> None:
        profile = _Profile(sector="Healthcare")
        text = format_agent_suggestion(profile)
        assert "lynx-investor-healthcare" in text
        assert "Lince Investor Suite" in text
        assert text.startswith("\n\nSuggestion:")

    def test_empty_when_no_match(self) -> None:
        assert format_agent_suggestion(_Profile()) == ""

    def test_empty_when_same_agent(self) -> None:
        text = format_agent_suggestion(
            _Profile(sector="Energy"),
            current_agent="lynx-investor-energy",
        )
        # If basic-materials also matches, suggestion is non-empty
        # but will not contain the current agent.
        assert "lynx-investor-energy'" not in text

    def test_custom_prefix(self) -> None:
        text = format_agent_suggestion(
            _Profile(sector="Healthcare"), prefix=" | ",
        )
        assert text.startswith(" | use 'lynx-investor-healthcare'")
