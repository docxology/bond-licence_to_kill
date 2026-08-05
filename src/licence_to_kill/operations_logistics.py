"""Operations logistics — risk-adjusted routing, gadget loadout, trip planning.

The ROGUE mission's fifth domain: the *physical* campaign behind the
finance. The operator must move the Wavekrest-class mothership and its cargo
between Isthmus City, Hong Kong, and Florida; pick which gadgets ride along
under a weight budget; and schedule the legs against the vessel's speed and
fuel endurance. This module provides:

- ``OperationNetwork`` + ``shortest_path`` — Dijkstra's algorithm
  [@dijkstra1959] over leg distance, dollar cost, or *cumulative risk*
  (edge weight −ln(1−r) makes the product survival metric additive);
- ``gadget_knapsack`` — exact 0/1 knapsack by dynamic programming
  [@kellerer2004] for the equipment loadout;
- ``trip_plan`` — leg-by-leg endurance/refuel feasibility and elapsed-time
  projection.

All algorithms are deterministic (heap-based Dijkstra with string tie-breaks,
integer-scaled knapsack DP, closed-form trip arithmetic). Pure stdlib only.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Any, Iterable

__all__ = [
    "GadgetItem",
    "KnapsackResult",
    "MissionLeg",
    "OperationNetwork",
    "OperationsLogisticsReport",
    "RouteResult",
    "TripPlan",
    "analyze_operations_logistics",
    "canonical_logistics_params",
    "gadget_knapsack",
    "shortest_path",
    "trip_plan",
]

#: Weight keys accepted by :func:`shortest_path`.
WEIGHT_KEYS = ("risk", "cost", "distance")


@dataclass(frozen=True)
class MissionLeg:
    """A single transport leg: origin → destination with economics and risk."""

    origin: str
    destination: str
    distance_nm: float
    cost: float
    risk: float

    def __post_init__(self) -> None:
        if not (isinstance(self.origin, str) and self.origin.strip()):
            raise ValueError("MissionLeg.origin must be a non-empty string")
        if not (isinstance(self.destination, str) and self.destination.strip()):
            raise ValueError("MissionLeg.destination must be a non-empty string")
        if self.origin == self.destination:
            raise ValueError("MissionLeg origin and destination must differ")
        if not (isinstance(self.distance_nm, (int, float)) and self.distance_nm > 0):
            raise ValueError("MissionLeg.distance_nm must be a positive number")
        if not (isinstance(self.cost, (int, float)) and self.cost >= 0):
            raise ValueError("MissionLeg.cost must be a non-negative number")
        if not (isinstance(self.risk, (int, float)) and 0.0 <= self.risk < 1.0):
            raise ValueError("MissionLeg.risk must be in [0, 1)")

    def as_dict(self) -> dict[str, object]:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "distance_nm": self.distance_nm,
            "cost": self.cost,
            "risk": self.risk,
        }


@dataclass(frozen=True)
class GadgetItem:
    """A candidate gadget for the loadout: name, weight, mission value."""

    name: str
    weight_kg: float
    value: float

    def __post_init__(self) -> None:
        if not (isinstance(self.name, str) and self.name.strip()):
            raise ValueError("GadgetItem.name must be a non-empty string")
        if not (isinstance(self.weight_kg, (int, float)) and self.weight_kg >= 0):
            raise ValueError("GadgetItem.weight_kg must be a non-negative number")
        if not (isinstance(self.value, (int, float)) and self.value >= 0):
            raise ValueError("GadgetItem.value must be a non-negative number")


class OperationNetwork:
    """Directed weighted graph of mission legs, insertion-ordered."""

    def __init__(self, legs: Iterable[MissionLeg] = ()) -> None:
        self._legs: list[MissionLeg] = []
        self._out: dict[str, list[MissionLeg]] = {}
        for leg in legs:
            self.add_leg(leg)

    def add_leg(self, leg: MissionLeg) -> None:
        """Append a validated leg."""
        if not isinstance(leg, MissionLeg):
            raise ValueError("expected a MissionLeg")
        self._legs.append(leg)
        self._out.setdefault(leg.origin, []).append(leg)
        self._out.setdefault(leg.destination, [])

    def nodes(self) -> tuple[str, ...]:
        return tuple(self._out)

    def legs(self) -> tuple[MissionLeg, ...]:
        return tuple(self._legs)

    def legs_from(self, origin: str) -> tuple[MissionLeg, ...]:
        return tuple(self._out.get(origin, ()))

    def has_node(self, node: str) -> bool:
        return node in self._out

    def __len__(self) -> int:
        return len(self._legs)


@dataclass(frozen=True)
class RouteResult:
    """The optimal route: path, constituent legs, and aggregate metrics."""

    path: tuple[str, ...]
    legs: tuple[MissionLeg, ...]
    total_cost: float
    total_distance_nm: float
    cumulative_risk: float
    weight: str

    def as_dict(self) -> dict[str, object]:
        return {
            "path": list(self.path),
            "legs": [leg.as_dict() for leg in self.legs],
            "total_cost": self.total_cost,
            "total_distance_nm": self.total_distance_nm,
            "cumulative_risk": self.cumulative_risk,
            "weight": self.weight,
        }


def _edge_weight(leg: MissionLeg, weight: str) -> float:
    if weight == "risk":
        # -ln(1-r) is additive and order-isomorphic to the product survival metric.
        return float(-math.log1p(-leg.risk))
    if weight == "cost":
        return float(leg.cost)
    return float(leg.distance_nm)


def shortest_path(
    network: OperationNetwork,
    origin: str,
    destination: str,
    weight: str = "risk",
) -> RouteResult | None:
    """Dijkstra's algorithm; ``None`` when ``destination`` is unreachable."""
    if weight not in WEIGHT_KEYS:
        raise ValueError(f"weight must be one of {WEIGHT_KEYS}")
    if not network.has_node(origin) or not network.has_node(destination):
        raise ValueError(f"unknown node: {origin if not network.has_node(origin) else destination!r}")

    dist: dict[str, float] = {origin: 0.0}
    prev: dict[str, tuple[str, MissionLeg]] = {}
    heap: list[tuple[float, str]] = [(0.0, origin)]
    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist > dist.get(node, math.inf):
            continue
        if node == destination:
            break
        for leg in network.legs_from(node):
            candidate = current_dist + _edge_weight(leg, weight)
            if candidate < dist.get(leg.destination, math.inf):
                dist[leg.destination] = candidate
                prev[leg.destination] = (node, leg)
                heapq.heappush(heap, (candidate, leg.destination))

    if destination not in dist:
        return None

    path: list[str] = [destination]
    legs: list[MissionLeg] = []
    node = destination
    while node != origin:
        node, leg = prev[node]
        path.append(node)
        legs.append(leg)
    path.reverse()
    legs.reverse()
    total_cost = sum(leg.cost for leg in legs)
    total_distance = sum(leg.distance_nm for leg in legs)
    survival = math.prod(1.0 - leg.risk for leg in legs)
    return RouteResult(
        path=tuple(path),
        legs=tuple(legs),
        total_cost=float(total_cost),
        total_distance_nm=float(total_distance),
        cumulative_risk=float(1.0 - survival),
        weight=weight,
    )


