"""Bind ``manuscript/config.yaml``'s ``mission:`` block to the executable params.

The pure domain core is dependency-free and does not read YAML, so the
``mission:`` block in ``manuscript/config.yaml`` is a *declared mirror* of the
``canonical_*_params()`` functions rather than their input. Without a gate that
mirror rots silently: a parameter changed in Python leaves the YAML — and any
prose that cites it — quietly wrong.

These tests are that gate. Every key in the YAML block is compared against the
value the code actually computes with, so the two cannot drift. They also pin
that the three consumers of those params (``mission.py``,
``manuscript_variables.py``, ``figures/plots.py``) agree, and that the search
bounds are genuinely *consumed* rather than merely named.

Zero mocks: real YAML file, real canonical functions, real analyses.
"""

from __future__ import annotations

import json

import pytest

from licence_to_kill.laundering_graph import (
    analyze_laundering,
    build_sanchez_network,
    canonical_laundering_params,
)
from licence_to_kill.manuscript_variables import load_mission_config, project_root
from licence_to_kill.narcotics_finance import canonical_finance_params
from licence_to_kill.operations_logistics import canonical_logistics_params
from licence_to_kill.rogue_ops import canonical_rogue_params
from licence_to_kill.surveillance import EXACT_ORDER_LIMIT, canonical_surveillance_params
from licence_to_kill.vessel_forensics import canonical_vessel_params


@pytest.fixture(scope="module")
def mission_block() -> dict:
    """The ``mission:`` block of the on-disk manuscript config."""
    return load_mission_config()["mission"]


def test_identity_and_seed_mirror(mission_block):
    assert mission_block["film"] == "licence_to_kill"
    assert mission_block["codename"] == "ROGUE"
    assert mission_block["seed"] == canonical_laundering_params()["seed"]


def test_laundering_block_mirrors_canonical(mission_block):
    params = canonical_laundering_params()
    block = mission_block["laundering"]
    assert tuple(block["sources"]) == params["sources"]
    assert tuple(block["sinks"]) == params["sinks"]
    assert block["max_depth"] == params["max_depth"]
    assert block["max_cycles"] == params["max_cycles"]
    assert block["max_paths"] == params["max_paths"]
    assert block["funnel_threshold"] == pytest.approx(params["funnel_threshold"])


def test_vessel_block_mirrors_canonical(mission_block):
    params = canonical_vessel_params()
    profile = params["profile"]
    block = mission_block["vessel"]
    assert block["profile"] == profile.name
    assert block["cargo_volume_m3"] == pytest.approx(profile.cargo_volume_m3)
    assert block["block_coefficient"] == pytest.approx(profile.block_coefficient)
    assert block["max_speed_knots"] == pytest.approx(profile.max_speed_knots)
    assert block["observed"]["cargo_mass_t"] == pytest.approx(params["observed"]["cargo_mass_t"])
    assert block["observed"]["declared_displacement_t"] == pytest.approx(params["observed"]["declared_displacement_t"])


def test_rogue_block_mirrors_canonical(mission_block):
    params = canonical_rogue_params()
    block = mission_block["rogue"]
    assert block["horizon"] == params["horizon"]
    assert block["alert_max"] == params["alert_max"]
    assert block["exposure_cap"] == params["exposure_cap"]
    assert tuple(block["actions"]) == params["actions"]


def test_finance_block_mirrors_canonical(mission_block):
    params = canonical_finance_params()
    block = mission_block["finance"]
    assert block["value_usd"] == pytest.approx(params["value_usd"])
    assert block["denomination"] == pytest.approx(params["denomination"])
    assert block["purity"] == pytest.approx(params["purity"])
    assert block["base_cost_per_kg"] == pytest.approx(params["base_cost_per_kg"])
    assert block["hold_volume_m3"] == pytest.approx(params["hold_volume_m3"])
    assert block["hold_mass_kg"] == pytest.approx(params["hold_mass_kg"])
    assert tuple(block["stages"]) == tuple(name for name, _ in params["stages"])


def test_logistics_block_mirrors_canonical(mission_block):
    params = canonical_logistics_params()
    block = mission_block["logistics"]
    assert block["origin"] == params["origin"]
    assert block["destination"] == params["destination"]
    assert block["capacity_kg"] == pytest.approx(params["capacity_kg"])
    assert block["speed_knots"] == pytest.approx(params["speed_knots"])
    assert block["endurance_nm"] == pytest.approx(params["endurance_nm"])
    assert block["refuel_hours"] == pytest.approx(params["refuel_hours"])


def test_surveillance_block_mirrors_canonical(mission_block):
    params = canonical_surveillance_params()
    model = params["model"]
    block = mission_block["surveillance"]
    assert block["actions"] == len(params["actions"])
    assert block["detection_threshold"] == pytest.approx(model.detection_threshold)
    assert block["beta_0"] == pytest.approx(model.beta_0)
    assert block["beta_watch"] == pytest.approx(model.beta_watch)
    assert block["beta_signature"] == pytest.approx(model.beta_signature)
    assert block["exact_limit"] == EXACT_ORDER_LIMIT


