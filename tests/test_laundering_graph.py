"""Real-data tests for the Sanchez money-laundering graph detectors.

No mocks: every assertion runs the real graph algorithms on hand-built or
seeded networks.
"""

from __future__ import annotations

import pytest

from licence_to_kill.laundering_graph import (
    LaunderingGraphError,
    Transaction,
    TransactionGraph,
    _canonical_cycle,
    analyze_laundering,
    build_sanchez_network,
    canonical_laundering_params,
)

_SOURCES = ("S1", "S2", "S3")
_SINKS = ("B1", "B2", "B3", "B4")


# ---------------------------------------------------------------- structure
def test_canonical_cycle_rotates_to_smallest_node():
    assert _canonical_cycle(["A", "B", "C"]) == ("A", "B", "C")
    assert _canonical_cycle(["B", "C", "A"]) == ("A", "B", "C")


def test_add_transaction_and_accessors():
    g = TransactionGraph()
    g.add_transaction(Transaction("a", "b", 10.0, "cash"))
    g.add_transaction(Transaction("b", "c", 5.0))
    assert g.nodes() == ("a", "b", "c")
    assert len(g) == 2
    assert g.out_amount("a") == 10.0
    assert g.in_amount("c") == 5.0
    assert g.out_edges("a")[0].source == "a"
    assert g.in_edges("c")[0].target == "c"
    assert g.has_node("a") and not g.has_node("z")
    assert g.out_amount("missing") == 0.0


def test_from_transactions_classmethod():
    g = TransactionGraph.from_transactions([Transaction("x", "y", 1.0)])
    assert g.has_node("x") and g.has_node("y")


def test_add_transaction_validation_errors():
    g = TransactionGraph()
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(None)  # type: ignore[arg-type]
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("", "b", 1.0))
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("  ", "b", 1.0))
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("a", "", 1.0))
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("a", "a", 1.0))
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("a", "b", 0.0))
    with pytest.raises(LaunderingGraphError):
        g.add_transaction(Transaction("a", "b", -1.0))


# ---------------------------------------------------------------- layering
def _triangle() -> TransactionGraph:
    g = TransactionGraph()
    g.add_transaction(Transaction("a", "b", 1.0))
    g.add_transaction(Transaction("b", "c", 1.0))
    g.add_transaction(Transaction("c", "a", 1.0))
    return g


def test_cycle_detection_and_dedup():
    g = _triangle()
    cycles = g.find_cycles()
    assert len(cycles) == 1
    assert cycles[0] == ("a", "b", "c")


def test_cycle_depth_guard():
    with pytest.raises(LaunderingGraphError):
        _triangle().find_cycles(max_depth=2)


def test_cycle_max_cycles_cap():
    g = TransactionGraph()
    g.add_transaction(Transaction("a", "b", 1.0))
    g.add_transaction(Transaction("b", "c", 1.0))
    g.add_transaction(Transaction("c", "a", 1.0))
    g.add_transaction(Transaction("x", "y", 1.0))
    g.add_transaction(Transaction("y", "z", 1.0))
    g.add_transaction(Transaction("z", "x", 1.0))
    full = g.find_cycles()
    assert len(full) == 2
    limited = g.find_cycles(max_cycles=1)
    assert len(limited) == 1


def test_concentration_values():
    g = TransactionGraph()
    g.add_transaction(Transaction("a", "h", 1.0))
    g.add_transaction(Transaction("b", "h", 2.0))
    c = g.concentration("h")
    assert c["unique_sources"] == 2
    assert c["in_amount"] == 3.0
    assert c["funnel_ratio"] == pytest.approx(3.0)  # (2+1)/(0+1)


def test_funnels_detect_collector_and_distributor_but_not_pass_through():
    g = TransactionGraph()
    # collector hub: three sources in, one out
    g.add_transaction(Transaction("a", "h", 1.0))
    g.add_transaction(Transaction("b", "h", 1.0))
    g.add_transaction(Transaction("c", "h", 1.0))
    g.add_transaction(Transaction("h", "z", 3.0))
    # distributor: one in, three out
    g.add_transaction(Transaction("p", "q", 1.0))
    g.add_transaction(Transaction("q", "m1", 1.0))
    g.add_transaction(Transaction("q", "m2", 1.0))
    g.add_transaction(Transaction("q", "m3", 1.0))
    # trivial linear pass-through must NOT be flagged
    g.add_transaction(Transaction("solo", "solo2", 1.0))
    names = {f["node"] for f in g.funnels(threshold=1.5)}
    assert "h" in names
    assert "q" in names
    assert "solo" not in names


def test_layering_paths_dedup_and_cap():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "f1", 1.0))
    g.add_transaction(Transaction("s", "f2", 1.0))
    g.add_transaction(Transaction("f1", "b", 1.0))
    g.add_transaction(Transaction("f2", "b", 1.0))
    paths = g.layering_paths(["s"], ["b"])
    assert {tuple(p) for p in paths} == {("s", "f1", "b"), ("s", "f2", "b")}
    assert len(g.layering_paths(["s"], ["b"], max_paths=1)) == 1


