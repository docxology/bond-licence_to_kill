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
from typing import Any, Mapping, Sequence, cast

import numpy as np
import yaml

from licence_to_kill import CODENAME, FILM, __version__ as VERSION
from licence_to_kill.laundering_graph import (
    LaunderingReport,
    TransactionGraph,
    analyze_laundering,
    build_sanchez_network,
    canonical_laundering_params,
)
from licence_to_kill.narcotics_finance import (
    BILL_MASS_G,
    BILL_VOLUME_CM3,
    NarcoticsFinanceReport,
    analyze_narcotics_finance,
    canonical_finance_params,
)
from licence_to_kill.operations_logistics import (
    OperationNetwork,
    OperationsLogisticsReport,
    analyze_operations_logistics,
    canonical_logistics_params,
    direct_leg,
)
from licence_to_kill.rogue_ops import RogueReport, canonical_rogue_params, solve_optimal_policy
from licence_to_kill.surveillance import (
    EXACT_ORDER_LIMIT,
    SurveillanceReport,
    analyze_surveillance,
    canonical_surveillance_params,
)
from licence_to_kill.vessel_forensics import (
    CARGO_DENSITY_CEILING,
    DIESEL_SFC,
    DISPLACEMENT_TOLERANCE,
    SEAWATER_DENSITY,
    VesselForensicReport,
    canonical_vessel_params,
    forensic_report,
)

__all__ = [
    "compromise_step_label",
    "direct_leg_risk",
    "generate_variables",
    "last_escalation_action",
    "load_mission_config",
    "order_endpoint",
    "project_root",
    "risk_reduction",
    "substitute",
]


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
    """Deterministically recompute the six-domain ROGUE results (typed).

    Every input comes from a ``canonical_*_params()`` single source, the same
    ones ``mission.py`` consumes, so a manuscript token can never disagree
    with the mission outcome it describes.
    """
    laundering_params = canonical_laundering_params()
    vessel_params = canonical_vessel_params()
    rogue_params = canonical_rogue_params()
    finance_params = canonical_finance_params()
    logistics_params = canonical_logistics_params()
    surveillance_params = canonical_surveillance_params()

    graph = build_sanchez_network(seed=int(laundering_params["seed"]))
    launder = analyze_laundering(
        graph,
        laundering_params["sources"],
        laundering_params["sinks"],
        max_depth=int(laundering_params["max_depth"]),
        max_cycles=int(laundering_params["max_cycles"]),
        max_paths=int(laundering_params["max_paths"]),
        funnel_threshold=float(laundering_params["funnel_threshold"]),
    )
    vessel = forensic_report(vessel_params["profile"], observed=vessel_params["observed"])
    rogue = solve_optimal_policy(rogue_params["model"])
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


def direct_leg_risk(network: OperationNetwork, origin: str, destination: str) -> float:
    """Interdiction risk of the direct ``origin → destination`` leg.

    Raises when no such leg exists. The manuscript reports this number as the
    baseline the layered route beats; if the direct leg is gone there is no
    baseline, and substituting a default (the old ``else 1.0``) would
    fabricate a comparison that no input produced. "Absent" and "risk 1.0"
    are different findings — Rule 8.
    """
    leg = direct_leg(network, origin, destination)
    if leg is None:
        raise ValueError(f"no direct leg {origin!r} -> {destination!r}: there is no direct baseline to report")
    return float(leg.risk)


def risk_reduction(direct_risk: float, route_risk: float) -> float:
    """Fractional interdiction-risk reduction of a route against the direct leg.

    ``direct_risk <= 0`` means the direct leg is already risk-free, so there
    is nothing to reduce and the fraction is undefined; it is reported as
    ``0.0`` rather than dividing by zero. Reachable — and reached — by
    ``tests/test_manuscript_variables.py``.
    """
    if direct_risk <= 0.0:
        return 0.0
    return (direct_risk - route_risk) / direct_risk


def last_escalation_action(escalation: Sequence[Mapping[str, Any]]) -> str:
    """Name of the last action in an escalation table (``"none"`` if empty)."""
    if not escalation:
        return "none"
    return str(escalation[-1]["action"])


