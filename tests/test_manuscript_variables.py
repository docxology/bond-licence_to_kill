"""Tests for manuscript {{TOKEN}} hydration and the live cross-reference gate.

The cross-reference test scans only the numbered prose sections
(``manuscript/[0-9]*.md``) and asserts every token they contain is generated
by :func:`generate_variables` — the "never hand-author metrics" guarantee.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from licence_to_kill.laundering_graph import canonical_laundering_params
from licence_to_kill.narcotics_finance import canonical_finance_params
from licence_to_kill.operations_logistics import (
    MissionLeg,
    OperationNetwork,
    canonical_logistics_params,
    direct_leg,
    shortest_path,
)
from licence_to_kill.rogue_ops import canonical_rogue_params, solve_optimal_policy
from licence_to_kill.surveillance import (
    EXACT_ORDER_LIMIT,
    analyze_surveillance,
    canonical_surveillance_params,
)
from licence_to_kill.vessel_forensics import CARGO_DENSITY_CEILING, DISPLACEMENT_TOLERANCE

from licence_to_kill.manuscript_variables import (
    _RANKING_SIMPLEX,
    compromise_step_label,
    direct_leg_risk,
    generate_variables,
    last_escalation_action,
    layering_ranking_stability,
    load_mission_config,
    order_endpoint,
    project_root,
    risk_reduction,
    substitute,
)

_TOKEN_RE = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")


def test_generate_variables_contains_expected_tokens():
    tokens = generate_variables()
    for key in (
        "BOND_FILM",
        "BOND_CODENAME",
        "LAYERING_SCORE",
        "INTEGRATION_SCORE",
        "MIXING_ENTROPY",
        "LAUNDERING_NODES",
        "VESSEL_GROSS_TONNAGE",
        "VESSEL_ANOMALIES",
        "ROGUE_OPTIMAL_VALUE",
        "ROGUE_FIRST_ACTION",
        "PYTHON_VERSION",
    ):
        assert key in tokens and tokens[key] != ""


def test_no_token_carries_a_wall_clock_value():
    """No emitted token may be a clock reading.

    The regression this pins: ``GENERATION_TIMESTAMP`` was rendered into
    ``output/data/manuscript_variables.json`` from ``datetime.now()``, so
    every regeneration produced different bytes while the manuscript claimed
    byte-for-byte reproducibility. Two separate wall-clock formats are
    matched (``YYYY-MM-DD`` and ``HH:MM:SS``) so a reformatted stamp cannot
    creep back in under a new name.
    """
    tokens = generate_variables()
    clockish = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}")
    offenders = sorted(k for k, v in tokens.items() if clockish.search(v))
    assert offenders == [], f"wall-clock-shaped token values persisted: {offenders}"
    source = (project_root() / "src" / "licence_to_kill" / "manuscript_variables.py").read_text(encoding="utf-8")
    assert "datetime" not in source, "the token generator must not import or call a clock"


def test_generate_variables_values_match_domain():
    tokens = generate_variables()
    assert tokens["BOND_FILM"] == "licence_to_kill"
    assert tokens["BOND_CODENAME"] == "ROGUE"
    assert tokens["LAUNDERING_NODES"] == "22"
    assert tokens["VESSEL_ANOMALIES"] == "2"
    assert tokens["ROGUE_FIRST_ACTION"] == "stealth"
    assert float(tokens["INTEGRATION_SCORE"]) == pytest.approx(0.6526, abs=0.01)


def test_generate_variables_is_deterministic_across_a_moving_clock():
    """Two calls with a real second of wall clock between them must agree.

    Deliberately *not* injecting a fixed ``now``: the injected-clock test
    this replaces could not observe the defect it was supposed to guard,
    because it froze the only thing that varied.
    """
    a = generate_variables()
    time.sleep(1.1)
    b = generate_variables()
    assert a == b


def test_load_mission_config_reads_title():
    cfg = load_mission_config()
    assert "title" in cfg["paper"]


def test_project_root_path():
    root = project_root()
    assert root.name == "licence_to_kill"


def test_substitute_replaces_known_and_leaves_unknown():
    text = "Hello {{BOND_CODENAME}}, {{MISSING_TOKEN}}"
    out = substitute(text, {"BOND_CODENAME": "ROGUE"})
    assert out == "Hello ROGUE, {{MISSING_TOKEN}}"


def test_all_manuscript_tokens_are_generated():
    """Live gate: every {{TOKEN}} in numbered prose is produced by generate_variables."""
    tokens = generate_variables()
    manuscript = project_root() / "manuscript"
    used: set[str] = set()
    for section in sorted(manuscript.glob("[0-9]*.md")):
        used.update(_TOKEN_RE.findall(section.read_text(encoding="utf-8")))
    missing = sorted(t for t in used if t not in tokens)
    assert missing == [], f"manuscript tokens not generated: {missing}"


def test_domain_extension_tokens():
    tokens = generate_variables()
    # finance
    assert tokens["FIN_STREET_PURE_GRAM"] == "30"
    assert tokens["FIN_CASH_MASS_KG"] == "50.0"
    assert tokens["FIN_BILLS"] == "50,000"
    # logistics
    assert tokens["LOG_ROUTE"] == "IC → HK → FL"
    assert tokens["LOG_KNAPSACK_VALUE"] == "32"
    assert tokens["LOG_KNAPSACK_WEIGHT"] == "17.7"
    assert tokens["LOG_RISK_REDUCTION"] == "30.7%"
    # surveillance
    assert tokens["SURV_SUCCESS"] == "0.263"
    assert tokens["SURV_COMPROMISE_STEP_ONE"] == "5"
    assert tokens["SURV_PEAK_HAZARD"] == "0.633"
    # all three new prefixes present
    for prefix in ("FIN_", "LOG_", "SURV_"):
        assert any(k.startswith(prefix) for k in tokens)


#: Declared parameters that MUST reach the prose as a token, never as a
#: hand-typed literal: token name → the canonical value it has to carry.
#: This is the concrete form of the "never hand-author a metric" rule for
#: *parameters* (the results side is already covered by the token gate).
_PARAMETER_BINDINGS = {
    "LAUNDERING_MAX_PATHS": lambda: str(canonical_laundering_params()["max_paths"]),
    "LAUNDERING_MAX_DEPTH": lambda: str(canonical_laundering_params()["max_depth"]),
    "LAUNDERING_MAX_CYCLES": lambda: str(canonical_laundering_params()["max_cycles"]),
    "LAUNDERING_FUNNEL_THRESHOLD": lambda: f"{canonical_laundering_params()['funnel_threshold']:.1f}",
    "LAYERING_WEIGHT_CYCLE": lambda: f"{canonical_laundering_params()['layering_weights'][0]:.1f}",
    "FIN_HOLD_VOLUME_M3": lambda: f"{canonical_finance_params()['hold_volume_m3']:,.0f}",
    "FIN_HOLD_MASS_T": lambda: f"{canonical_finance_params()['hold_mass_kg'] / 1000.0:,.0f}",
    "FIN_PURITY": lambda: f"{canonical_finance_params()['purity']:.0%}",
    "FIN_BASE_COST_PER_KG": lambda: f"{canonical_finance_params()['base_cost_per_kg']:,.0f}",
    "LOG_CAPACITY_KG": lambda: f"{canonical_logistics_params()['capacity_kg']:.0f}",
    "LOG_ENDURANCE_NM": lambda: f"{canonical_logistics_params()['endurance_nm']:,.0f}",
    "LOG_SPEED_KNOTS": lambda: f"{canonical_logistics_params()['speed_knots']:.0f}",
    "SURV_THRESHOLD": lambda: f"{canonical_surveillance_params()['model'].detection_threshold:.2f}",
    "SURV_EXACT_LIMIT": lambda: str(EXACT_ORDER_LIMIT),
    "ROGUE_EXPOSURE_CAP": lambda: str(canonical_rogue_params()["exposure_cap"]),
    "VESSEL_CARGO_DENSITY_CEILING": lambda: f"{CARGO_DENSITY_CEILING:.1f}",
    "VESSEL_DISPLACEMENT_TOLERANCE": lambda: f"{DISPLACEMENT_TOLERANCE:.0%}",
}


def _numbered_sections() -> dict[str, str]:
    manuscript = project_root() / "manuscript"
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(manuscript.glob("[0-9]*.md"))}


@pytest.mark.parametrize("token", sorted(_PARAMETER_BINDINGS))
def test_declared_parameter_reaches_prose_as_a_token(token):
    """Each declared parameter is bound: canonical value → token → prose.

    Two failure modes this catches, both of which have bitten this package
    before: (a) the token drifts from the canonical value it claims to
    report, and (b) someone "simplifies" the prose by typing the number
    directly, silently severing it from source. Deleting the token reference
    from every section fails this test.
    """
    tokens = generate_variables()
    assert tokens[token] == _PARAMETER_BINDINGS[token](), f"{token} drifted from its canonical source"
    placeholder = "{{" + token + "}}"
    citing = [name for name, text in _numbered_sections().items() if placeholder in text]
    assert citing, f"{token} is generated but no numbered section cites it — prose may hard-code it instead"


def test_no_section_leaves_an_unresolved_placeholder():
    """After substitution, no ``{{...}}`` may survive in any numbered section."""
    tokens = generate_variables()
    for name, text in _numbered_sections().items():
        rendered = substitute(text, tokens)
        assert _TOKEN_RE.search(rendered) is None, f"{name} has an unresolved token after substitution"


def test_direct_leg_risk_reads_the_direct_leg_not_the_shortest_path():
    """The baseline is the direct leg itself, not whatever path is shortest.

    Constructed counterexample: a two-hop path that is shorter in distance
    than the direct leg. ``shortest_path(..., weight="distance")`` — what the
    token used to be computed from — returns the two-hop route and its
    pooled risk; the direct leg's own risk is a different number.
    """
    legs = (
        MissionLeg("A", "B", 100.0, 1.0, 0.50),
        MissionLeg("A", "C", 10.0, 1.0, 0.10),
        MissionLeg("C", "B", 10.0, 1.0, 0.10),
    )
    network = OperationNetwork(legs)
    assert direct_leg_risk(network, "A", "B") == pytest.approx(0.50)
    distance_minimal = shortest_path(network, "A", "B", weight="distance")
    assert distance_minimal is not None
    assert distance_minimal.path == ("A", "C", "B")
    assert distance_minimal.cumulative_risk == pytest.approx(0.19)


def test_direct_baseline_binds_behaviourally_through_generate_variables():
    """V1: the token's direct-leg baseline is bound on the production entry point.

    On the canonical network the direct leg happens to be the distance-minimal
    path (both give risk 0.300), so no canonical value can discriminate the
    ``direct_leg`` baseline from a ``shortest_path`` one. Injecting a network
    on which they genuinely differ — a high-risk direct ``IC→FL`` leg beside a
    low-risk two-hop ``IC→X→FL`` path — forces the difference into the open:
    the token must carry the *direct leg's* risk, not the route's. This is the
    behavioural binding that replaces the old lexical ``"shortest_path" not in
    source`` guard (which an alias import could defeat).
    """
    legs = (
        MissionLeg("IC", "FL", 100.0, 1.0, 0.50),
        MissionLeg("IC", "X", 10.0, 1.0, 0.10),
        MissionLeg("X", "FL", 10.0, 1.0, 0.10),
    )
    network = OperationNetwork(legs)
    tokens = generate_variables(logistics_network=network)
    # the risk-optimal route is the two-hop path (lower cumulative risk)
    assert tokens["LOG_ROUTE"] == "IC → X → FL"
    assert float(tokens["LOG_ROUTE_RISK"]) == pytest.approx(0.19, abs=1e-3)
    # the baseline token is the DIRECT leg's own risk — a different number
    assert tokens["LOG_DIRECT_RISK"] == "0.500"
    assert float(tokens["LOG_DIRECT_RISK"]) != float(tokens["LOG_ROUTE_RISK"])


def test_direct_leg_risk_raises_when_there_is_no_direct_leg():
    """No direct leg is a loud failure, never a substituted default."""
    network = OperationNetwork(
        (
            MissionLeg("A", "C", 10.0, 1.0, 0.10),
            MissionLeg("C", "B", 10.0, 1.0, 0.10),
        )
    )
    assert direct_leg(network, "A", "B") is None
    with pytest.raises(ValueError, match="no direct leg"):
        direct_leg_risk(network, "A", "B")


def test_direct_risk_token_is_the_canonical_direct_leg():
    tokens = generate_variables()
    params = canonical_logistics_params()
    network = OperationNetwork(params["legs"])
    expected = direct_leg_risk(network, str(params["origin"]), str(params["destination"]))
    assert tokens["LOG_DIRECT_RISK"] == f"{expected:.3f}"


def test_risk_reduction_both_branches():
    assert risk_reduction(0.30, 0.208) == pytest.approx((0.30 - 0.208) / 0.30)
    # a risk-free direct leg leaves nothing to reduce
    assert risk_reduction(0.0, 0.0) == 0.0
    assert risk_reduction(-1.0, 0.5) == 0.0


def test_last_escalation_action_both_branches():
    assert last_escalation_action(({"action": "stealth"}, {"action": "overt"})) == "overt"
    assert last_escalation_action(()) == "none"


def test_compromise_step_label_both_branches():
    assert compromise_step_label(4) == "5"
    assert compromise_step_label(0) == "1"
    assert compromise_step_label(None) == "never"


def test_order_endpoint_both_branches():
    order = ("observe", "bug", "infiltrate")
    assert order_endpoint(order, 0) == "observe"
    assert order_endpoint(order, -1) == "infiltrate"
    assert order_endpoint((), 0) == "none"
    assert order_endpoint((), -1) == "none"


def test_empty_surveillance_run_reaches_the_none_labels():
    """The 'no actions' labels are reachable through the real domain API.

    ``analyze_surveillance`` accepts an empty action set, so these are live
    code paths for a caller, not decoration on an impossible case.
    """
    report = analyze_surveillance((), canonical_surveillance_params()["model"])
    assert order_endpoint(report.optimal_order, 0) == "none"
    assert order_endpoint(report.optimal_order, -1) == "none"
    assert compromise_step_label(report.compromise_step) == "never"


def test_layering_score_ranking_is_weight_dependent():
    """V2 negative control: the composite score's ranking is not weight-invariant.

    The composite score blends three hand-chosen weights, so a single-scalar
    ordering of two structures is only meaningful if it survives the choice of
    weights. It does not: across the coarse simplex sampling both orderings of
    the two reference structures occur (True and False both appear), and the
    measured share of weight vectors that agree with the canonical-weight
    ordering is strictly between 0 and 1 — the score is neither a stable
    ranking device nor trivially degenerate. This pins the manuscript's honest
    claim: previously it asserted the score was ``useful for ranking`` with no
    test able to falsify it.
    """
    from licence_to_kill.manuscript_variables import (
        _RANK_SINKS,
        _RANK_SOURCES,
        _blend,
        _component_vector,
        _cycle_heavy_probe,
        _deep_funnel_probe,
    )

    a = _component_vector(_cycle_heavy_probe(), _RANK_SOURCES, _RANK_SINKS)
    b = _component_vector(_deep_funnel_probe(), _RANK_SOURCES, _RANK_SINKS)
    orderings = {_blend(a, w) > _blend(b, w) for w in _RANKING_SIMPLEX}
    assert orderings == {True, False}
    share = layering_ranking_stability()
    assert 0.0 < share < 1.0


def test_layering_ranking_tokens_are_live_and_consistent():
    """The manuscript's ranking-stability tokens carry the real measurement."""
    tokens = generate_variables()
    share = layering_ranking_stability()
    assert tokens["LAYERING_RANKING_SAMPLES"] == str(len(_RANKING_SIMPLEX))
    assert tokens["LAYERING_RANKING_STABILITY"] == f"{share:.0%}"
    assert 0.0 < share < 1.0


