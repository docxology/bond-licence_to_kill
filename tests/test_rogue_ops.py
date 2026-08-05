"""Real-data tests for the rogue-00 risk model (escalation + blowback DP).

Deterministic arithmetic only: the DP, logistic hazard, and escalation
projection are all exact and reproducible. No mocks, no RNG.
"""

from __future__ import annotations

import pytest

from licence_to_kill.rogue_ops import (
    DEFAULT_ACTIONS,
    RogueModel,
    RogueReport,
    alert_increment,
    blowback_probability,
    build_rogue_model,
    canonical_rogue_params,
    escalation_path,
    expected_value_of_policy,
    next_alert,
    solve_optimal_policy,
)


def test_build_rogue_model_canonical():
    m = build_rogue_model()
    assert m.actions == DEFAULT_ACTIONS
    assert m.horizon == 10
    assert m.alert_max == 10
    assert m.beta_0 == -5.0


def test_rogue_model_validation_errors():
    with pytest.raises(ValueError):
        build_rogue_model(horizon=0)
    with pytest.raises(ValueError):
        build_rogue_model(alert_max=0)
    with pytest.raises(ValueError):
        RogueModel(
            horizon=5,
            alert_max=5,
            actions=("a",),
            visibility=(1.0,),
            gain=(1.0, 2.0),
            beta_0=0,
            beta_alert=0,
            beta_exposure=0,
            loss_on_blowback=1,
        )
    with pytest.raises(ValueError):
        RogueModel(
            horizon=5,
            alert_max=5,
            actions=(),
            visibility=(),
            gain=(),
            beta_0=0,
            beta_alert=0,
            beta_exposure=0,
            loss_on_blowback=1,
        )
    with pytest.raises(ValueError):
        RogueModel(
            horizon=5,
            alert_max=5,
            actions=("a",),
            visibility=(-1.0,),
            gain=(1.0,),
            beta_0=0,
            beta_alert=0,
            beta_exposure=0,
            loss_on_blowback=1,
        )
    with pytest.raises(ValueError):
        RogueModel(
            horizon=5,
            alert_max=5,
            actions=("a",),
            visibility=(1.0,),
            gain=(1.0,),
            beta_0=0,
            beta_alert=0,
            beta_exposure=0,
            loss_on_blowback=1,
            exposure_cap=0,
        )


def test_blowback_probability_bounds_and_branches():
    m = build_rogue_model()
    assert 0.0 < blowback_probability(0, 0, m) < 1.0
    # z >= 0 branch (large alert + exposure pulls the logistic numerator up)
    assert blowback_probability(10, 20, m) > 0.99
    # monotonic increasing in alert and exposure
    assert blowback_probability(2, 0, m) > blowback_probability(1, 0, m)
    assert blowback_probability(0, 2, m) > blowback_probability(0, 1, m)


def test_escalation_path_updates_state():
    m = build_rogue_model()
    path = escalation_path(m, [0, 1, 2])
    assert len(path) == 3
    assert path[0]["step"] == 0
    assert path[0]["alert"] == 0.0
    # the projection uses the DP's integral alert lattice, not raw visibility
    assert path[1]["alert"] == pytest.approx(alert_increment(m, 0))
    assert path[2]["alert"] == pytest.approx(alert_increment(m, 0) + alert_increment(m, 1))
    assert 0.0 < float(path[0]["blowback"]) < 1.0


def test_expected_value_of_policy():
    m = build_rogue_model()
    value, path = expected_value_of_policy(m, [0, 0, 0, 0])
    # deterministic: same policy gives the same value
    value2, _ = expected_value_of_policy(m, [0, 0, 0, 0])
    assert value == pytest.approx(value2)
    assert len(path) == 4


def test_dp_beats_naive_policy():
    m = build_rogue_model()
    optimal = solve_optimal_policy(m).optimal_value
    naive, _ = expected_value_of_policy(m, [2] * m.horizon)  # all-overt
    assert optimal >= naive - 1e-9


def test_solve_optimal_policy_report():
    m = build_rogue_model()
    r = solve_optimal_policy(m)
    assert isinstance(r, RogueReport)
    assert r.optimal_value == pytest.approx(1.6648, abs=0.01)
    assert r.first_action == "stealth"
    assert r.peak_blowback == pytest.approx(0.3775, abs=0.01)
    assert len(r.escalation) == m.horizon
    assert r.policy_cells == m.horizon * (m.alert_max + 1) * (m.exposure_cap + 1)
    assert r.actions == DEFAULT_ACTIONS


def test_solve_optimal_policy_deterministic():
    a = solve_optimal_policy(build_rogue_model()).as_dict()
    b = solve_optimal_policy(build_rogue_model()).as_dict()
    assert a == b


def test_solve_optimal_policy_horizon_two():
    # a short horizon still returns a valid policy and non-empty escalation
    r = solve_optimal_policy(build_rogue_model(horizon=2))
    assert len(r.escalation) == 2
    assert r.horizon == 2


def test_alert_transition_is_shared_and_integral():
    """One definition of the alert transition, used by DP and projection alike.

    The DP optimises over integer alert states, so the visibility ladder is
    truncated onto that lattice. Before this was factored out, the DP used
    ``int(visibility)`` while ``escalation_path``/``expected_value_of_policy``
    used the raw float — two different processes reported as one.
    """
    m = build_rogue_model()
    assert alert_increment(m, 0) == 0  # stealth 0.5 → 0 on the integer lattice
    assert alert_increment(m, 1) == 1  # covert 1.5 → 1
    assert alert_increment(m, 2) == 3  # overt 3.0 → 3
    assert next_alert(0.0, m, 2) == pytest.approx(3.0)
    # the clamp at alert_max holds
    assert next_alert(float(m.alert_max), m, 2) == pytest.approx(float(m.alert_max))


def test_dp_value_equals_replayed_optimal_sequence():
    """Replaying the DP's own action sequence must reproduce its value exactly.

    This is the real oracle for the DP: it only holds when the lattice
    transition and the projection transition are the same function. It fails
    outright if they diverge, which is exactly the defect the shared
    ``next_alert`` removed.
    """
    m = build_rogue_model()
    report = solve_optimal_policy(m)
    index = {name: i for i, name in enumerate(m.actions)}
    sequence = [index[str(step["action"])] for step in report.escalation]
    replayed, _ = expected_value_of_policy(m, sequence)
    assert replayed == pytest.approx(report.optimal_value, abs=1e-9)


def test_dp_dominates_every_constant_policy():
    """The optimum must be >= every fixed-intensity policy, not just all-overt."""
    m = build_rogue_model()
    optimal = solve_optimal_policy(m).optimal_value
    for action_idx in range(len(m.actions)):
        constant, _ = expected_value_of_policy(m, [action_idx] * m.horizon)
        assert optimal >= constant - 1e-9


def test_canonical_rogue_params_expose_the_lattice():
    params = canonical_rogue_params()
    model = params["model"]
    assert params["horizon"] == model.horizon
    assert params["alert_max"] == model.alert_max
    assert params["exposure_cap"] == model.exposure_cap
    assert params["actions"] == model.actions
