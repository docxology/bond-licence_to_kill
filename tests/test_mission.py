"""Tests for the ROGUE MissionProvider adapter and the frozen bond-api contract.

Zero mocks: the provider is constructed directly, the full five-stage flow is
driven through the real ``bond_api.protocol.run_mission``, and determinism is
proven by executing twice and comparing results byte-for-byte.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from licence_to_kill.laundering_graph import build_sanchez_network
from licence_to_kill.mission import (
    GADGET_REGISTRY,
    MissionProvider,
    _input_hash,
    canonical_domain_inputs,
    run_rogue_mission,
)
from licence_to_kill.rogue_ops import canonical_rogue_params
from licence_to_kill.surveillance import canonical_surveillance_params

from bond_api.protocol import (
    MissionProvider as ProtocolType,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    ReconReport,
    ReconRequest,
    run_mission,
)

_SRC = Path(__file__).resolve().parents[1] / "src" / "licence_to_kill"


def test_provider_satisfies_protocol():
    # runtime-checkable: isinstance exercises the structural contract
    assert isinstance(MissionProvider(), ProtocolType)


def test_brief_fields():
    brief = MissionProvider().brief()
    assert isinstance(brief, MissionBrief)
    assert brief.film == "licence_to_kill"
    assert brief.codename == "ROGUE"
    assert len(brief.objectives) == 6
    assert len(brief.assets) == 6
    assert any(c.kind == "determinism" for c in brief.constraints)


def test_recon_findings():
    report = MissionProvider().recon(ReconRequest(goal="survey the network"))
    assert isinstance(report, ReconReport)
    labels = {f.label for f in report.findings}
    assert {"goal", "layering", "integration", "vessel", "rogue", "finance", "logistics", "surveillance"} <= labels


def test_plan_steps():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert isinstance(plan, MissionPlan)
    assert len(plan.steps) == 7
    assert {s.name for s in plan.steps} == {
        "network",
        "vessel",
        "rogue",
        "finance",
        "logistics",
        "surveillance",
        "verify",
    }


def test_execute_deterministic_and_provenance():
    provider = MissionProvider()
    first = provider.execute(provider.plan(provider.brief()))
    second = provider.execute(provider.plan(provider.brief()))
    assert isinstance(first, MissionOutcome)
    assert first.success is True
    assert first.results == second.results
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.seed == 0
    assert first.provenance.wall_time_s == 0.0
    assert first.provenance.package_version == "0.1.0"
    assert set(first.results) >= {
        "laundering",
        "vessel",
        "rogue",
        "narcotics_finance",
        "operations_logistics",
        "surveillance",
        "seed",
        "input_hash",
    }


def test_execute_results_match_domain():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    launder = outcome.results["laundering"]
    assert launder["num_nodes"] == 22
    assert launder["integration_score"] == pytest.approx(0.6526, abs=0.01)
    vessel = outcome.results["vessel"]
    assert vessel["num_anomalies"] == 2
    rogue = outcome.results["rogue"]
    assert rogue["first_action"] == "stealth"
    finance = outcome.results["narcotics_finance"]
    assert finance["bills"] == 50_000
    assert finance["manifest"]["feasible"] is True
    logistics = outcome.results["operations_logistics"]
    assert logistics["route"]["path"] == ["IC", "HK", "FL"]
    assert logistics["loadout"]["value"] == pytest.approx(32.0)
    surveillance = outcome.results["surveillance"]
    assert surveillance["compromise_step"] == 4


def test_debrief_lessons_and_passthrough():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert debrief.outcome is outcome
    assert len(debrief.lessons) == 7


def test_full_run_mission_flow():
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(goal="complete ROGUE"))
    assert debrief.outcome.success is True
    assert len(debrief.lessons) == 7


def test_run_rogue_mission_convenience():
    debrief = run_rogue_mission(ReconRequest(goal="go"))
    assert debrief.outcome.success is True


def test_gadget_registry_register():
    gadgets = set(GADGET_REGISTRY.gadgets_for("licence_to_kill"))
    assert gadgets == {
        "laundering_analyzer",
        "laundering_network",
        "vessel_forensics",
        "rogue_risk_model",
        "narcotics_finance",
        "operations_router",
        "surveillance_model",
        "network_manifest",
    }
    manifest = GADGET_REGISTRY.lookup("licence_to_kill", "network_manifest")
    assert manifest["seed"] == 0
    assert GADGET_REGISTRY.contains("licence_to_kill", "surveillance_model")


#: One mutation per domain: domain key → (parameter key, mutated value).
#: Each mutation changes a real input the mission consumes, so a provenance
#: hash that claims to cover "all six domains" must respond to every one.
_DOMAIN_MUTATIONS = {
    "laundering": ("max_depth", 99),
    "vessel": ("observed", {"cargo_mass_t": 1.0, "declared_displacement_t": 1.0}),
    "rogue": ("model", replace(canonical_rogue_params()["model"], horizon=3)),
    "finance": ("purity", 0.99),
    "logistics": ("capacity_kg", 999.0),
    "surveillance": ("model", replace(canonical_surveillance_params()["model"], beta_0=-1.0)),
}


def test_canonical_domain_inputs_lists_every_domain():
    assert set(canonical_domain_inputs()) == set(_DOMAIN_MUTATIONS)


@pytest.mark.parametrize("domain", sorted(_DOMAIN_MUTATIONS))
def test_input_hash_covers_every_domain(domain):
    """Mutating any one domain's canonical inputs must change the provenance hash.

    This is the gate the ``input_hash`` documentation depends on: README,
    AGENTS, and ``docs/architecture.md`` all claim the hash covers the
    canonical inputs of all six domains, so an outcome can be audited without
    re-running it. Before this test, the hashed payload silently omitted the
    entire vessel and rogue domains — every vessel/rogue parameter could
    change while the "audit" hash stayed identical. Dropping a domain from
    ``_input_hash``'s payload turns the matching case red.
    """
    graph = build_sanchez_network(seed=0)
    baseline = _input_hash(graph)
    # Control: an untouched copy of the same inputs reproduces the hash.
    assert _input_hash(graph, {k: dict(v) for k, v in canonical_domain_inputs().items()}) == baseline

    key, value = _DOMAIN_MUTATIONS[domain]
    mutated = {k: dict(v) for k, v in canonical_domain_inputs().items()}
    assert key in mutated[domain], f"{domain} has no parameter {key!r}"
    mutated[domain][key] = value
    assert _input_hash(graph, mutated) != baseline, f"{domain} inputs are absent from the provenance hash"


def test_input_hash_covers_the_built_graph():
    """The graph itself is hashed too, not only the declared parameters."""
    baseline = _input_hash(build_sanchez_network(seed=0))
    assert _input_hash(build_sanchez_network(seed=7)) != baseline


def test_pure_domain_modules_are_bond_api_free():
    for name in (
        "laundering_graph.py",
        "vessel_forensics.py",
        "rogue_ops.py",
        "narcotics_finance.py",
        "operations_logistics.py",
        "surveillance.py",
    ):
        source = (_SRC / name).read_text(encoding="utf-8")
        assert "bond_api" not in source, f"{name} must stay bond-api-free"