def compromise_step_label(step: int | None) -> str:
    """One-based label for the compromise step, or ``"never"`` when uncompromised."""
    if step is None:
        return "never"
    return str(step + 1)


def order_endpoint(order: Sequence[str], index: int) -> str:
    """Name at ``index`` of an action order (``"none"`` for an empty order)."""
    if not order:
        return "none"
    return str(order[index])


def generate_variables(now: _dt.datetime | None = None) -> dict[str, str]:
    """Compute the full {{TOKEN}} → value map, deterministically.

    ``now`` is injectable for fully deterministic tests; when omitted the
    current UTC timestamp is used (runtime diagnostic only).
    """
    cfg = load_mission_config()
    paper = cfg.get("paper", {})
    _graph, launder, vessel, rogue, finance, logistics, surveillance = _run_mission_analyses()

    laundering_params = canonical_laundering_params()
    vessel_params = canonical_vessel_params()
    rogue_params = canonical_rogue_params()
    finance_params = canonical_finance_params()
    logistics_params = canonical_logistics_params()
    surveillance_params = canonical_surveillance_params()
    surv_model = surveillance_params["model"]
    vessel_profile = vessel_params["profile"]

    route = logistics.route
    # The direct single leg — the baseline the manuscript compares against.
    network = OperationNetwork(logistics_params["legs"])
    direct_risk = direct_leg_risk(network, logistics.origin, logistics.destination)
    reduction = risk_reduction(direct_risk, route.cumulative_risk)

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
        # laundering search bounds (declared parameters, not results)
        "LAUNDERING_SOURCE_COUNT": str(len(laundering_params["sources"])),
        "LAUNDERING_SINK_COUNT": str(len(laundering_params["sinks"])),
        "LAUNDERING_MAX_DEPTH": str(laundering_params["max_depth"]),
        "LAUNDERING_MAX_CYCLES": str(laundering_params["max_cycles"]),
        "LAUNDERING_MAX_PATHS": str(laundering_params["max_paths"]),
        "LAUNDERING_FUNNEL_THRESHOLD": f"{float(laundering_params['funnel_threshold']):.1f}",
        "LAYERING_WEIGHT_CYCLE": f"{float(laundering_params['layering_weights'][0]):.1f}",
        "LAYERING_WEIGHT_DEPTH": f"{float(laundering_params['layering_weights'][1]):.1f}",
        "LAYERING_WEIGHT_FUNNEL": f"{float(laundering_params['layering_weights'][2]):.1f}",
        # vessel
        "VESSEL_GROSS_TONNAGE": f"{vessel.gross_tonnage:.0f}",
        "VESSEL_HULL_VOLUME": f"{vessel.hull_volume:.0f}",
        "VESSEL_DISPLACEMENT": f"{vessel.predicted_displacement:.0f}",
        "VESSEL_FUEL_TONNES": f"{vessel.fuel_mass_tonnes:.1f}",
        "VESSEL_ENDURANCE_NM": f"{vessel.endurance_nm:.0f}",
        "VESSEL_ANOMALIES": str(len(vessel.anomalies)),
        "VESSEL_ANOMALY_SCORE": f"{vessel.anomaly_score:.1f}",
        # vessel declared parameters + physical constants
        "VESSEL_CARGO_VOLUME_M3": f"{vessel_profile.cargo_volume_m3:.0f}",
        "VESSEL_BLOCK_COEFFICIENT": f"{vessel_profile.block_coefficient:.2f}",
        "VESSEL_MAX_SPEED_KNOTS": f"{vessel_profile.max_speed_knots:.1f}",
        "VESSEL_OBSERVED_CARGO_T": f"{float(vessel_params['observed']['cargo_mass_t']):,.0f}",
        "VESSEL_OBSERVED_DISPLACEMENT_T": f"{float(vessel_params['observed']['declared_displacement_t']):,.0f}",
        "VESSEL_SEAWATER_DENSITY": f"{SEAWATER_DENSITY:.3f}",
        "VESSEL_DIESEL_SFC": f"{DIESEL_SFC:.3f}",
        "VESSEL_CARGO_DENSITY_CEILING": f"{CARGO_DENSITY_CEILING:.1f}",
        "VESSEL_DISPLACEMENT_TOLERANCE": f"{DISPLACEMENT_TOLERANCE:.0%}",
        # rogue
        "ROGUE_HORIZON": str(rogue.horizon),
        "ROGUE_ALERT_MAX": str(rogue.alert_max),
        "ROGUE_OPTIMAL_VALUE": f"{rogue.optimal_value:.3f}",
        "ROGUE_FIRST_ACTION": str(rogue.first_action),
        "ROGUE_LAST_ACTION": last_escalation_action(rogue.escalation),
        # Peak over the alert each action *leaves behind*: the entering-alert
        # column cannot show what the final action did (see RogueReport).
        "ROGUE_PEAK_ALERT": f"{rogue.peak_alert:.1f}",
        "ROGUE_TERMINAL_ALERT": f"{rogue.terminal_alert:.1f}",
        "ROGUE_PEAK_BLOWBACK": f"{rogue.peak_blowback:.3f}",
        "ROGUE_ACTION_CARD": " / ".join(str(a) for a in rogue.actions),
        "ROGUE_POLICY_CELLS": str(rogue.policy_cells),
        "ROGUE_STEALTH_VISIBILITY": f"{float(rogue_params['model'].visibility[0]):.1f}",
        "ROGUE_EXPOSURE_CAP": str(rogue_params["exposure_cap"]),
        "ROGUE_EXPOSURE_CELLS": str(int(rogue_params["exposure_cap"]) + 1),
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
        # finance declared parameters + currency constants
        "FIN_PURITY": f"{float(finance_params['purity']):.0%}",
        "FIN_BASE_COST_PER_KG": f"{float(finance_params['base_cost_per_kg']):,.0f}",
        "FIN_STAGE_LADDER": " → ".join(str(name) for name, _ in finance_params["stages"]),
        "FIN_HOLD_VOLUME_M3": f"{float(finance_params['hold_volume_m3']):,.0f}",
        "FIN_HOLD_MASS_T": f"{float(finance_params['hold_mass_kg']) / 1000.0:,.0f}",
        "FIN_BILL_MASS_G": f"{BILL_MASS_G:.1f}",
        "FIN_BILL_VOLUME_CM3": f"{BILL_VOLUME_CM3:.2f}",
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
        # logistics declared parameters
        "LOG_CAPACITY_KG": f"{float(logistics_params['capacity_kg']):.0f}",
        "LOG_SPEED_KNOTS": f"{float(logistics_params['speed_knots']):.0f}",
        "LOG_ENDURANCE_NM": f"{float(logistics_params['endurance_nm']):,.0f}",
        "LOG_REFUEL_HOURS": f"{float(logistics_params['refuel_hours']):.0f}",
        "LOG_HUB_COUNT": str(len(OperationNetwork(logistics_params["legs"]).nodes())),
        "LOG_NETWORK_LEGS": str(len(logistics_params["legs"])),
        "LOG_GADGET_CANDIDATES": str(len(logistics_params["gadgets"])),
        # surveillance
        "SURV_ACTION_COUNT": str(len(surveillance.optimal_order)),
        "SURV_SUCCESS": f"{surveillance.success_probability:.3f}",
        "SURV_COMPROMISE_STEP_ONE": compromise_step_label(surveillance.compromise_step),
        "SURV_PEAK_HAZARD": f"{surveillance.peak_hazard:.3f}",
        "SURV_FIRST_ACTION": order_endpoint(surveillance.optimal_order, 0),
        "SURV_LAST_ACTION": order_endpoint(surveillance.optimal_order, -1),
        # surveillance declared parameters
        "SURV_THRESHOLD": f"{surv_model.detection_threshold:.2f}",
        "SURV_BETA_0": f"{surv_model.beta_0:.1f}",
        "SURV_BETA_WATCH": f"{surv_model.beta_watch:.1f}",
        "SURV_BETA_SIGNATURE": f"{surv_model.beta_signature:.1f}",
        "SURV_EXACT_LIMIT": str(EXACT_ORDER_LIMIT),
        # environment
        "SEED": str(laundering_params["seed"]),
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
