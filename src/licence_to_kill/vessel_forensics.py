"""Wavekrest-class vessel forensics — anomaly detection from marine physics.

The ROGUE mission's second domain: given a declared ``VesselProfile`` of the
Wavekrest-class mothership used to smuggle the Sanchez proceeds, compute
first-principles physical quantities (enclosed hull volume, gross tonnage,
draft-displacement relation, fuel endurance, route-speed plausibility) and
flag inconsistencies that indicate covert modification — hidden holds,
overloaded displacement, or suicidal fuel/range economics that only make
sense if the vessel is not really a fishing boat.

Everything is deterministic analytic math (no RNG, no wall-clock): the IMO
gross-tonnage convention @IMO1969, the cubic propulsion-power law, diesel
specific fuel consumption, and seawater density.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

__all__ = [
    "CARGO_DENSITY_CEILING",
    "DIESEL_DENSITY",
    "DIESEL_SFC",
    "DISPLACEMENT_TOLERANCE",
    "POWER_DENSITY_CEILING",
    "SEAWATER_DENSITY",
    "VesselForensicReport",
    "VesselProfile",
    "WAVEKREST_CLASS",
    "anomaly_scan",
    "canonical_vessel_params",
    "displacement_from_draft",
    "endurance_range_nm",
    "forensic_report",
    "fuel_consumption_kgph",
    "fuel_mass_tonnes",
    "gross_tonnage",
    "hull_volume",
    "propulsion_power_at_speed",
    "route_average_speed_knots",
    "route_plausibility",
]

#: Seawater density, tonnes per cubic metre (≈ 1.025 t/m³).
SEAWATER_DENSITY = 1.025
#: Marine-diesel density, tonnes per cubic metre (≈ 0.85 t/m³).
DIESEL_DENSITY = 0.85
#: Brake specific fuel consumption of a marine diesel, kg per kWh (≈ 0.195).
DIESEL_SFC = 0.195
#: Knots per (km/h) conversion factor.
KMH_PER_KNOT = 1.852
#: Gross-tonnage empirical parameter K1 (IMO formula K1 = 0.2 + 0.02 log10 V).
_GT_K1_BASE = 0.2
_GT_K1_FACTOR = 0.02
#: Bulk-density ceiling for boxed fish, t/m³ — above this the cargo is not fish.
CARGO_DENSITY_CEILING = 1.4
#: Allowed relative gap between declared and draft-predicted displacement.
DISPLACEMENT_TOLERANCE = 0.15
#: Installed-power ceiling for a genuine fishing hull, kW per m³ of hull volume.
POWER_DENSITY_CEILING = 2.0


@dataclass(frozen=True)
class VesselProfile:
    """Declared physical dimensions and machinery of a fishing-class mothership."""

    name: str
    length_m: float
    beam_m: float
    depth_m: float
    draft_m: float
    engine_kw: float
    fuel_capacity_m3: float
    cargo_volume_m3: float
    max_speed_knots: float
    block_coefficient: float = 0.60
    home_port: str = ""


#: Canonical Wavekrest-class deep-sea trawler / mothership profile.
WAVEKREST_CLASS = VesselProfile(
    name="Wavekrest",
    length_m=48.0,
    beam_m=9.5,
    depth_m=4.8,
    draft_m=3.4,
    engine_kw=1200.0,
    fuel_capacity_m3=60.0,
    cargo_volume_m3=520.0,
    max_speed_knots=12.5,
    block_coefficient=0.62,
    home_port="Hong Kong",
)


def hull_volume(profile: VesselProfile) -> float:
    """Enclosed moulded volume estimate V = L·B·D·Cb (m³)."""
    return profile.length_m * profile.beam_m * profile.depth_m * profile.block_coefficient


def gross_tonnage(profile: VesselProfile) -> float:
    """IMO 1969 gross tonnage: GT = K1·V with K1 = 0.2 + 0.02·log10(V)."""
    volume = hull_volume(profile)
    if volume <= 0.0:
        raise ValueError("hull volume must be positive to compute gross tonnage")
    k1 = _GT_K1_BASE + _GT_K1_FACTOR * math.log10(volume)
    return k1 * volume


def displacement_from_draft(profile: VesselProfile, draft_m: float | None = None) -> float:
    """Hydrostatic displacement (t) for a given draft: ρ·L·B·draft·Cb."""
    draft = profile.draft_m if draft_m is None else draft_m
    return SEAWATER_DENSITY * profile.length_m * profile.beam_m * draft * profile.block_coefficient


def fuel_mass_tonnes(profile: VesselProfile) -> float:
    """Usable fuel mass (t) from tank capacity and marine-diesel density."""
    return profile.fuel_capacity_m3 * DIESEL_DENSITY


def propulsion_power_at_speed(profile: VesselProfile, speed_knots: float) -> float:
    """Required shaft power (kW) at a given speed via the cubic law."""
    if speed_knots < 0.0:
        raise ValueError("speed must be non-negative")
    if profile.max_speed_knots <= 0.0:
        raise ValueError("max_speed_knots must be positive")
    ratio = min(speed_knots / profile.max_speed_knots, 1.0)
    return profile.engine_kw * (ratio**3)


def fuel_consumption_kgph(profile: VesselProfile, speed_knots: float) -> float:
    """Instantaneous fuel burn (kg/h) at speed: P_kW × SFC."""
    return propulsion_power_at_speed(profile, speed_knots) * DIESEL_SFC


def endurance_range_nm(profile: VesselProfile, speed_knots: float | None = None) -> float:
    """Maximum range (nautical miles) on full tanks at cruise speed."""
    cruise = 0.8 * profile.max_speed_knots if speed_knots is None else speed_knots
    burn_kg_per_h = fuel_consumption_kgph(profile, cruise)
    if burn_kg_per_h <= 0.0:
        return 0.0
    fuel_kg = fuel_mass_tonnes(profile) * 1000.0
    return fuel_kg / burn_kg_per_h * cruise


def route_average_speed_knots(distance_nm: float, duration_h: float) -> float:
    """Average speed (knots) required to cover ``distance_nm`` in ``duration_h``."""
    if duration_h <= 0.0:
        raise ValueError("duration_h must be positive")
    if distance_nm < 0.0:
        raise ValueError("distance_nm must be non-negative")
    return distance_nm / duration_h


def route_plausibility(
    profile: VesselProfile,
    distance_nm: float,
    duration_h: float,
    tolerance: float = 0.0,
) -> tuple[bool, float, str]:
    """Return ``(plausible, required_speed_knots, reason)`` for a declared route."""
    required = route_average_speed_knots(distance_nm, duration_h)
    ceiling = profile.max_speed_knots * (1.0 + tolerance)
    if required > ceiling:
        return False, required, "required average speed exceeds vessel capability"
    return True, required, "route speed is physically achievable"


def anomaly_scan(
    profile: VesselProfile,
    observed: Mapping[str, float] | None = None,
    distance_nm: float | None = None,
    duration_h: float | None = None,
) -> tuple[tuple[str, ...], float]:
    """First-principles inconsistency checks; return flagged anomalies + score.

    Lower bound of anomaly-score is normalised so that a clean vessel ≈ 0 and
    every flagged check adds a unit weight.

    Raises:
        ValueError: if ``distance_nm``/``duration_h`` are supplied and the
            profile cannot support an endurance computation (non-positive
            ``max_speed_knots``) or the declared duration is non-positive.
    """
    obs: dict[str, float] = dict(observed or {})
    flags: list[str] = []
    score = 0.0

    # 1. Cargo bulk-density plausibility (contraband is denser than fish).
    if "cargo_mass_t" in obs:
        density = obs["cargo_mass_t"] / profile.cargo_volume_m3 if profile.cargo_volume_m3 > 0 else 0.0
        if density > CARGO_DENSITY_CEILING:
            flags.append(f"implausibly dense cargo ({density:.2f} t/m3) — not boxed fish")
            score += 1.0

    # 2. Draft/displacement mismatch (hidden ballast/contraband displaces more).
    if "declared_displacement_t" in obs:
        predicted = displacement_from_draft(profile)
        declared = obs["declared_displacement_t"]
        if abs(declared - predicted) / max(predicted, 1e-9) > DISPLACEMENT_TOLERANCE:
            flags.append(
                f"declared displacement {declared:.0f} t differs "
                f">{DISPLACEMENT_TOLERANCE:.0%} from draft-predicted {predicted:.0f} t"
            )
            score += 1.0

    # 3. Endurance vs a declared voyage (fuel must cover distance).
    #
    # ``endurance_range_nm`` is called unguarded on purpose: it raises
    # ``ValueError`` only for a structurally invalid profile (non-positive
    # ``max_speed_knots``), and a forensic scan must not silently downgrade an
    # invalid profile to "no endurance anomaly". ``forensic_report`` calls the
    # same function unguarded, so swallowing here would only make
    # ``anomaly_scan`` disagree with the report built from it.
    if distance_nm is not None and duration_h is not None:
        plausible, _, reason = route_plausibility(profile, distance_nm, duration_h)
        if not plausible:
            flags.append(reason)
            score += 1.5
        endurance = endurance_range_nm(profile)
        if endurance > 0.0 and distance_nm > endurance:
            flags.append(f"declared voyage {distance_nm:.0f} nm exceeds fuel endurance {endurance:.0f} nm")
            score += 1.5

    # 4. Engine power anomaly: a real trawler is not over-horsepowered for its hull.
    power_density = profile.engine_kw / hull_volume(profile) if hull_volume(profile) > 0 else 0.0
    if power_density > POWER_DENSITY_CEILING:
        flags.append(f"high power density ({power_density:.2f} kW/m3) for a fishing hull")
        score += 1.0

    return tuple(flags), score


@dataclass(frozen=True)
class VesselForensicReport:
    """Deterministic forensic summary for one vessel profile."""

    profile_name: str
    hull_volume: float
    gross_tonnage: float
    predicted_displacement: float
    fuel_mass_tonnes: float
    endurance_nm: float
    anomalies: tuple[str, ...]
    anomaly_score: float

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_name": self.profile_name,
            "hull_volume": self.hull_volume,
            "gross_tonnage": self.gross_tonnage,
            "predicted_displacement": self.predicted_displacement,
            "fuel_mass_tonnes": self.fuel_mass_tonnes,
            "endurance_nm": self.endurance_nm,
            "num_anomalies": len(self.anomalies),
            "anomalies": list(self.anomalies),
            "anomaly_score": self.anomaly_score,
        }


def forensic_report(
    profile: VesselProfile,
    observed: Mapping[str, float] | None = None,
    distance_nm: float | None = None,
    duration_h: float | None = None,
) -> VesselForensicReport:
    """Full first-principles forensic pass over a vessel profile."""
    anomalies, score = anomaly_scan(profile, observed, distance_nm, duration_h)
    return VesselForensicReport(
        profile_name=profile.name,
        hull_volume=hull_volume(profile),
        gross_tonnage=gross_tonnage(profile),
        predicted_displacement=displacement_from_draft(profile),
        fuel_mass_tonnes=fuel_mass_tonnes(profile),
        endurance_nm=endurance_range_nm(profile),
        anomalies=anomalies,
        anomaly_score=score,
    )


def canonical_vessel_params() -> dict[str, Any]:
    """Single source of truth for the canonical Wavekrest-class forensic case.

    The observed quantities are the two that expose covert modification in
    the film: a hold far denser than boxed fish, and a declared displacement
    well below the draft-predicted value. Mirrors the ``mission.vessel``
    block of ``manuscript/config.yaml`` (bound by
    ``tests/test_canonical_params.py``) and is consumed by ``mission.py``,
    ``manuscript_variables.py``, and ``figures/plots.py``.
    """
    return {
        "profile": WAVEKREST_CLASS,
        "observed": {
            "cargo_mass_t": 900.0,
            "declared_displacement_t": 700.0,
        },
    }
