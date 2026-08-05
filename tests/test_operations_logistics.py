"""Real-data tests for the operations-logistics domain core.

Dijkstra routing, 0/1-knapsack loadout, and trip planning — all against the
canonical campaign. No mocks.
"""

from __future__ import annotations

import pytest

from licence_to_kill.operations_logistics import (
    GadgetItem,
    KnapsackResult,
    MissionLeg,
    OperationNetwork,
    OperationsLogisticsReport,
    RouteResult,
    TripPlan,
    analyze_operations_logistics,
    canonical_logistics_params,
    direct_leg,
    gadget_knapsack,
    shortest_path,
    trip_plan,
)


def _params():
    return canonical_logistics_params()


def _network():
    params = _params()
    return OperationNetwork(params["legs"])


# --------------------------------------------------------------- dataclasses
def test_mission_leg_validation_errors():
    good = dict(origin="A", destination="B", distance_nm=100.0, cost=10.0, risk=0.1)
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "origin": ""})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "destination": " "})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "destination": "A"})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "distance_nm": 0.0})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "cost": -1.0})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "risk": -0.1})
    with pytest.raises(ValueError):
        MissionLeg(**{**good, "risk": 1.0})


def test_gadget_item_validation_errors():
    with pytest.raises(ValueError):
        GadgetItem("", 1.0, 1.0)
    with pytest.raises(ValueError):
        GadgetItem("x", -1.0, 1.0)
    with pytest.raises(ValueError):
        GadgetItem("x", 1.0, -1.0)


def test_network_construction():
    net = _network()
    assert net.has_node("IC") and net.has_node("FL")
    assert "BOG" in net.nodes()
    assert len(net) == 5
    assert net.legs_from("IC")  # non-empty
    with pytest.raises(ValueError):
        net.add_leg("not a leg")  # type: ignore[arg-type]


# --------------------------------------------------------------- routing
def test_shortest_path_by_risk():
    route = shortest_path(_network(), "IC", "FL", weight="risk")
    assert route is not None
    assert isinstance(route, RouteResult)
    assert route.path == ("IC", "HK", "FL")
    assert route.cumulative_risk == pytest.approx(0.208)  # 1 - 0.9*0.88
    assert route.total_cost == pytest.approx(270_000.0)
    assert route.total_distance_nm == pytest.approx(17_000.0)
    assert route.weight == "risk"


def test_shortest_path_by_cost_and_distance():
    cost = shortest_path(_network(), "IC", "FL", weight="cost")
    dist = shortest_path(_network(), "IC", "FL", weight="distance")
    assert cost is not None and dist is not None
    assert cost.path == ("IC", "FL")
    assert cost.total_cost == pytest.approx(90_000.0)
    assert dist.path == ("IC", "FL")
    assert dist.total_distance_nm == pytest.approx(12_000.0)


def test_shortest_path_reachable_and_errors():
    # BOG reaches FL only via HK (BOG->HK->FL): check risk path from BOG
    route = shortest_path(_network(), "BOG", "FL", weight="risk")
    assert route is not None
    assert route.path[0] == "BOG" and route.path[-1] == "FL"

    with pytest.raises(ValueError):
        shortest_path(_network(), "IC", "NOPE")
    with pytest.raises(ValueError):
        shortest_path(_network(), "NOPE", "FL")
    with pytest.raises(ValueError):
        shortest_path(_network(), "IC", "FL", weight="time")


def test_shortest_path_stale_heap_entry_skipped():
    # B is first reached expensively via A, then more cheaply via C, so the
    # first (stale) heap entry for B pops before D finalizes and hits the
    # `continue` guard. An expensive B→D leg keeps D behind the stale entry.
    net = OperationNetwork(
        [
            MissionLeg("A", "B", 50.0, 5.0, 0.0),
            MissionLeg("A", "C", 10.0, 1.0, 0.0),
            MissionLeg("C", "B", 10.0, 1.0, 0.0),
            MissionLeg("B", "D", 10.0, 100.0, 0.0),
        ]
    )
    route = shortest_path(net, "A", "D", weight="cost")
    assert route is not None
    assert route.total_cost == pytest.approx(102.0)


def test_shortest_path_unreachable_known_returns_none():
    # A and D are both valid nodes (D appears as a target) but no path exists.
    net = OperationNetwork([MissionLeg("A", "B", 10.0, 1.0, 0.0), MissionLeg("C", "D", 5.0, 1.0, 0.0)])
    assert shortest_path(net, "A", "D") is None


