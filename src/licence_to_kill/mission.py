"""mission.py — the ROGUE MissionProvider adapter for licence_to_kill.

This is the thin protocol adapter between the pure domain core
(:mod:`laundering_graph`, :mod:`vessel_forensics`, :mod:`rogue_ops`) and the
FROZEN ``bond-api`` contract. Discovery (``bond_api.discovery``) imports
``licence_to_kill.mission``, instantiates ``MissionProvider()`` with no args,
and drives the five lifecycle stages.

Only this module imports ``bond_api``; the domain core stays importable
without it (fallback if the path dependency ever fails).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from licence_to_kill import CODENAME, FILM, __version__ as _PACKAGE_VERSION
from licence_to_kill.laundering_graph import (
    LaunderingReport,
    TransactionGraph,
    analyze_laundering,
    build_sanchez_network,
)
from licence_to_kill.rogue_ops import (
    RogueModel,
    RogueReport,
    build_rogue_model,
    solve_optimal_policy,
)
from licence_to_kill.vessel_forensics import (
    VesselForensicReport,
    WAVEKREST_CLASS,
    forensic_report,
)

__all__ = ["GADGET_REGISTRY", "MissionProvider", "run_rogue_mission"]

#: Deterministic seed for the whole ROGUE run (0 disables randomness).
_SEED = 0

#: The dirty-placement (source) nodes in the canonical Sanchez network.
_SOURCES = ("S1", "S2", "S3")
#: The integration (bank) sink nodes.
_SINKS = ("B1", "B2", "B3", "B4")

#: Deterministic vessel observations that expose covert modification
#: (implausibly dense cargo + draft/displacement mismatch → hidden contraband).
_VESSEL_OBSERVED: dict[str, float] = {
    "cargo_mass_t": 900.0,
    "declared_displacement_t": 700.0,
}

#: The canonical rogue risk model (horizon used by plan + recon).
_ROGUE_MODEL: RogueModel = build_rogue_model()


def _input_hash(graph: TransactionGraph) -> str:
    """Stable fingerprint of the mission's canonical inputs."""
    payload: dict[str, object] = {
        "seed": _SEED,
        "sources": list(_SOURCES),
        "sinks": list(_SINKS),
        "nodes": list(graph.nodes()),
        "edges": [{"s": e.source, "t": e.target, "a": e.amount, "x": e.sector} for e in graph.edges()],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: Gadgets this film registers with the BOND-API GadgetRegistry (opaque,
#: deterministic callables + the canonical network manifest).
GADGET_REGISTRY = GadgetRegistry()
GADGET_REGISTRY.register(
    FILM,
    {
        "laundering_analyzer": analyze_laundering,
        "laundering_network": build_sanchez_network,
        "vessel_forensics": forensic_report,
        "rogue_risk_model": solve_optimal_policy,
        "network_manifest": {
            "sources": list(_SOURCES),
            "sinks": list(_SINKS),
            "seed": _SEED,
        },
    },
)


def _run_domain_analyses() -> tuple[TransactionGraph, LaunderingReport, VesselForensicReport, RogueReport]:
    """Deterministically run the three domain analyses on canonical inputs."""
    graph = build_sanchez_network(seed=_SEED)
    launder = analyze_laundering(graph, _SOURCES, _SINKS)
    vessel = forensic_report(WAVEKREST_CLASS, observed=_VESSEL_OBSERVED)
    rogue = solve_optimal_policy(_ROGUE_MODEL)
    return graph, launder, vessel, rogue


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """Deterministic BOND-API provider for the ROGUE (Licence to Kill) mission."""

    film = FILM

    @staticmethod
    def _brief_assets() -> tuple[Asset, ...]:
        graph = build_sanchez_network(seed=_SEED)
        return (
            Asset(
                kind="network",
                name="sanchez_graph",
                payload={
                    "sources": list(_SOURCES),
                    "sinks": list(_SINKS),
                    "seed": _SEED,
                    "nodes": list(graph.nodes()),
                    "edges": len(graph.edges()),
                },
            ),
            Asset(
                kind="vessel",
                name="wavekrest_class",
                payload={
                    "name": WAVEKREST_CLASS.name,
                    "length_m": WAVEKREST_CLASS.length_m,
                    "fuel_capacity_m3": WAVEKREST_CLASS.fuel_capacity_m3,
                },
            ),
            Asset(
                kind="risk",
                name="rogue_model",
                payload={
                    "horizon": _ROGUE_MODEL.horizon,
                    "actions": list(_ROGUE_MODEL.actions),
                },
            ),
        )

    def brief(self) -> MissionBrief:
        """Declare the ROGUE mission: three objectives over the three domains."""
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "detect layering and integration in the Sanchez money-laundering network",
                "forensic anomaly scan of the Wavekrest-class mothership",
                "risk-optimised rogue-00 engagement plan under a revoked licence",
            ),
            assets=self._brief_assets(),
            constraints=(
                Constraint(
                    kind="determinism",
                    detail="no random draws, no external calls, no wall-clock in persisted outputs",
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the ROGUE domains against the canonical assets and the goal."""
        _, launder, vessel, rogue = _run_domain_analyses()
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="layering",
                    detail=(
                        f"layering_score={launder.layering_score:.3f} "
                        f"cycles={len(launder.cycles)} funnels={len(launder.funnels)}"
                    ),
                ),
                Finding(
                    label="integration",
                    detail=(
                        f"integration_score={launder.integration_score:.3f} mixing_entropy={launder.mixing_entropy:.3f}"
                    ),
                ),
                Finding(
                    label="vessel",
                    detail=(f"gross_tonnage={vessel.gross_tonnage:.0f} anomalies={len(vessel.anomalies)}"),
                ),
                Finding(
                    label="rogue",
                    detail=(f"optimal_value={rogue.optimal_value:.3f} first_action={rogue.first_action}"),
                ),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the four deterministic steps matching the mission objectives."""
        return MissionPlan(
            steps=(
                Step(
                    "network",
                    "analyze_laundering",
                    params={"sources": _SOURCES, "sinks": _SINKS, "objectives": len(brief.objectives)},
                ),
                Step("vessel", "forensic_scan", params={"profile": WAVEKREST_CLASS.name}),
                Step("rogue", "solve_optimal_policy", params={"horizon": _ROGUE_MODEL.horizon}),
                Step("verify", "cross_check_determinism", params={"seed": _SEED}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the full deterministic ROGUE analysis and return its outcome."""
        graph, launder, vessel, rogue = _run_domain_analyses()
        results: dict[str, Any] = {
            "steps_completed": len(plan.steps),
            "outputs": tuple(step.name for step in plan.steps),
            "seed": _SEED,
            "input_hash": _input_hash(graph),
            "laundering": launder.as_dict(),
            "vessel": vessel.as_dict(),
            "rogue": rogue.as_dict(),
        }
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_SEED,
                input_hash=str(results["input_hash"]),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarise the mission and record the ROGUE standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "layering is detectable as cyclic + funnel imbalance in the flow graph",
                "a 'fishing' mothership's physics betray covert cargo before its crew does",
                "a revoked licence trades gain against escalating blowback — the DP finds the optimum",
                "deterministic provenance makes every ROGUE result independently audit-able",
            ),
        )


def run_rogue_mission(request: ReconRequest) -> Debrief:
    """Convenience entry: drive the full five-stage flow on a fresh provider."""
    from bond_api.protocol import run_mission

    return run_mission(MissionProvider(), request)
