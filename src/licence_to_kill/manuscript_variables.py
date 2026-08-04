"""Manuscript {{TOKEN}} hydration for the ROGUE mission.

Every numeric value that appears in the manuscript prose is injected from
this module's :func:`generate_variables` — it is the single source of truth
so metrics are never hand-authored. Identity tokens come from
``manuscript/config.yaml``; result tokens come from a fresh deterministic run
of the three domain analyses.

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
from licence_to_kill.rogue_ops import RogueReport, build_rogue_model, solve_optimal_policy
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


def _run_mission_analyses() -> tuple[TransactionGraph, LaunderingReport, VesselForensicReport, RogueReport]:
    """Deterministically recompute the three-domain ROGUE results (typed)."""
    graph = build_sanchez_network(seed=_SEED)
    launder = analyze_laundering(graph, _SOURCES, _SINKS)
    vessel = forensic_report(WAVEKREST_CLASS, observed=_VESSEL_OBSERVED)
    rogue = solve_optimal_policy(build_rogue_model())
    return graph, launder, vessel, rogue


def generate_variables(now: _dt.datetime | None = None) -> dict[str, str]:
    """Compute the full {{TOKEN}} → value map, deterministically.

    ``now`` is injectable for fully deterministic tests; when omitted the
    current UTC timestamp is used (runtime diagnostic only).
    """
    cfg = load_mission_config()
    paper = cfg.get("paper", {})
    _graph, launder, vessel, rogue = _run_mission_analyses()

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