@dataclass(frozen=True)
class KnapsackResult:
    """The optimal 0/1-knapsack loadout."""

    names: tuple[str, ...]
    value: float
    weight_kg: float

    def as_dict(self) -> dict[str, object]:
        return {
            "names": list(self.names),
            "value": self.value,
            "weight_kg": self.weight_kg,
        }


def gadget_knapsack(items: tuple[GadgetItem, ...], capacity_kg: float) -> KnapsackResult:
    """Exact 0/1 knapsack by DP over gram-scaled weights."""
    if capacity_kg <= 0.0:
        raise ValueError("capacity_kg must be positive")
    if not items:
        return KnapsackResult((), 0.0, 0.0)

    scale = 1000
    capacity = int(round(capacity_kg * scale))
    weights = [int(round(item.weight_kg * scale)) for item in items]
    values = [float(item.value) for item in items]
    count = len(items)

    # dp[c] = best value achievable with capacity c (grams); selected[i][c]
    # records whether item i is part of the optimum at capacity c, decided at
    # item i's own pass so the reconstruction walk stays consistent (a plain
    # final-array equality check false-negatives once dp[c-w] already
    # contains the item).
    dp: list[float] = [0.0] * (capacity + 1)
    selected: list[list[bool]] = [[False] * (capacity + 1) for _ in range(count)]
    for i in range(count):
        w = weights[i]
        if w > capacity:
            continue
        v = values[i]
        for c in range(capacity, w - 1, -1):
            candidate = dp[c - w] + v
            if candidate > dp[c]:
                dp[c] = candidate
                selected[i][c] = True

    # Reconstruct deterministically by walking items in reverse order.
    chosen: list[int] = []
    c = capacity
    for i in range(count - 1, -1, -1):
        if selected[i][c]:
            chosen.append(i)
            c -= weights[i]
    chosen.reverse()
    names = tuple(items[i].name for i in chosen)
    total_weight = sum(items[i].weight_kg for i in chosen)
    return KnapsackResult(names=names, value=float(dp[capacity]), weight_kg=float(total_weight))


