"""Registry of the specialized investor agents shipped with the Suite.

Each entry in :data:`AGENT_REGISTRY` describes which Yahoo ``sector`` /
``industry`` values — and which description patterns — are the primary
domain of one of the specialized ``lynx-investor-*`` agents. The registry
is consulted by :mod:`lynx_investor_core.sector_gate` to append a
"use ``<agent>`` instead" line whenever an agent refuses a company that
belongs to another agent's scope.

The registry lives in the shared core package on purpose: even when a user
only installs one specialized agent (say ``lynx-investor-basic-materials``),
they still see a useful redirection toward, e.g., ``lynx-investor-energy``
if they point it at an oil major.

This module is import-safe at package load time; it performs no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Protocol, Tuple


__all__ = [
    "AgentEntry",
    "AGENT_REGISTRY",
    "suggest_agent",
    "format_agent_suggestion",
]


class _ProfileLike(Protocol):
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]


@dataclass(frozen=True)
class AgentEntry:
    """One row of the sector → agent mapping."""

    name: str                                  # canonical CLI / package name
    display_name: str                          # human-friendly label
    sectors: FrozenSet[str] = field(default_factory=frozenset)
    industries: FrozenSet[str] = field(default_factory=frozenset)
    description_patterns: Tuple[str, ...] = ()

    def matches(self, profile: _ProfileLike) -> bool:
        """True if *profile* belongs to this agent's primary domain."""
        sector = (profile.sector or "").lower().strip()
        industry = (profile.industry or "").lower().strip()
        if sector and sector in self.sectors:
            return True
        if industry:
            for allowed in self.industries:
                if allowed in industry or industry in allowed:
                    return True
        if self.description_patterns:
            desc = (profile.description or "").lower()
            if any(re.search(p, desc) for p in self.description_patterns):
                return True
        return False


def _f(*items: str) -> FrozenSet[str]:
    return frozenset(s.lower() for s in items)


