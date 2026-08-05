"""Manuscript {{TOKEN}} hydration for the ROGUE mission.

Every numeric value that appears in the manuscript prose is injected from
this module's :func:`generate_variables` — it is the single source of truth
so metrics are never hand-authored. Identity tokens come from
``manuscript/config.yaml``; result tokens come from a fresh deterministic run
of the six domain analyses.

The module imports only the pure domain core (not ``bond_api``), so it stays
importable in a fallback environment.
"""

from __future__ import annotations

import datetime as _dt
import platform
from pathlib import Path
from typing import Any, Mapping, cast

import numpy as np
import yaml

from licence_to_kill import CODENAME, FILM, __version__ as VERSION
from licence_to_kill.laundering_graph import (
    LaunderingReport,
    TransactionGraph,
    analyze_laundering,
    build_sanchez_network,
)
from licence_to_kill.narcotics_finance import (
    NarcoticsFinanceReport,
    analyze_narcotics_finance,
    canonical_finance_params,
)
from licence_to_kill.operations_logistics import (
    OperationNetwork,
    OperationsLogisticsReport,
    analyze_operations_logistics,
    canonical_logistics_params,
    shortest_path,
)
from licence_to_kill.rogue_ops import RogueReport, build_rogue_model, solve_optimal_policy
from licence_to_kill.surveillance import (
    SurveillanceReport,
    analyze_surveillance,
    canonical_surveillance_params,
)
from licence_to_kill.vessel_forensics import (
    VesselForensicReport,
    WAVEKREST_CLASS,
    forensic_report,
)

__all__ = ["generate_variables", "load_mission_config", "project_root", "substitute"]

#: Dirty-placement and integration nodes used to drive the analysis.
_SOURCES = ("S1", "S2", "S3")
_SINKS = ("B1", "B2", "B3", "B4")
_SEED = 0

#: Deterministic vessel observations (mirrors mission.py).
_VESSEL_OBSERVED: dict[str, float] = {
    "cargo_mass_t": 900.0,
    "declared_displacement_t": 700.0,
}


def project_root() -> Path:
    """Absolute path of the package root (``.../bond/licence_to_kill``)."""
    return Path(__file__).resolve().parents[2]


def load_mission_config(root: Path | None = None) -> dict[str, Any]:
    """Load ``manuscript/config.yaml`` from the package root."""
    root = root or project_root()
    path = root / "manuscript" / "config.yaml"
    with open(path, "r", encoding="utf-8") as handle:
        return cast("dict[str, Any]", yaml.safe_load(handle))


def _run_mission_analyses() -> tuple[
    TransactionGraph,
    LaunderingReport,
    VesselForensicReport,
    RogueReport,
    NarcoticsFinanceReport,
    OperationsLogisticsReport,
    SurveillanceReport,
]:
    """Deterministically recompute the six-domain ROGUE results (typed)."""
    finance_params = canonical_finance_params()
    logistics_params = canonical_logistics_params()
    surveillance_params = canonical_surveillance_params()

    graph = build_sanchez_network(seed=_SEED)
    launder = analyze_laundering(graph, _SOURCES, _SINKS)
    vessel = forensic_report(WAVEKREST_CLASS, observed=_VESSEL_OBSERVED)
    rogue = solve_optimal_policy(build_rogue_model())
    finance = analyze_narcotics_finance(**finance_params)
    network = OperationNetwork(logistics_params["legs"])
    logistics = analyze_operations_logistics(
        network,
        str(logistics_params["origin"]),
        str(logistics_params["destination"]),
        logistics_params["gadgets"],
        float(logistics_params["capacity_kg"]),
        float(logistics_params["speed_knots"]),
        float(logistics_params["endurance_nm"]),
        float(logistics_params["refuel_hours"]),
    )
    surveillance = analyze_surveillance(
        surveillance_params["actions"],
        surveillance_params["model"],
    )
    return graph, launder, vessel, rogue, finance, logistics, surveillance


