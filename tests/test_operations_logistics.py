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
