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
    blowback_probability,
    build_rogue_model,
    escalation_path,
    expected_value_of_policy,
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
    assert path[1]["alert"] == pytest.approx(m.visibility[0])
    assert path[2]["alert"] == pytest.approx(m.visibility[0] + m.visibility[1])
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
    assert r.peak_blowback == pytest.approx(0.9569, abs=0.01)
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
