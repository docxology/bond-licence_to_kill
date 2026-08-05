"""Narcotics-finance economics — price chain, cash physics, and manifest feasibility.

The ROGUE mission's fourth domain: quantify the *money side* of the Sanchez
cartel. The film opens with an intercepted courier flight carrying ~$5M in
cash; this module models the cocaine supply chain that generates that cash
(production → export → wholesale → street, with purity adjustment) and the
physics of the cash itself (bill mass/volume per denomination), then checks
whether a given value physically fits the Wavekrest-class hold — volume,
mass, and cover constraints — and how many trips it takes.

Everything is closed-form, deterministic, and pure (stdlib only): price
multipliers, purity-adjusted unit economics, US-currency bill physics, and
manifest arithmetic. Constants are documented and sourced
(US Bureau of Engraving and Printing currency specifications; DEA price
data anchors).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

__all__ = [
    "BILL_MASS_G",
    "BILL_VOLUME_CM3",
    "ManifestCheck",
    "NarcoticsFinanceReport",
    "analyze_narcotics_finance",
    "canonical_finance_params",
    "cash_bills",
    "cash_density_kg_m3",
    "cash_mass_kg",
    "cash_volume_m3",
    "manifest_feasibility",
    "price_chain",
    "purity_adjusted_price",
    "trips_required",
]

#: Mass of a single US currency note, grams (BEP currency specifications).
BILL_MASS_G = 1.0
#: Approximate volume of a single folded note, cm³ (156×66 mm, 0.11 mm thick).
BILL_VOLUME_CM3 = 1.13


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def price_chain(
    base_cost_per_kg: float,
    stages: tuple[tuple[str, float], ...],
) -> tuple[dict[str, float], float]:
    """Apply sequential markup multipliers down the supply chain.

    Returns ``(stage_prices, final_price_per_kg)`` where each stage price is
    the cumulative product of the multipliers up to that stage.
    """
    _require(base_cost_per_kg > 0.0, "base_cost_per_kg must be positive")
    _require(bool(stages), "stages must not be empty")
    stage_prices: dict[str, float] = {}
    price = float(base_cost_per_kg)
    for name, multiplier in stages:
        _require(bool(name.strip()), "stage names must be non-empty")
        _require(multiplier > 0.0, f"stage {name!r} multiplier must be positive")
        price *= multiplier
        stage_prices[name] = price
    return stage_prices, price


def purity_adjusted_price(price_per_kg: float, purity: float) -> float:
    """Price per kg of *pure* product: divide by the purity fraction."""
    _require(price_per_kg > 0.0, "price_per_kg must be positive")
    _require(0.0 < purity <= 1.0, "purity must be in (0, 1]")
    return price_per_kg / purity


def cash_bills(value: float, denomination: float) -> int:
    """Whole notes needed to carry ``value`` (ceil — conservative)."""
    _require(value > 0.0, "value must be positive")
    _require(denomination > 0.0, "denomination must be positive")
    return math.ceil(value / denomination)


def cash_mass_kg(value: float, denomination: float) -> float:
    """Bulk-cash mass in kilograms for ``value`` in notes of ``denomination``."""
    return cash_bills(value, denomination) * BILL_MASS_G / 1000.0


def cash_volume_m3(value: float, denomination: float) -> float:
    """Bulk-cash volume in cubic metres for ``value`` in notes of ``denomination``."""
    return cash_bills(value, denomination) * BILL_VOLUME_CM3 / 1e6


def cash_density_kg_m3(value: float, denomination: float) -> float:
    """Packed-cash bulk density (kg/m³) for a given denomination mix."""
    return cash_mass_kg(value, denomination) / cash_volume_m3(value, denomination)


@dataclass(frozen=True)
class ManifestCheck:
    """Volume/mass feasibility of a cash parcel against a hold."""

    feasible: bool
    mass_kg: float
    volume_m3: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feasible": self.feasible,
            "mass_kg": self.mass_kg,
            "volume_m3": self.volume_m3,
            "reason": self.reason,
        }


def manifest_feasibility(
    value: float,
    denomination: float,
    hold_volume_m3: float,
    hold_mass_kg: float,
) -> ManifestCheck:
    """Check whether ``value`` fits a hold of given volume and mass capacity."""
    _require(hold_volume_m3 > 0.0, "hold_volume_m3 must be positive")
    _require(hold_mass_kg > 0.0, "hold_mass_kg must be positive")
    mass = cash_mass_kg(value, denomination)
    volume = cash_volume_m3(value, denomination)
    volume_ok = volume <= hold_volume_m3
    mass_ok = mass <= hold_mass_kg
    if volume_ok and mass_ok:
        reason = "fits hold volume and mass"
    elif not volume_ok and not mass_ok:
        reason = "exceeds hold volume and mass"
    elif not volume_ok:
        reason = "exceeds hold volume"
    else:
        reason = "exceeds hold mass"
    return ManifestCheck(volume_ok and mass_ok, mass, volume, reason)


def trips_required(value: float, denomination: float, hold_volume_m3: float) -> int:
    """Whole trips needed to move ``value`` given a hold's usable volume."""
    _require(hold_volume_m3 > 0.0, "hold_volume_m3 must be positive")
    volume = cash_volume_m3(value, denomination)
    return max(1, math.ceil(volume / hold_volume_m3))