def generate_variables(now: _dt.datetime | None = None) -> dict[str, str]:
    """Compute the full {{TOKEN}} → value map, deterministically.

    ``now`` is injectable for fully deterministic tests; when omitted the
    current UTC timestamp is used (runtime diagnostic only).
    """
    cfg = load_mission_config()
    paper = cfg.get("paper", {})
    _graph, launder, vessel, rogue, finance, logistics, surveillance = _run_mission_analyses()

    route = logistics.route
    # Direct single-leg route for the self-gauging risk reduction metric.
    network = OperationNetwork(canonical_logistics_params()["legs"])
    direct = shortest_path(
        network,
        logistics.origin,
        logistics.destination,
        weight="distance",
    )
    direct_risk = float(direct.cumulative_risk) if direct is not None else 1.0
    reduction = (direct_risk - route.cumulative_risk) / direct_risk if direct_risk > 0.0 else 0.0

    stamp = (now or _dt.datetime.now(_dt.timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "BOND_TITLE": str(paper.get("title", "")),
        "BOND_SUBTITLE": str(paper.get("subtitle", "")),
        "BOND_VERSION": str(paper.get("version", VERSION)),
        "BOND_FILM": FILM,
        "BOND_CODENAME": CODENAME,
        # laundering
        "LAUNDERING_NODES": str(launder.num_nodes),
        "LAUNDERING_EDGES": str(launder.num_edges),
        "LAUNDERING_CYCLES": str(len(launder.cycles)),
        "LAUNDERING_FUNNELS": str(len(launder.funnels)),
        "LAUNDERING_PATHS": str(len(launder.layering_paths)),
        "LAYERING_SCORE": f"{launder.layering_score:.3f}",
        "INTEGRATION_SCORE": f"{launder.integration_score:.3f}",
        "MIXING_ENTROPY": f"{launder.mixing_entropy:.3f}",
        "PLACEMENT": f"{launder.placement:.1f}",
        # vessel
        "VESSEL_GROSS_TONNAGE": f"{vessel.gross_tonnage:.0f}",
        "VESSEL_HULL_VOLUME": f"{vessel.hull_volume:.0f}",
        "VESSEL_DISPLACEMENT": f"{vessel.predicted_displacement:.0f}",
        "VESSEL_FUEL_TONNES": f"{vessel.fuel_mass_tonnes:.1f}",
        "VESSEL_ENDURANCE_NM": f"{vessel.endurance_nm:.0f}",
        "VESSEL_ANOMALIES": str(len(vessel.anomalies)),
        "VESSEL_ANOMALY_SCORE": f"{vessel.anomaly_score:.1f}",
        # rogue
        "ROGUE_HORIZON": str(rogue.horizon),
        "ROGUE_ALERT_MAX": str(rogue.alert_max),
        "ROGUE_OPTIMAL_VALUE": f"{rogue.optimal_value:.3f}",
        "ROGUE_FIRST_ACTION": str(rogue.first_action),
        "ROGUE_PEAK_BLOWBACK": f"{rogue.peak_blowback:.3f}",
        "ROGUE_ACTION_CARD": " / ".join(str(a) for a in rogue.actions),
        "ROGUE_POLICY_CELLS": str(rogue.policy_cells),
        # narcotics finance
        "FIN_VALUE_USD": f"{finance.value_usd:,.0f}",
        "FIN_DENOMINATION": f"{finance.denomination:.0f}",
        "FIN_BILLS": f"{finance.bills:,.0f}",
        "FIN_CASH_MASS_KG": f"{finance.mass_kg:.1f}",
        "FIN_CASH_VOLUME_M3": f"{finance.volume_m3:.4f}",
        "FIN_CASH_DENSITY": f"{finance.density_kg_m3:.0f}",
        "FIN_WHOLESALE_PER_KG": f"{finance.wholesale_per_kg:,.0f}",
        "FIN_STREET_PER_KG": f"{finance.street_per_gram * 1000:,.0f}",
        "FIN_STREET_PER_GRAM": f"{finance.street_per_gram:.0f}",
        "FIN_STREET_PURE_GRAM": f"{finance.street_per_pure_gram:.0f}",
        "FIN_MANIFEST_FEASIBLE": "yes" if finance.manifest.feasible else "no",
        "FIN_TRIPS": str(finance.trips),
        # operations logistics
        "LOG_ORIGIN": str(logistics.origin),
        "LOG_DESTINATION": str(logistics.destination),
        "LOG_ROUTE": " → ".join(route.path),
        "LOG_ROUTE_LEGS": str(len(route.legs)),
        "LOG_ROUTE_RISK": f"{route.cumulative_risk:.3f}",
        "LOG_ROUTE_COST": f"{route.total_cost:,.0f}",
        "LOG_ROUTE_NM": f"{route.total_distance_nm:,.0f}",
        "LOG_DIRECT_RISK": f"{direct_risk:.3f}",
        "LOG_RISK_REDUCTION": f"{reduction:.1%}",
        "LOG_REFUELS": str(logistics.trip.refuels),
        "LOG_TRIP_HOURS": f"{logistics.trip.total_hours:,.0f}",
        "LOG_TRIP_DAYS": f"{logistics.trip.total_hours / 24.0:.0f}",
        "LOG_KNAPSACK_ITEMS": str(len(logistics.loadout.names)),
        "LOG_KNAPSACK_VALUE": f"{logistics.loadout.value:.0f}",
        "LOG_KNAPSACK_WEIGHT": f"{logistics.loadout.weight_kg:.1f}",
        # surveillance
        "SURV_ACTION_COUNT": str(len(surveillance.optimal_order)),
        "SURV_SUCCESS": f"{surveillance.success_probability:.3f}",
        "SURV_COMPROMISE_STEP_ONE": (
            str(surveillance.compromise_step + 1) if surveillance.compromise_step is not None else "never"
        ),
        "SURV_PEAK_HAZARD": f"{surveillance.peak_hazard:.3f}",
        "SURV_FIRST_ACTION": str(surveillance.optimal_order[0]) if surveillance.optimal_order else "none",
        # environment
        "SEED": str(_SEED),
        "PYTHON_VERSION": platform.python_version(),
        "NUMPY_VERSION": np.__version__,
        "GENERATION_TIMESTAMP": stamp,
    }


def substitute(text: str, tokens: Mapping[str, str]) -> str:
    """Replace every ``{{TOKEN}}`` in ``text`` with its resolved value.

    Tokens that are present in the text but absent from the mapping are left
    verbatim so the caller can detect unresolved placeholders.
    """
    resolved = text
    for key, value in tokens.items():
        resolved = resolved.replace("{{" + key + "}}", str(value))
    return resolved