def test_direct_leg_returns_the_single_leg_or_none():
    params = _params()
    net = OperationNetwork(params["legs"])
    leg = direct_leg(net, "IC", "FL")
    assert leg is not None
    assert (leg.origin, leg.destination) == ("IC", "FL")
    assert leg.risk == pytest.approx(0.30)
    # BOG has no direct leg to FL even though FL is reachable via HK
    assert direct_leg(net, "BOG", "FL") is None


def test_direct_leg_differs_from_distance_minimal_path_in_general():
    """They coincide on the canonical network; that is a coincidence, not a rule."""
    net = OperationNetwork(
        (
            MissionLeg("A", "B", 100.0, 1.0, 0.5),
            MissionLeg("A", "C", 10.0, 1.0, 0.1),
            MissionLeg("C", "B", 10.0, 1.0, 0.1),
        )
    )
    leg = direct_leg(net, "A", "B")
    assert leg is not None and leg.risk == pytest.approx(0.5)
    by_distance = shortest_path(net, "A", "B", weight="distance")
    assert by_distance is not None
    assert by_distance.path == ("A", "C", "B")
    assert by_distance.cumulative_risk != pytest.approx(leg.risk)


# --------------------------------------------------------------- knapsack
def test_knapsack_canonical():
    params = _params()
    result = gadget_knapsack(params["gadgets"], params["capacity_kg"])
    assert isinstance(result, KnapsackResult)
    assert result.value == pytest.approx(32.0)
    assert result.weight_kg == pytest.approx(17.7)
    assert set(result.names) == {"Walther PPK", "explosive charges", "surveillance kit", "first aid", "stinger missile"}


def test_knapsack_simple_known_optimum():
    items = (GadgetItem("a", 2.0, 3.0), GadgetItem("b", 3.0, 4.0), GadgetItem("c", 4.0, 5.0))
    result = gadget_knapsack(items, 5.0)
    # capacity 5 kg: a+b = 5 kg value 7 beats c (4kg value 5)
    assert result.value == pytest.approx(7.0)
    assert set(result.names) == {"a", "b"}


def test_knapsack_empty_and_errors():
    assert gadget_knapsack((), 10.0).value == 0.0
    with pytest.raises(ValueError):
        gadget_knapsack((GadgetItem("a", 1.0, 1.0),), 0.0)
    # an item heavier than capacity is simply skipped
    result = gadget_knapsack((GadgetItem("heavy", 100.0, 50.0), GadgetItem("light", 1.0, 2.0)), 10.0)
    assert result.names == ("light",)


def _greedy_value_density(items: tuple[GadgetItem, ...], capacity_kg: float) -> KnapsackResult:
    """The heuristic the exact DP is contrasted against, implemented for real.

    Sort by value per kilogram (name as the deterministic tie-break), take
    greedily while the item fits. This is not a helper the package ships — it
    exists so the manuscript's comparison against greedy is *measured* rather
    than asserted.
    """
    order = sorted(items, key=lambda item: (-(item.value / item.weight_kg), item.name))
    names: list[str] = []
    weight = 0.0
    value = 0.0
    for item in order:
        if weight + item.weight_kg <= capacity_kg:
            names.append(item.name)
            weight += item.weight_kg
            value += item.value
    return KnapsackResult(tuple(names), value, weight)


def test_greedy_matches_exact_on_the_canonical_instance():
    """On the canonical gadget set, greedy and the exact DP agree exactly.

    The manuscript used to present the loadout as "the exact optimum, not a
    greedy value-density pick", implying the two differ here. They do not:
    same five items, same value, same weight. This test pins that fact so the
    prose cannot quietly drift back to claiming a contrast that the numbers
    do not support.
    """
    params = _params()
    exact = gadget_knapsack(params["gadgets"], params["capacity_kg"])
    greedy = _greedy_value_density(params["gadgets"], params["capacity_kg"])
    assert set(greedy.names) == set(exact.names)
    assert greedy.value == pytest.approx(exact.value)
    assert greedy.weight_kg == pytest.approx(exact.weight_kg)