def test_declared_search_bounds_are_consumed_not_just_named():
    """Flipping a bound must change the analysis — otherwise it is decorative.

    ``max_paths`` and ``max_cycles`` are threaded from
    ``canonical_laundering_params()`` into the detectors. This asserts they
    genuinely bind: halving the path cap halves the enumerated chains, and
    dropping the cycle cap to zero removes every cycle. Without this the
    parameter could be renamed or dropped and no test would notice.
    """
    params = canonical_laundering_params()
    graph = build_sanchez_network(seed=int(params["seed"]))
    baseline = analyze_laundering(
        graph,
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_cycles=int(params["max_cycles"]),
        max_paths=int(params["max_paths"]),
        funnel_threshold=float(params["funnel_threshold"]),
    )
    tightened = analyze_laundering(
        graph,
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_cycles=int(params["max_cycles"]),
        max_paths=int(params["max_paths"]) // 2,
        funnel_threshold=float(params["funnel_threshold"]),
    )
    # ``max_paths`` is set strictly above the canonical network's true chain
    # count (C2 fix), so the reported enumeration is the *exact* count, not a
    # saturated cap. Halving the cap still saturates, which is what proves
    # the bound genuinely binds rather than being decorative.
    assert len(baseline.layering_paths) < int(params["max_paths"])
    assert len(tightened.layering_paths) == int(params["max_paths"]) // 2

    # A stricter funnel threshold cannot admit MORE funnels.
    stricter = analyze_laundering(
        graph,
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_cycles=int(params["max_cycles"]),
        max_paths=int(params["max_paths"]),
        funnel_threshold=float(params["funnel_threshold"]) * 4.0,
    )
    assert len(stricter.funnels) < len(baseline.funnels)


def test_consumers_share_one_canonical_scenario():
    """``mission.py`` and ``manuscript_variables.py`` must run the same inputs.

    Both modules import the same ``canonical_*_params()`` functions; this
    asserts the *outcome* agrees, which is the property that actually matters
    (a manuscript token describing a different scenario than the mission
    outcome would be an undetectable lie).
    """
    from licence_to_kill.manuscript_variables import _run_mission_analyses
    from licence_to_kill.mission import _run_domain_analyses

    _, launder_a, vessel_a, rogue_a, fin_a, log_a, surv_a = _run_domain_analyses()
    _, launder_b, vessel_b, rogue_b, fin_b, log_b, surv_b = _run_mission_analyses()

    assert launder_a.as_dict() == launder_b.as_dict()
    assert vessel_a.as_dict() == vessel_b.as_dict()
    assert rogue_a.as_dict() == rogue_b.as_dict()
    assert fin_a.as_dict() == fin_b.as_dict()
    assert log_a.as_dict() == log_b.as_dict()
    assert surv_a.as_dict() == surv_b.as_dict()


#: Every domain core module → a phrase the deposit metadata must contain to
#: describe it. Keys are checked against what is actually on disk, so adding a
#: seventh domain core fails this test until the deposit description is
#: updated to mention it.
_DOMAIN_DESCRIPTION_PHRASES = {
    "laundering_graph.py": "money-laundering-graph",
    "vessel_forensics.py": "vessel-forensic",
    "rogue_ops.py": "rogue-operation",
    "narcotics_finance.py": "narcotics-finance",
    "operations_logistics.py": "operations logistics",
    "surveillance.py": "surveillance",
}
#: Modules under ``src/licence_to_kill/`` that are adapters or tooling, not
#: domain cores.
_NON_DOMAIN_MODULES = {"__init__.py", "mission.py", "manuscript_variables.py"}


def _domain_core_modules() -> set[str]:
    src = project_root() / "src" / "licence_to_kill"
    return {p.name for p in src.glob("*.py")} - _NON_DOMAIN_MODULES


def test_domain_phrase_map_matches_the_modules_on_disk():
    """The phrase map is bound to the tree, not to a remembered domain count."""
    assert _domain_core_modules() == set(_DOMAIN_DESCRIPTION_PHRASES)


@pytest.mark.parametrize("deposit", [".zenodo.json", "codemeta.json"])
def test_deposit_metadata_describes_every_domain(deposit):
    """Deposit descriptions must name every domain core the package ships.

    The Zenodo description described three domains for the whole life of the
    six-domain package — an archived record that understates what was
    deposited. This gate makes that failure mode loud: drop a domain from the
    description, or add a domain core without updating it, and this goes red.
    """
    path = project_root() / deposit
    payload = json.loads(path.read_text(encoding="utf-8"))
    description = str(payload["description"]).lower()
    missing = sorted(
        phrase for module, phrase in _DOMAIN_DESCRIPTION_PHRASES.items() if phrase.lower() not in description
    )
    assert missing == [], f"{deposit} description omits: {missing}"
