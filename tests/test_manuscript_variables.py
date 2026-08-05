"""Tests for manuscript {{TOKEN}} hydration and the live cross-reference gate.

The cross-reference test scans only the numbered prose sections
(``manuscript/[0-9]*.md``) and asserts every token they contain is generated
by :func:`generate_variables` — the "never hand-author metrics" guarantee.
"""

from __future__ import annotations

import datetime as dt
import re

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
    compromise_step_label,
    direct_leg_risk,
    generate_variables,
    last_escalation_action,
    load_mission_config,
    order_endpoint,
    project_root,
    risk_reduction,
    substitute,
)

_TOKEN_RE = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")


def test_generate_variables_contains_expected_tokens():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, 12, 0, tzinfo=dt.timezone.utc))
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
        "GENERATION_TIMESTAMP",
    ):
        assert key in tokens and tokens[key] != ""


def test_generate_variables_values_match_domain():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4))
    assert tokens["BOND_FILM"] == "licence_to_kill"
    assert tokens["BOND_CODENAME"] == "ROGUE"
    assert tokens["LAUNDERING_NODES"] == "22"
    assert tokens["VESSEL_ANOMALIES"] == "2"
    assert tokens["ROGUE_FIRST_ACTION"] == "stealth"
    assert float(tokens["INTEGRATION_SCORE"]) == pytest.approx(0.6526, abs=0.01)


def test_generate_variables_deterministic_under_fixed_now():
    now = dt.datetime(2026, 8, 4, 9, 30, tzinfo=dt.timezone.utc)
    assert generate_variables(now=now) == generate_variables(now=now)


def test_timestamp_changes_with_now():
    a = generate_variables(now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
    b = generate_variables(now=dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc))
    assert a["GENERATION_TIMESTAMP"] != b["GENERATION_TIMESTAMP"]


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
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    manuscript = project_root() / "manuscript"
    used: set[str] = set()
    for section in sorted(manuscript.glob("[0-9]*.md")):
        used.update(_TOKEN_RE.findall(section.read_text(encoding="utf-8")))
    missing = sorted(t for t in used if t not in tokens)
    assert missing == [], f"manuscript tokens not generated: {missing}"


def test_domain_extension_tokens():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
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
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    assert tokens[token] == _PARAMETER_BINDINGS[token](), f"{token} drifted from its canonical source"
    placeholder = "{{" + token + "}}"
    citing = [name for name, text in _numbered_sections().items() if placeholder in text]
    assert citing, f"{token} is generated but no numbered section cites it — prose may hard-code it instead"


def test_no_section_leaves_an_unresolved_placeholder():
    """After substitution, no ``{{...}}`` may survive in any numbered section."""
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
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


def test_direct_baseline_is_not_computed_by_shortest_path():
    """Lexical guard on the one binding the canonical data cannot discriminate.

    On the canonical network the direct leg *is* the distance-minimal path,
    so both implementations produce {{LOG_DIRECT_RISK}} = 0.300 and no
    value-level assertion can tell them apart. The discriminating cases live
    in ``test_direct_leg_risk_reads_the_direct_leg_not_the_shortest_path``
    (semantics) and ``test_figures.py::test_operations_figure_requires_a_real_direct_leg``
    (behaviour); this pins that the token generator does not quietly go back
    to routing for its baseline.
    """
    source = (project_root() / "src" / "licence_to_kill" / "manuscript_variables.py").read_text(encoding="utf-8")
    assert "shortest_path" not in source, "the direct-leg baseline must come from direct_leg, not from routing"
    assert "direct_leg" in source


def test_direct_risk_token_is_the_canonical_direct_leg():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
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


def test_rogue_peak_alert_token_reports_the_terminal_escalation():
    """The token must carry the alert the closing action leaves behind."""
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    report = solve_optimal_policy(canonical_rogue_params()["model"])
    assert tokens["ROGUE_PEAK_ALERT"] == f"{report.peak_alert:.1f}"
    assert tokens["ROGUE_TERMINAL_ALERT"] == f"{report.terminal_alert:.1f}"
    assert float(tokens["ROGUE_PEAK_ALERT"]) > 0.0, "a flat-zero peak alert hides the final overt action"


def test_every_generated_token_is_used_somewhere():
    """A token nobody cites is dead weight that will silently rot.

    ``GENERATION_TIMESTAMP`` and the identity tokens consumed by the render
    header are the documented exceptions.
    """
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    allowed_unused = {"GENERATION_TIMESTAMP"}
    corpus = "".join(_numbered_sections().values())
    unused = sorted(k for k in tokens if k not in allowed_unused and "{{" + k + "}}" not in corpus)
    assert unused == [], f"generated but never cited: {unused}"