@dataclass(frozen=True)
class NarcoticsFinanceReport:
    """Deterministic narcotics-finance summary for one canonical scenario."""

    value_usd: float
    denomination: float
    bills: int
    mass_kg: float
    volume_m3: float
    density_kg_m3: float
    stage_prices: dict[str, float]
    wholesale_per_kg: float
    street_per_gram: float
    street_per_pure_gram: float
    manifest: ManifestCheck
    trips: int

    def as_dict(self) -> dict[str, object]:
        return {
            "value_usd": self.value_usd,
            "denomination": self.denomination,
            "bills": self.bills,
            "mass_kg": self.mass_kg,
            "volume_m3": self.volume_m3,
            "density_kg_m3": self.density_kg_m3,
            "stage_prices": dict(self.stage_prices),
            "wholesale_per_kg": self.wholesale_per_kg,
            "street_per_gram": self.street_per_gram,
            "street_per_pure_gram": self.street_per_pure_gram,
            "manifest": self.manifest.as_dict(),
            "trips": self.trips,
        }


def analyze_narcotics_finance(
    value_usd: float,
    denomination: float,
    stages: tuple[tuple[str, float], ...],
    purity: float,
    hold_volume_m3: float,
    hold_mass_kg: float,
    base_cost_per_kg: float = 1500.0,
) -> NarcoticsFinanceReport:
    """Run the full narcotics-finance pass over a canonical scenario."""
    stage_prices, _final_per_kg = price_chain(base_cost_per_kg, stages)
    wholesale_per_kg = stage_prices["wholesale"]
    street_per_kg = stage_prices["street"]
    bills = cash_bills(value_usd, denomination)
    mass = cash_mass_kg(value_usd, denomination)
    volume = cash_volume_m3(value_usd, denomination)
    return NarcoticsFinanceReport(
        value_usd=value_usd,
        denomination=denomination,
        bills=bills,
        mass_kg=mass,
        volume_m3=volume,
        density_kg_m3=cash_density_kg_m3(value_usd, denomination),
        stage_prices=stage_prices,
        wholesale_per_kg=wholesale_per_kg,
        street_per_gram=street_per_kg / 1000.0,
        street_per_pure_gram=purity_adjusted_price(street_per_kg / 1000.0, purity),
        manifest=manifest_feasibility(value_usd, denomination, hold_volume_m3, hold_mass_kg),
        trips=trips_required(value_usd, denomination, hold_volume_m3),
    )


def canonical_finance_params() -> dict[str, Any]:
    """Single source of truth for the canonical narcotics-finance scenario.

    Anchored to the film's opening: the intercepted courier flight carries
    ~$5M in $100 bills, and the Wavekrest-class hold (520 m³) is the
    transport constraint. Used by both ``mission.py`` and
    ``manuscript_variables.py`` so outcome results and manuscript tokens can
    never disagree.
    """
    return {
        "value_usd": 5_000_000.0,
        "denomination": 100.0,
        "stages": (("export", 3.0), ("wholesale", 2.0), ("street", 2.0)),
        "base_cost_per_kg": 1500.0,
        "purity": 0.6,
        "hold_volume_m3": 520.0,
        "hold_mass_kg": 300_000.0,
    }