@dataclass(frozen=True)
class TripPlan:
    """Leg-by-leg endurance feasibility, refuelling load, and elapsed time."""

    feasible: bool
    total_hours: float
    refuels: int
    segments: tuple[dict[str, object], ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feasible": self.feasible,
            "total_hours": self.total_hours,
            "refuels": self.refuels,
            "segments": [dict(s) for s in self.segments],
            "reason": self.reason,
        }


def trip_plan(
    legs: tuple[MissionLeg, ...],
    speed_knots: float,
    endurance_nm: float,
    refuel_hours: float = 24.0,
    allow_mid_leg_refuel: bool = True,
) -> TripPlan:
    """Project a voyage: per-leg hours, refuel stops, and total elapsed time."""
    if speed_knots <= 0.0:
        raise ValueError("speed_knots must be positive")
    if endurance_nm <= 0.0:
        raise ValueError("endurance_nm must be positive")
    if refuel_hours < 0.0:
        raise ValueError("refuel_hours must be non-negative")

    total_hours = 0.0
    refuels = 0
    segments: list[dict[str, object]] = []
    for leg in legs:
        if leg.distance_nm > endurance_nm and not allow_mid_leg_refuel:
            return TripPlan(
                False,
                0.0,
                0,
                (),
                f"leg {leg.origin}->{leg.destination} exceeds single-tank endurance",
            )
        seg_refuels = 0
        if allow_mid_leg_refuel and leg.distance_nm > endurance_nm:
            seg_refuels = math.ceil(leg.distance_nm / endurance_nm) - 1
        hours = leg.distance_nm / speed_knots + seg_refuels * refuel_hours
        total_hours += hours
        refuels += seg_refuels
        segments.append(
            {
                "origin": leg.origin,
                "destination": leg.destination,
                "distance_nm": leg.distance_nm,
                "hours": hours,
                "refuels": seg_refuels,
            }
        )
    return TripPlan(True, float(total_hours), refuels, tuple(segments), "ok")


@dataclass(frozen=True)
class OperationsLogisticsReport:
    """Deterministic operations-logistics summary for one campaign."""

    origin: str
    destination: str
    route: RouteResult
    loadout: KnapsackResult
    trip: TripPlan

    def as_dict(self) -> dict[str, object]:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "route": self.route.as_dict(),
            "loadout": self.loadout.as_dict(),
            "trip": self.trip.as_dict(),
        }


def analyze_operations_logistics(
    network: OperationNetwork,
    origin: str,
    destination: str,
    gadgets: tuple[GadgetItem, ...],
    capacity_kg: float,
    speed_knots: float,
    endurance_nm: float,
    refuel_hours: float = 24.0,
) -> OperationsLogisticsReport:
    """Run the full logistics pass: route, loadout, and voyage projection."""
    route = shortest_path(network, origin, destination, weight="risk")
    if route is None:
        raise ValueError(f"{destination!r} is unreachable from {origin!r}")
    return OperationsLogisticsReport(
        origin=origin,
        destination=destination,
        route=route,
        loadout=gadget_knapsack(gadgets, capacity_kg),
        trip=trip_plan(route.legs, speed_knots, endurance_nm, refuel_hours),
    )


def canonical_logistics_params() -> dict[str, Any]:
    """Single source of truth for the canonical logistics scenario.

    Legs connect the film's operational hubs: Isthmus City (IC), the refinery
    at Bogota (BOG), Hong Kong (HK), and Florida (FL). The Wavekrest-class
    endurance (~4,257 nm at cruise) and a 25 kg gadget budget drive the
    knapsack and voyage projection. Used by both ``mission.py`` and
    ``manuscript_variables.py``.
    """
    return {
        "origin": "IC",
        "destination": "FL",
        "legs": (
            MissionLeg("IC", "HK", 8300.0, 120_000.0, 0.10),
            MissionLeg("HK", "FL", 8700.0, 150_000.0, 0.12),
            MissionLeg("IC", "FL", 12000.0, 90_000.0, 0.30),
            MissionLeg("IC", "BOG", 900.0, 8_000.0, 0.04),
            MissionLeg("BOG", "HK", 9800.0, 110_000.0, 0.15),
        ),
        "gadgets": (
            GadgetItem("Walther PPK", 0.7, 6.0),
            GadgetItem("explosive charges", 8.0, 10.0),
            GadgetItem("diving gear", 15.0, 7.0),
            GadgetItem("fishing cover stores", 40.0, 9.0),
            GadgetItem("surveillance kit", 4.0, 8.0),
            GadgetItem("first aid", 2.0, 3.0),
            GadgetItem("stinger missile", 3.0, 5.0),
        ),
        "capacity_kg": 25.0,
        "speed_knots": 10.0,
        "endurance_nm": 4257.0,
        "refuel_hours": 24.0,
    }
