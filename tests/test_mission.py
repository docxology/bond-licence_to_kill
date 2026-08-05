"""Tests for the ROGUE MissionProvider adapter and the frozen bond-api contract.

Zero mocks: the provider is constructed directly, the full five-stage flow is
driven through the real ``bond_api.protocol.run_mission``, and determinism is
proven by executing twice and comparing results byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from licence_to_kill.mission import GADGET_REGISTRY, MissionProvider, run_rogue_mission

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
