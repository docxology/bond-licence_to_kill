"""Surveillance and watchlist — detection risk over a covert-action sequence.

The ROGUE mission's sixth domain: an unsanctioned operator survives only as
long as the adversary's surveillance apparatus does not catch him. Each
covert action carries a *signature* (how detectable it is) and *watch
increment* (how much it teaches the adversary's watchlist). The probability
of being detected on step t is a logistic function of the accumulated
watchlist weight plus the action's signature; the sequence succeeds only if
every step goes undetected.

This module computes, deterministically:

- ``detection_probability`` — the logistic hazard;
- ``simulate_sequence`` / ``compromise_step`` — product-survival over a
  given order and the first step at which cumulative detection crosses a
  threshold;
- ``exact_action_order`` — exhaustive permutation search (n ≤ 8) for the
  order that maximises survival;
- ``heuristic_action_order`` — a ratio rule (Smith's scheduling rule
  [@smith1956]) for large action sets.

Pure stdlib only; no RNG.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Sequence

__all__ = [
    "EXACT_ORDER_LIMIT",
    "CovertAction",
    "SurveillanceModel",
    "SurveillanceReport",
    "analyze_surveillance",
    "canonical_surveillance_params",
    "compromise_step",
    "detection_probability",
    "exact_action_order",
    "heuristic_action_order",
    "optimal_action_order",
    "simulate_sequence",
]

#: Exact search is factorial; cap it at 8! = 40,320 permutations.
EXACT_ORDER_LIMIT = 8


def _logistic(z: float) -> float:
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1.0 + exp_z)


@dataclass(frozen=True)
class CovertAction:
    """A single covert action: detectability, watchlist feedback, value."""

    name: str
    signature: float
    watch_increment: float
    value: float

    def __post_init__(self) -> None:
        if not (isinstance(self.name, str) and self.name.strip()):
            raise ValueError("CovertAction.name must be a non-empty string")
        if not (isinstance(self.signature, (int, float)) and 0.0 <= self.signature < 1.0):
            raise ValueError("CovertAction.signature must be in [0, 1)")
        if not (isinstance(self.watch_increment, (int, float)) and self.watch_increment > 0.0):
            raise ValueError("CovertAction.watch_increment must be positive")
        if not (isinstance(self.value, (int, float)) and self.value >= 0.0):
            raise ValueError("CovertAction.value must be non-negative")


@dataclass(frozen=True)
class SurveillanceModel:
    """Parameters of the adversary's watchlist / detection process."""

    beta_0: float
    beta_watch: float
    beta_signature: float
    detection_threshold: float = 0.5

    def __post_init__(self) -> None:
        if not (isinstance(self.beta_watch, (int, float)) and self.beta_watch >= 0.0):
            raise ValueError("SurveillanceModel.beta_watch must be non-negative")
        if not (isinstance(self.beta_signature, (int, float)) and self.beta_signature >= 0.0):
            raise ValueError("SurveillanceModel.beta_signature must be non-negative")
        if not (isinstance(self.detection_threshold, (int, float)) and 0.0 < self.detection_threshold < 1.0):
            raise ValueError("SurveillanceModel.detection_threshold must be in (0, 1)")


def detection_probability(
    action: CovertAction,
    watch: float,
    model: SurveillanceModel,
) -> float:
    """Logistic hazard: P(detected) = σ(β₀ + β_w·watch + β_s·signature)."""
    z = model.beta_0 + model.beta_watch * watch + model.beta_signature * action.signature
    return _logistic(float(z))


def simulate_sequence(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
) -> tuple[float, tuple[dict[str, float | str | int], ...]]:
    """Simulate an action order; return ``(success_prob, per-step traces)``."""
    watch = 0.0
    success = 1.0
    steps: list[dict[str, float | str | int]] = []
    for index, action in enumerate(actions):
        hazard = detection_probability(action, watch, model)
        success *= 1.0 - hazard
        steps.append(
            {
                "step": index,
                "action": action.name,
                "watch": watch,
                "hazard": hazard,
                "cumulative_detection": 1.0 - success,
            }
        )
        watch += action.watch_increment
    return float(success), tuple(steps)