def test_rogue_peak_alert_token_reports_the_terminal_escalation():
    """The token must carry the alert the closing action leaves behind."""
    tokens = generate_variables()
    report = solve_optimal_policy(canonical_rogue_params()["model"])
    assert tokens["ROGUE_PEAK_ALERT"] == f"{report.peak_alert:.1f}"
    assert tokens["ROGUE_TERMINAL_ALERT"] == f"{report.terminal_alert:.1f}"
    assert float(tokens["ROGUE_PEAK_ALERT"]) > 0.0, "a flat-zero peak alert hides the final overt action"


def test_every_generated_token_is_used_somewhere():
    """A token nobody cites is dead weight that will silently rot.

    There is no longer an exception list: ``GENERATION_TIMESTAMP`` was the
    only entry, and removing the wall clock removed it.
    """
    tokens = generate_variables()
    corpus = "".join(_numbered_sections().values())
    unused = sorted(k for k in tokens if "{{" + k + "}}" not in corpus)
    assert unused == [], f"generated but never cited: {unused}"


def _digest_tree(root: Path) -> dict[str, str]:
    """sha256 of every persisted artifact under ``root``, keyed by relative path."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_regeneration_is_byte_identical(tmp_path):
    """The claim, asserted rather than asserted-about.

    Runs the *production* entry point — ``scripts/z_generate_manuscript_variables.py``
    — twice, a real second apart, into two independent copies of the package,
    then compares every emitted artifact byte for byte: the variables JSON,
    the mission results JSON, the nine rendered sections, and the four PNGs.
    No clock is injected anywhere, which is exactly why this test can fail
    and the previous fixed-``now`` test could not: it failed on the variables
    JSON while ``GENERATION_TIMESTAMP`` was live.

    Scope: a fixed interpreter and NumPy build. ``PYTHON_VERSION`` and
    ``NUMPY_VERSION`` are the only environment-derived tokens, and this test
    holds them fixed by running both passes on ``sys.executable``.
    """
    source_root = project_root()
    digests: list[dict[str, str]] = []
    for run in ("first", "second"):
        work = tmp_path / run
        shutil.copytree(
            source_root,
            work,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", "output", "*.egg-info", "__pycache__", ".pytest_cache", ".mypy_cache"
            ),
        )
        result = subprocess.run(
            [sys.executable, str(work / "scripts" / "z_generate_manuscript_variables.py")],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, result.stderr
        digests.append(_digest_tree(work / "output"))
        if run == "first":
            time.sleep(1.1)

    emitted = sorted(digests[0])
    # Guard against a vacuous pass: the comparison must actually see the
    # artifacts the reproducibility claim covers.
    assert any(name.endswith("manuscript_variables.json") for name in emitted), emitted
    assert sum(name.endswith(".md") for name in emitted) == 9, emitted
    assert sum(name.endswith(".png") for name in emitted) == 4, emitted

    differing = sorted(k for k in digests[0] if digests[0][k] != digests[1].get(k))
    assert digests[0].keys() == digests[1].keys()
    assert differing == [], f"regeneration changed these artifacts: {differing}"
