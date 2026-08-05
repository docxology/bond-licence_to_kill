"""Real-data tests for the surveillance/watchlist domain core.

Logistic detection, product-survival, exact permutation ordering, and the
ratio-rule heuristic. Deterministic — no mocks.
"""

from __future__ import annotations

import pytest

from licence_to_kill.surveillance import (
    CovertAction,
    SurveillanceModel,
    SurveillanceReport,
    analyze_surveillance,
    canonical_surveillance_params,
    compromise_step,
    detection_probability,
    exact_action_order,
    heuristic_action_order,
    optimal_action_order,
    simulate_sequence,
)


def _params():
    params = canonical_surveillance_params()
    return tuple(params["actions"]), params["model"]


def _action(**overrides) -> CovertAction:
    base = dict(name="a", signature=0.05, watch_increment=0.5, value=3.0)
    base.update(overrides)
    return CovertAction(**base)


def _model(**overrides) -> SurveillanceModel:
    base = dict(beta_0=-4.0, beta_watch=1.2, beta_signature=1.5, detection_threshold=0.5)
    base.update(overrides)
    return SurveillanceModel(**base)


# ------------------------------------------------------------- validation
def test_covert_action_validation_errors():
    with pytest.raises(ValueError):
        CovertAction("", 0.05, 0.5, 3.0)
    with pytest.raises(ValueError):
        CovertAction("a", -0.1, 0.5, 3.0)
    with pytest.raises(ValueError):
        CovertAction("a", 1.0, 0.5, 3.0)
    with pytest.raises(ValueError):
        CovertAction("a", 0.05, 0.0, 3.0)
    with pytest.raises(ValueError):
        CovertAction("a", 0.05, 0.5, -1.0)


def test_surveillance_model_validation_errors():
    with pytest.raises(ValueError):
        SurveillanceModel(-4.0, beta_watch=-1.0, beta_signature=1.5)
    with pytest.raises(ValueError):
        SurveillanceModel(-4.0, beta_watch=1.2, beta_signature=-0.5)
    with pytest.raises(ValueError):
        SurveillanceModel(-4.0, beta_watch=1.2, beta_signature=1.5, detection_threshold=0.0)
    with pytest.raises(ValueError):
        SurveillanceModel(-4.0, beta_watch=1.2, beta_signature=1.5, detection_threshold=1.0)


# ------------------------------------------------------------- detection
def test_detection_probability_bounds_and_monotonic():
    model = _model()
    p0 = detection_probability(_action(signature=0.02), 0.0, model)
    assert 0.0 < p0 < 1.0
    # more watch weight -> higher hazard
    assert detection_probability(_action(signature=0.02), 2.0, model) > p0
    # higher signature -> higher hazard
    assert detection_probability(_action(signature=0.2), 0.0, model) > p0
    # sufficient watch/signature drives the logistic into the z >= 0 branch
    assert detection_probability(_action(signature=0.2), 10.0, model) > 0.9


def test_ratio_key_zero_exposure_returns_inf():
    # beta_watch == 0 and a zero-signature action contributes no exposure
    model = SurveillanceModel(beta_0=-4.0, beta_watch=0.0, beta_signature=1.5, detection_threshold=0.5)
    actions = (_action(name="zero", signature=0.0, value=5.0), _action(name="hi", signature=0.5, value=4.0))
    ordered = heuristic_action_order(actions, model)
    assert ordered[0].name == "zero"  # infinite ratio sorts first


# ------------------------------------------------------------- sequence
def test_simulate_sequence_product_and_traces():
    actions, model = _params()
    success, steps = simulate_sequence(actions, model)
    assert len(steps) == 5
    # success == product of (1 - hazard)
    product = 1.0
    for entry in steps:
        product *= 1.0 - float(entry["hazard"])
    assert success == pytest.approx(product)
    assert float(steps[-1]["cumulative_detection"]) == pytest.approx(1.0 - success)
    assert steps[0]["step"] == 0
    assert steps[0]["watch"] == 0.0


def test_canonical_surveillance_success():
    actions, model = _params()
    _order, success = optimal_action_order(actions, model)
    assert success == pytest.approx(0.2634, abs=0.001)


# ------------------------------------------------------------- compromise
def test_compromise_step_within_and_never():
    actions, model = _params()
    assert compromise_step(actions, model) == 4
    # an unreachable high threshold returns None
    assert compromise_step(actions, model, threshold=0.9) is None


def test_compromise_step_threshold_validation():
    actions, model = _params()
    with pytest.raises(ValueError):
        compromise_step(actions, model, threshold=0.0)
    with pytest.raises(ValueError):
        compromise_step(actions, model, threshold=1.0)


# ------------------------------------------------------------- ordering
def test_heuristic_action_order_deterministic_and_ratio():
    actions, model = _params()
    ordered = heuristic_action_order(actions, model)
    assert tuple(sorted(a.name for a in ordered)) == tuple(sorted(a.name for a in actions))
    # highest value-per-exposure action is first
    assert ordered[0].name == "observe_isthmus_house"


def test_exact_action_order_matches_optimal_for_small_n():
    actions, model = _params()
    exact_order, exact_success = exact_action_order(actions, model)
    assert len(exact_order) == len(actions)
    assert exact_success == pytest.approx(0.2634, abs=0.001)
    # exact is at least as good as the heuristic
    heuristic = heuristic_action_order(actions, model)
    heuristic_success, _ = simulate_sequence(heuristic, model)
    assert exact_success >= heuristic_success - 1e-12


def test_exact_action_order_empty_and_overflow():
    assert exact_action_order((), _model()) == ((), 1.0)
    nine = tuple(_action(name=f"a{i}") for i in range(9))
    with pytest.raises(ValueError):
        exact_action_order(nine, _model())


def test_optimal_action_order_heuristic_for_large_n():
    nine = tuple(_action(name=f"a{i}", value=float(i + 1)) for i in range(9))
    order, success = optimal_action_order(nine, _model())
    assert len(order) == 9
    assert success == pytest.approx(simulate_sequence(order, _model())[0])
    # matches the heuristic for n > 8
    heuristic = heuristic_action_order(nine, _model())
    assert tuple(a.name for a in order) == tuple(a.name for a in heuristic)


# ------------------------------------------------------------- aggregate
def test_analyze_surveillance_canonical_report():
    actions, model = _params()
    report = analyze_surveillance(actions, model)
    assert isinstance(report, SurveillanceReport)
    assert report.success_probability == pytest.approx(0.2634, abs=0.001)
    assert report.compromise_step == 4
    assert report.peak_hazard == pytest.approx(0.633, abs=0.01)
    assert report.optimal_order[0] == "observe_isthmus_house"
    assert report.model_threshold == 0.5
    assert len(report.steps) == 5


def test_analyze_surveillance_deterministic():
    actions, model = _params()
    a = analyze_surveillance(actions, model).as_dict()
    b = analyze_surveillance(actions, model).as_dict()
    assert a == b


def test_canonical_surveillance_params_shape():
    params = canonical_surveillance_params()
    assert len(params["actions"]) == 5
    assert params["model"].detection_threshold == 0.5