def compromise_step(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
    threshold: float | None = None,
) -> int | None:
    """First step index where cumulative detection reaches the threshold."""
    level = model.detection_threshold if threshold is None else threshold
    if not (0.0 < level < 1.0):
        raise ValueError("threshold must be in (0, 1)")
    _, steps = simulate_sequence(actions, model)
    for entry in steps:
        if float(entry["cumulative_detection"]) >= level:
            return int(entry["step"])
    return None


def _ratio_key(action: CovertAction, model: SurveillanceModel) -> float:
    """Value per unit of watchlist exposure contributed by the action."""
    exposure = model.beta_watch * action.watch_increment + model.beta_signature * action.signature
    if exposure <= 0.0:
        return math.inf
    return float(action.value / exposure)


def heuristic_action_order(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
) -> tuple[CovertAction, ...]:
    """Ratio-rule ordering: highest value-per-exposure first (Smith's rule)."""
    ordered = sorted(actions, key=lambda a: -_ratio_key(a, model))
    return tuple(ordered)


def exact_action_order(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
) -> tuple[tuple[CovertAction, ...], float]:
    """Exhaustive permutation search for maximum survival probability."""
    if len(actions) > EXACT_ORDER_LIMIT:
        raise ValueError(f"exact search limited to {EXACT_ORDER_LIMIT} actions")
    if not actions:
        return (), 1.0
    best_order: tuple[CovertAction, ...] | None = None
    best_success = -math.inf
    for candidate in itertools.permutations(actions):
        success, _ = simulate_sequence(candidate, model)
        if success > best_success:
            best_success = success
            best_order = candidate
    assert best_order is not None
    return best_order, float(best_success)


def optimal_action_order(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
) -> tuple[tuple[CovertAction, ...], float]:
    """Exact optimal order when feasible; ratio-rule heuristic otherwise."""
    if len(actions) <= EXACT_ORDER_LIMIT:
        return exact_action_order(actions, model)
    heuristic = heuristic_action_order(actions, model)
    success, _ = simulate_sequence(heuristic, model)
    return heuristic, float(success)


@dataclass(frozen=True)
class SurveillanceReport:
    """Deterministic surveillance-risk summary for one action set."""

    model_threshold: float
    optimal_order: tuple[str, ...]
    success_probability: float
    compromise_step: int | None
    peak_hazard: float
    steps: tuple[dict[str, float | str | int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "model_threshold": self.model_threshold,
            "optimal_order": list(self.optimal_order),
            "success_probability": self.success_probability,
            "compromise_step": self.compromise_step,
            "peak_hazard": self.peak_hazard,
            "steps": [dict(s) for s in self.steps],
        }


def analyze_surveillance(
    actions: Sequence[CovertAction],
    model: SurveillanceModel,
) -> SurveillanceReport:
    """Run the full surveillance pass: order, survival, and compromise timing."""
    order, success = optimal_action_order(actions, model)
    _, steps = simulate_sequence(order, model)
    peak = max((float(s["hazard"]) for s in steps), default=0.0)
    return SurveillanceReport(
        model_threshold=model.detection_threshold,
        optimal_order=tuple(a.name for a in order),
        success_probability=success,
        compromise_step=compromise_step(order, model),
        peak_hazard=peak,
        steps=steps,
    )


def canonical_surveillance_params() -> dict[str, Any]:
    """Single source of truth for the canonical surveillance scenario.

    The operator's covert campaign against the Isthmus City organisation:
    five actions from street-level observation to compound infiltration.
    Used by both ``mission.py`` and ``manuscript_variables.py``.
    """
    return {
        "actions": (
            CovertAction("observe_isthmus_house", 0.02, 0.4, 3.0),
            CovertAction("recruit_informant", 0.05, 0.9, 6.0),
            CovertAction("plant_bug", 0.04, 0.7, 5.0),
            CovertAction("intercept_courier", 0.10, 1.6, 9.0),
            CovertAction("infiltrate_compound", 0.15, 2.4, 12.0),
        ),
        "model": SurveillanceModel(
            beta_0=-4.0,
            beta_watch=1.2,
            beta_signature=1.5,
            detection_threshold=0.5,
        ),
    }
