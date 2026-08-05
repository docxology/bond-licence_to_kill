"""mission.py — the ROGUE MissionProvider adapter for licence_to_kill.

This is the thin protocol adapter between the pure domain core
(:mod:`laundering_graph`, :mod:`vessel_forensics`, :mod:`rogue_ops`,
:mod:`narcotics_finance`, :mod:`operations_logistics`, :mod:`surveillance`)
and the FROZEN ``bond-api`` contract. Discovery (``bond_api.discovery``)
imports ``licence_to_kill.mission``, instantiates ``MissionProvider()`` with
no args, and drives the five lifecycle stages.

Only this module imports ``bond_api``; the domain core stays importable
without it (fallback if the path dependency ever fails).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from typing import Any, Mapping

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
    canonical_laundering_params,
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
)
from licence_to_kill.rogue_ops import RogueModel, RogueReport, canonical_rogue_params, solve_optimal_policy
from licence_to_kill.surveillance import (
    CovertAction,
    SurveillanceModel,
    SurveillanceReport,
    analyze_surveillance,
    canonical_surveillance_params,
)
from licence_to_kill.vessel_forensics import (
    VesselForensicReport,
    VesselProfile,
    canonical_vessel_params,
    forensic_report,
)

__all__ = ["GADGET_REGISTRY", "MissionProvider", "canonical_domain_inputs", "run_rogue_mission"]

#: Canonical scenarios for all six domains — every constant used below comes
#: from a ``canonical_*_params()`` single source shared with
#: ``manuscript_variables.py`` and ``figures/plots.py``, so the three consumers
#: cannot drift apart (bound by ``tests/test_canonical_params.py``).
_LAUNDERING = canonical_laundering_params()
_VESSEL = canonical_vessel_params()
_ROGUE = canonical_rogue_params()
_FINANCE = canonical_finance_params()
_LOGISTICS = canonical_logistics_params()
_SURVEILLANCE = canonical_surveillance_params()

#: Deterministic seed for the whole ROGUE run (0 disables randomness).
_SEED: int = int(_LAUNDERING["seed"])

#: The dirty-placement (source) nodes in the canonical Sanchez network.
_SOURCES: tuple[str, ...] = _LAUNDERING["sources"]
#: The integration (bank) sink nodes.
_SINKS: tuple[str, ...] = _LAUNDERING["sinks"]

#: Canonical vessel profile and the deterministic observations that expose
#: covert modification (dense cargo + draft/displacement mismatch).
_VESSEL_PROFILE: VesselProfile = _VESSEL["profile"]
_VESSEL_OBSERVED: dict[str, float] = _VESSEL["observed"]

#: The canonical rogue risk model (horizon used by plan + recon).
_ROGUE_MODEL: RogueModel = _ROGUE["model"]
_LOGISTICS_NETWORK = OperationNetwork(_LOGISTICS["legs"])
_ACTIONS: tuple[CovertAction, ...] = _SURVEILLANCE["actions"]
_SURV_MODEL: SurveillanceModel = _SURVEILLANCE["model"]


def canonical_domain_inputs() -> dict[str, dict[str, Any]]:
    """The six canonical parameter dicts, keyed by domain.

    One place, so :func:`_input_hash` cannot silently omit a domain: it hashes
    whatever this returns. A parameter added to any ``canonical_*_params()``
    enters the provenance hash automatically.
    """
    return {
        "laundering": _LAUNDERING,
        "vessel": _VESSEL,
        "rogue": _ROGUE,
        "finance": _FINANCE,
        "logistics": _LOGISTICS,
        "surveillance": _SURVEILLANCE,
    }


def _jsonable(value: Any) -> Any:
    """Recursively convert canonical parameters to JSON-serialisable values.

    Handles the frozen dataclasses the domains declare (``VesselProfile``,
    ``RogueModel``, ``MissionLeg``, ``GadgetItem``, ``CovertAction``,
    ``SurveillanceModel``), mappings, and sequences. Anything else is passed
    through and will raise loudly in :func:`json.dumps` rather than be dropped
    — an un-hashable input must fail, not vanish from the fingerprint.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _input_hash(graph: TransactionGraph, domains: Mapping[str, Any] | None = None) -> str:
    """Stable sha256 fingerprint of the mission's canonical inputs.

    Covers the built transaction graph *and* every parameter of all six
    canonical domain scenarios. ``domains`` is injectable so
    ``tests/test_mission.py::test_input_hash_covers_every_domain`` can mutate
    one domain at a time and prove the hash actually responds — the gate that
    was missing when this hash silently omitted the vessel and rogue domains.
    """
    payload: dict[str, object] = {
        "graph": {
            "nodes": list(graph.nodes()),
            "edges": [{"s": e.source, "t": e.target, "a": e.amount, "x": e.sector} for e in graph.edges()],
        },
        "domains": _jsonable(canonical_domain_inputs() if domains is None else domains),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: Gadgets this film registers with the BOND-API GadgetRegistry (opaque,
#: deterministic callables + canonical manifests).
GADGET_REGISTRY = GadgetRegistry()
GADGET_REGISTRY.register(
    FILM,
    {
        "laundering_analyzer": analyze_laundering,
        "laundering_network": build_sanchez_network,
        "vessel_forensics": forensic_report,
        "rogue_risk_model": solve_optimal_policy,
        "narcotics_finance": analyze_narcotics_finance,
        "operations_router": analyze_operations_logistics,
        "surveillance_model": analyze_surveillance,
        "network_manifest": {
            "sources": list(_SOURCES),
            "sinks": list(_SINKS),
            "seed": _SEED,
        },
    },
)


def _run_domain_analyses() -> tuple[
    TransactionGraph,
    LaunderingReport,
    VesselForensicReport,
    RogueReport,
    NarcoticsFinanceReport,
    OperationsLogisticsReport,
    SurveillanceReport,
]:
    """Deterministically run all six domain analyses on canonical inputs."""
    graph = build_sanchez_network(seed=_SEED)
    launder = analyze_laundering(
        graph,
        _SOURCES,
        _SINKS,
        max_depth=int(_LAUNDERING["max_depth"]),
        max_cycles=int(_LAUNDERING["max_cycles"]),
        max_paths=int(_LAUNDERING["max_paths"]),
        funnel_threshold=float(_LAUNDERING["funnel_threshold"]),
    )
    vessel = forensic_report(_VESSEL_PROFILE, observed=_VESSEL_OBSERVED)
    rogue = solve_optimal_policy(_ROGUE_MODEL)
    finance = analyze_narcotics_finance(**_FINANCE)
    logistics = analyze_operations_logistics(
        _LOGISTICS_NETWORK,
        str(_LOGISTICS["origin"]),
        str(_LOGISTICS["destination"]),
        _LOGISTICS["gadgets"],
        float(_LOGISTICS["capacity_kg"]),
        float(_LOGISTICS["speed_knots"]),
        float(_LOGISTICS["endurance_nm"]),
        float(_LOGISTICS["refuel_hours"]),
    )
    surveillance = analyze_surveillance(_ACTIONS, _SURV_MODEL)
    return graph, launder, vessel, rogue, finance, logistics, surveillance


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
                    "name": _VESSEL_PROFILE.name,
                    "length_m": _VESSEL_PROFILE.length_m,
                    "fuel_capacity_m3": _VESSEL_PROFILE.fuel_capacity_m3,
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
            Asset(
                kind="finance",
                name="narcotics_manifest",
                payload={
                    "value_usd": _FINANCE["value_usd"],
                    "denomination": _FINANCE["denomination"],
                    "stages": [str(s) for s in _FINANCE["stages"]],
                },
            ),
            Asset(
                kind="logistics",
                name="operations_network",
                payload={
                    "origin": _LOGISTICS["origin"],
                    "destination": _LOGISTICS["destination"],
                    "legs": len(_LOGISTICS["legs"]),
                    "capacity_kg": _LOGISTICS["capacity_kg"],
                },
            ),
            Asset(
                kind="surveillance",
                name="watchlist_model",
                payload={
                    "actions": len(_ACTIONS),
                    "threshold": _SURV_MODEL.detection_threshold,
                },
            ),
        )

    def brief(self) -> MissionBrief:
        """Declare the ROGUE mission: six objectives across the six domains."""
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "detect layering and integration in the Sanchez money-laundering network",
                "forensic anomaly scan of the Wavekrest-class mothership",
                "risk-optimised rogue-00 engagement plan under a revoked licence",
                "quantify narcotics-finance economics and cash-manifest feasibility",
                "route the operation and select the gadget loadout under risk and weight",
                "schedule covert actions against adversary watchlist accumulation",
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
        """Survey all six ROGUE domains against the canonical assets and the goal."""
        _, launder, vessel, rogue, finance, logistics, surveillance = _run_domain_analyses()
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
                Finding(
                    label="finance",
                    detail=(
                        f"cash_mass_kg={finance.mass_kg:.1f} manifest={finance.manifest.feasible} "
                        f"street_per_g={finance.street_per_gram:.2f}"
                    ),
                ),
                Finding(
                    label="logistics",
                    detail=(
                        f"route={'→'.join(logistics.route.path)} risk={logistics.route.cumulative_risk:.3f} "
                        f"loadout_value={logistics.loadout.value:.0f}"
                    ),
                ),
                Finding(
                    label="surveillance",
                    detail=(
                        f"success={surveillance.success_probability:.3f} compromise={surveillance.compromise_step}"
                    ),
                ),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the seven deterministic steps matching the mission objectives."""
        return MissionPlan(
            steps=(
                Step(
                    "network",
                    "analyze_laundering",
                    params={"sources": _SOURCES, "sinks": _SINKS, "objectives": len(brief.objectives)},
                ),
                Step("vessel", "forensic_scan", params={"profile": _VESSEL_PROFILE.name}),
                Step("rogue", "solve_optimal_policy", params={"horizon": _ROGUE_MODEL.horizon}),
                Step("finance", "narcotics_finance", params={"value_usd": _FINANCE["value_usd"]}),
                Step(
                    "logistics",
                    "operations_router",
                    params={"origin": _LOGISTICS["origin"], "destination": _LOGISTICS["destination"]},
                ),
                Step("surveillance", "watchlist_model", params={"actions": len(_ACTIONS)}),
                Step("verify", "cross_check_determinism", params={"seed": _SEED}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the full deterministic ROGUE analysis and return its outcome."""
        graph, launder, vessel, rogue, finance, logistics, surveillance = _run_domain_analyses()
        results: dict[str, Any] = {
            "steps_completed": len(plan.steps),
            "outputs": tuple(step.name for step in plan.steps),
            "seed": _SEED,
            "input_hash": _input_hash(graph),
            "laundering": launder.as_dict(),
            "vessel": vessel.as_dict(),
            "rogue": rogue.as_dict(),
            "narcotics_finance": finance.as_dict(),
            "operations_logistics": logistics.as_dict(),
            "surveillance": surveillance.as_dict(),
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
                "cash physics bound a laundering run before the courier ever flies",
                "the layered route cuts cumulative voyage risk below the direct one",
                "adversary watchlists price every covert action — order matters",
                "deterministic provenance makes every ROGUE result independently audit-able",
            ),
        )


def run_rogue_mission(request: ReconRequest) -> Debrief:
    """Convenience entry: drive the full five-stage flow on a fresh provider."""
    from bond_api.protocol import run_mission

    return run_mission(MissionProvider(), request)