def test_canonical_layering_path_count_is_exact_not_saturated():
    """C2: the reported chain count must be exact, not the enumeration cap.

    Regression: ``canonical_laundering_params()`` used to cap ``max_paths`` at
    200, which the canonical network saturated, so the reported chain count was
    really ``min(true_count, 200)`` — a lower bound reported as a count, and
    the composite depth component was computed over a truncated,
    enumeration-order-biased sample. The cap is now set strictly above the true
    count (720 here), so a default run enumerates every chain. Pin the exact
    count and assert the enumeration stays exact (and the depth component
    stable) when the cap is raised even further — if the cap ever saturates
    again, this test fails first.
    """
    params = canonical_laundering_params()
    graph = build_sanchez_network(seed=int(params["seed"]))
    full = graph.layering_paths(
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_paths=10**9,
    )
    assert len(full) == 720
    # the canonical cap must sit strictly above the true count (non-saturating)
    assert len(full) < int(params["max_paths"])
    default = analyze_laundering(
        graph,
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_cycles=int(params["max_cycles"]),
        max_paths=int(params["max_paths"]),
        funnel_threshold=float(params["funnel_threshold"]),
    )
    assert len(default.layering_paths) == len(full)
    # depth component converges on the full population; raising the cap changes
    # neither the count nor the depth statistic
    bigger = analyze_laundering(
        graph,
        params["sources"],
        params["sinks"],
        max_depth=int(params["max_depth"]),
        max_cycles=int(params["max_cycles"]),
        max_paths=10**9,
        funnel_threshold=float(params["funnel_threshold"]),
    )
    assert bigger.layering_components["depth_component"] == pytest.approx(
        default.layering_components["depth_component"]
    )


# ---------------------------------------------------------------- integration
def test_propagate_dirty_pools_at_sinks():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "m", 10.0))
    g.add_transaction(Transaction("m", "t", 4.0))
    g.add_transaction(Transaction("m", "u", 6.0))
    state = g.propagate_dirty({"s": 10.0})
    assert state["t"] == pytest.approx(4.0)
    assert state["u"] == pytest.approx(6.0)
    assert state["s"] == pytest.approx(0.0)


def test_propagate_dirty_pure_circulation_conserves_mass():
    c = TransactionGraph()
    c.add_transaction(Transaction("a", "b", 1.0))
    c.add_transaction(Transaction("b", "a", 1.0))
    state = c.propagate_dirty({"a": 5.0}, max_iter=50)
    assert abs((state["a"] + state["b"]) - 5.0) < 1e-9


def test_integration_score_dilutes_dirty():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "b", 10.0))
    g.add_transaction(Transaction("l", "b", 90.0))
    integration, fracs = g.integration_score({"s": 10.0}, ["b"])
    assert fracs["b"] == pytest.approx(0.1)
    assert integration == pytest.approx(0.9)


def test_integration_score_empty_fractions_default():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "b", 10.0))
    integration, fracs = g.integration_score({"s": 10.0}, ["no_such_sink"])
    assert fracs == {}
    # no measurable dirty at the (unknown) sinks → nothing observed as dirty
    assert integration == pytest.approx(1.0)


def test_mixing_entropy_zero_and_single():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "a", 10.0))
    g.add_transaction(Transaction("s", "b", 10.0))
    assert g.mixing_entropy({}, ["a", "b"]) == 0.0
    single = TransactionGraph()
    single.add_transaction(Transaction("s", "a", 10.0))
    assert single.mixing_entropy({"s": 10.0}, ["a"]) == pytest.approx(0.0)
    # two equal sinks → entropy log(2) nats
    assert g.mixing_entropy({"s": 10.0}, ["a", "b"]) == pytest.approx(0.693147, abs=1e-5)


# ---------------------------------------------------------------- aggregate
def test_analyze_laundering_full_report():
    g = build_sanchez_network(seed=0)
    r = analyze_laundering(g, _SOURCES, _SINKS)
    assert r.num_nodes == 22
    assert r.num_edges == 89
    assert 0.0 <= r.layering_score <= 1.0
    assert 0.0 <= r.integration_score <= 1.0
    assert r.as_dict()["num_cycles"] == len(r.cycles)
    assert r.layering_components["cycle_component"] >= 0.0


def test_analyze_laundering_acyclic_components_zero():
    g = TransactionGraph()
    g.add_transaction(Transaction("s", "b", 1.0))
    r = analyze_laundering(g, ["s"], ["b"])
    assert len(r.cycles) == 0
    assert r.layering_components["cycle_component"] == pytest.approx(0.0)


def test_build_sanchez_network_deterministic_and_seed_sensitive():
    a = build_sanchez_network(seed=0)
    b = build_sanchez_network(seed=0)
    assert a.edges() == b.edges()
    c = build_sanchez_network(seed=1)
    assert a.edges() != c.edges()
    assert len(a.edges()) == 89