def test_greedy_value_density_is_suboptimal_on_a_counterexample():
    """The DP's guarantee is instance-independent; greedy's is not.

    Capacity 10 kg. Greedy ranks by value/kg: the decoy (1 kg, value 6,
    density 6.0) first, then one 5 kg / value 10 item — 6 kg used, value 16,
    and nothing else fits. The exact optimum drops the decoy and takes both
    5 kg items: 10 kg, value 20. This is the claim the manuscript actually
    makes for the exact solver, and it is checked rather than asserted.
    """
    items = (
        GadgetItem("dense_decoy", 1.0, 6.0),
        GadgetItem("pair_a", 5.0, 10.0),
        GadgetItem("pair_b", 5.0, 10.0),
        GadgetItem("filler", 9.0, 9.0),
    )
    exact = gadget_knapsack(items, 10.0)
    greedy = _greedy_value_density(items, 10.0)
    assert exact.value == pytest.approx(20.0)
    assert set(exact.names) == {"pair_a", "pair_b"}
    assert greedy.value == pytest.approx(16.0)
    assert set(greedy.names) == {"dense_decoy", "pair_a"}
    assert greedy.value < exact.value


def test_knapsack_deterministic():
    params = _params()
    a = gadget_knapsack(params["gadgets"], params["capacity_kg"]).as_dict()
    b = gadget_knapsack(params["gadgets"], params["capacity_kg"]).as_dict()
    assert a == b


# --------------------------------------------------------------- trip plan
def test_trip_plan_feasible_with_refuels():
    legs = (MissionLeg("IC", "HK", 8300.0, 1.0, 0.1), MissionLeg("HK", "FL", 8700.0, 1.0, 0.1))
    plan = trip_plan(legs, speed_knots=10.0, endurance_nm=4257.0, refuel_hours=24.0)
    assert isinstance(plan, TripPlan)
    assert plan.feasible is True
    assert plan.refuels == 3  # ceil(8300/4257)-1 + ceil(8700/4257)-1 = 1 + 2
    assert plan.total_hours == pytest.approx(1700.0 + 3 * 24.0)


def test_trip_plan_infeasible_without_mid_leg_refuel():
    legs = (MissionLeg("IC", "FL", 12000.0, 1.0, 0.3),)
    plan = trip_plan(legs, speed_knots=10.0, endurance_nm=4257.0, allow_mid_leg_refuel=False)
    assert plan.feasible is False
    assert "exceeds" in plan.reason


def test_trip_plan_short_leg_no_mid_refuel():
    legs = (MissionLeg("A", "B", 100.0, 1.0, 0.1),)
    plan = trip_plan(legs, speed_knots=10.0, endurance_nm=200.0, allow_mid_leg_refuel=False)
    assert plan.feasible is True
    assert plan.refuels == 0
    assert plan.total_hours == pytest.approx(10.0)


def test_trip_plan_errors():
    legs = (MissionLeg("A", "B", 100.0, 1.0, 0.1),)
    with pytest.raises(ValueError):
        trip_plan(legs, 0.0, 4257.0)
    with pytest.raises(ValueError):
        trip_plan(legs, 10.0, 0.0)
    with pytest.raises(ValueError):
        trip_plan(legs, 10.0, 4257.0, refuel_hours=-1.0)


def test_trip_plan_deterministic():
    legs = (MissionLeg("IC", "HK", 8300.0, 1.0, 0.1),)
    a = trip_plan(legs, 10.0, 4257.0).as_dict()
    b = trip_plan(legs, 10.0, 4257.0).as_dict()
    assert a == b


# --------------------------------------------------------------- aggregate
def test_analyze_operations_logistics_canonical():
    params = _params()
    report = analyze_operations_logistics(
        _network(),
        str(params["origin"]),
        str(params["destination"]),
        params["gadgets"],
        float(params["capacity_kg"]),
        float(params["speed_knots"]),
        float(params["endurance_nm"]),
        float(params["refuel_hours"]),
    )
    assert isinstance(report, OperationsLogisticsReport)
    assert report.route.path == ("IC", "HK", "FL")
    assert report.loadout.value == pytest.approx(32.0)
    assert report.trip.refuels == 3
    assert report.as_dict()["origin"] == "IC"


def test_analyze_operations_logistics_unreachable_raises():
    net = OperationNetwork([MissionLeg("A", "B", 10.0, 1.0, 0.0), MissionLeg("C", "D", 5.0, 1.0, 0.0)])
    with pytest.raises(ValueError):
        analyze_operations_logistics(net, "A", "D", (), 10.0, 10.0, 1000.0)