# Every specialized investor currently shipped in the Suite. The order
# here is the tie-break order: when a profile matches more than one
# entry we pick the first. Sectors with the most specific identification
# (description patterns) come first so, e.g., a Basic-Materials-listed
# miner is steered to lynx-investor-basic-materials rather than to a
# generic sector match.
AGENT_REGISTRY: Tuple[AgentEntry, ...] = (
    AgentEntry(
        name="lynx-investor-basic-materials",
        display_name="lynx-investor-basic-materials",
        sectors=_f("basic materials"),
        industries=_f(
            "gold", "silver", "copper", "uranium",
            "other industrial metals & mining",
            "other precious metals & mining",
            "specialty mining & metals", "coking coal",
            "steel", "agricultural inputs", "chemicals",
            "industrial metals & minerals",
            "metals & mining", "aluminum", "coal",
            "diversified metals & mining", "thermal coal",
        ),
        description_patterns=(
            r"\bmining\b", r"\bmineral propert", r"\bmineral resource",
            r"\bore body\b", r"\bore deposit\b", r"\bopen.?pit\b",
            r"\bunderground mine\b", r"\bNI 43-101\b", r"\bJORC\b",
            r"\bAISC\b", r"\bsmelter\b", r"\bgold mine\b",
            r"\bsilver mine\b", r"\bcopper mine\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-energy",
        display_name="lynx-investor-energy",
        sectors=_f("energy"),
        industries=_f(
            "oil & gas", "oil & gas e&p", "oil & gas integrated",
            "oil & gas midstream", "oil & gas refining & marketing",
            "oil & gas equipment & services", "oil & gas drilling",
            "uranium", "thermal coal",
        ),
        description_patterns=(
            r"\boil and gas\b", r"\bupstream\b", r"\bdownstream\b",
            r"\brefining\b", r"\bnatural gas\b", r"\bpetroleum\b",
            r"\blng\b", r"\bpipeline operator\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-healthcare",
        display_name="lynx-investor-healthcare",
        sectors=_f("healthcare", "health care"),
        industries=_f(
            "drug manufacturers - general", "drug manufacturers—general",
            "drug manufacturers - specialty & generic",
            "drug manufacturers—specialty & generic",
            "biotechnology", "medical devices",
            "medical instruments & supplies",
            "medical care facilities", "medical distribution",
            "diagnostics & research", "healthcare plans",
            "health information services", "pharmaceutical retailers",
            "long-term care facilities", "pharmaceutical preparations",
        ),
        description_patterns=(
            r"\bpharmaceutical\b", r"\bbiopharmaceutical\b",
            r"\bbiotech(nology)?\b", r"\bclinical.?stage\b",
            r"\bphase [123iv]+\b", r"\bpreclinical\b",
            r"\bmonoclonal antibody\b", r"\bgene therapy\b",
            r"\bcell therapy\b", r"\bmrna\b", r"\bcrispr\b",
            r"\bvaccine\b", r"\bmedical devices?\b",
            r"\bmedical equipment\b", r"\bdiagnostic\b",
            r"\bhospital operator\b", r"\bhealth system\b",
            r"\bdialysis\b", r"\bmanaged care\b",
            r"\bhealth insurance\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-financials",
        display_name="lynx-investor-financials",
        sectors=_f("financial services", "financials", "financial"),
        industries=_f(
            "banks", "banks—regional", "banks—diversified",
            "asset management", "capital markets",
            "insurance—life", "insurance—property & casualty",
            "insurance—specialty", "insurance brokers",
            "insurance—diversified", "insurance—reinsurance",
            "credit services", "financial data & stock exchanges",
            "mortgage finance", "shell companies",
        ),
        description_patterns=(
            r"\bbank holding company\b", r"\bcommercial bank\b",
            r"\binvestment bank\b", r"\basset manager\b",
            r"\binsurance underwrit", r"\breinsur",
            r"\bbroker-?dealer\b", r"\bexchange operator\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-information-technology",
        display_name="lynx-investor-information-technology",
        sectors=_f("technology", "information technology"),
        industries=_f(
            "software—application", "software—infrastructure",
            "semiconductors", "semiconductor equipment & materials",
            "consumer electronics", "computer hardware",
            "electronic components",
            "electronics & computer distribution",
            "information technology services",
            "scientific & technical instruments",
            "solar",
        ),
        description_patterns=(
            r"\bsoftware.as.a.service\b", r"\bsaas\b",
            r"\bcloud platform\b", r"\bsemiconductor\b",
            r"\bfoundry\b", r"\bdata center\b",
            r"\boperating system\b", r"\bdeveloper platform\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-communication-services",
        display_name="lynx-investor-communication-services",
        sectors=_f("communication services", "communications"),
        industries=_f(
            "telecom services", "entertainment",
            "internet content & information",
            "electronic gaming & multimedia",
            "publishing", "advertising agencies",
            "broadcasting",
        ),
        description_patterns=(
            r"\btelecom(munications)?\b", r"\bwireless carrier\b",
            r"\bstreaming (service|platform)\b",
            r"\bsearch engine\b", r"\bsocial (network|media) platform\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-consumer-discretionary",
        display_name="lynx-investor-consumer-discretionary",
        sectors=_f("consumer cyclical", "consumer discretionary"),
        industries=_f(
            "auto manufacturers", "auto parts",
            "auto & truck dealerships", "recreational vehicles",
            "apparel manufacturing", "apparel retail",
            "footwear & accessories", "leisure",
            "gambling", "resorts & casinos",
            "restaurants", "specialty retail",
            "internet retail", "home improvement retail",
            "lodging", "luxury goods", "personal services",
            "residential construction", "furnishings, fixtures & appliances",
            "travel services", "department stores",
        ),
        description_patterns=(
            r"\bautomotive manufactur", r"\be-?commerce\b",
            r"\bquick.service restaurant\b", r"\bcasino\b",
            r"\bresort\b", r"\bapparel brand\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-consumer-staples",
        display_name="lynx-investor-consumer-staples",
        sectors=_f("consumer defensive", "consumer staples"),
        industries=_f(
            "beverages—non-alcoholic", "beverages—wineries & distilleries",
            "beverages—brewers", "confectioners",
            "farm products", "food distribution",
            "grocery stores", "household & personal products",
            "packaged foods", "discount stores",
            "tobacco", "education & training services",
        ),
        description_patterns=(
            r"\bconsumer packaged goods\b", r"\bcpg\b",
            r"\bgrocery retailer\b", r"\btobacco manufactur",
            r"\bpackaged food\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-industrials",
        display_name="lynx-investor-industrials",
        sectors=_f("industrials"),
        industries=_f(
            "aerospace & defense", "airlines", "airports & air services",
            "building products & equipment", "business equipment & supplies",
            "conglomerates", "consulting services",
            "electrical equipment & parts", "engineering & construction",
            "farm & heavy construction machinery",
            "industrial distribution", "infrastructure operations",
            "integrated freight & logistics", "marine shipping",
            "metal fabrication", "pollution & treatment controls",
            "railroads", "rental & leasing services",
            "security & protection services", "specialty business services",
            "specialty industrial machinery", "staffing & employment services",
            "tools & accessories", "trucking", "waste management",
        ),
        description_patterns=(
            r"\baerospace\b", r"\bdefense contractor\b",
            r"\bfreight\b", r"\brailroad\b",
            r"\bindustrial machinery\b", r"\bconstruction equipment\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-utilities",
        display_name="lynx-investor-utilities",
        sectors=_f("utilities"),
        industries=_f(
            "utilities—regulated electric", "utilities—regulated gas",
            "utilities—regulated water", "utilities—diversified",
            "utilities—independent power producers",
            "utilities—renewable", "utilities",
        ),
        description_patterns=(
            r"\belectric utility\b", r"\bgas utility\b",
            r"\bwater utility\b", r"\bregulated utility\b",
            r"\bindependent power producer\b",
        ),
    ),
    AgentEntry(
        name="lynx-investor-real-estate",
        display_name="lynx-investor-real-estate",
        sectors=_f("real estate", "real estate\u2014reits"),
        industries=_f(
            "reit—residential", "reit—retail", "reit—office",
            "reit—industrial", "reit—healthcare facilities",
            "reit—hotel & motel", "reit—mortgage",
            "reit—specialty", "reit—diversified",
            "real estate services", "real estate—development",
            "real estate—diversified",
        ),
        description_patterns=(
            r"\breal estate investment trust\b", r"\breit\b",
            r"\bproperty portfolio\b", r"\bcommercial real estate\b",
            r"\bresidential real estate\b",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest_agent(
    profile: _ProfileLike,
    *,
    current_agent: Optional[str] = None,
) -> Optional[str]:
    """Return the best-matching agent name for *profile*, or ``None``.

    When *current_agent* is given, that entry is skipped in the lookup so
    the suggestion is never "use the agent you're already using".
    Matching follows the normal sector → industry → description precedence.
    """
    for entry in AGENT_REGISTRY:
        if current_agent and entry.name == current_agent:
            continue
        if entry.matches(profile):
            return entry.display_name
    return None


def format_agent_suggestion(
    profile: _ProfileLike,
    *,
    current_agent: Optional[str] = None,
    prefix: str = "\n\nSuggestion: ",
) -> str:
    """Return a ready-to-append suggestion line, or ``""`` when no match.

    Example output::

        "\\n\\nSuggestion: use 'lynx-investor-energy' from the Lince
         Investor Suite instead."
    """
    agent = suggest_agent(profile, current_agent=current_agent)
    if not agent:
        return ""
    return (
        f"{prefix}use '{agent}' from the Lince Investor Suite instead."
    )
