"""Rogue-00 operation risk model — revoked licence: escalation and blowback.

The ROGUE mission's third domain: after the 00 licence is formally revoked,
an operator (James Bond in *Licence to Kill*) continues against Franz Sanchez
unsanctioned. Every overt action escalates the adversary's alert level and the
operator's accumulated exposure, raising the probability of *blowback* — a
retaliatory strike that destroys the mission's value.

This module models that trade-off with a deterministic finite-horizon
dynamic program. State is ``(alert, exposure)``; the operator chooses a
stealth/covert/overt intensity each step to maximise expected net mission
value under a logistic blowback hazard. Backward induction returns the exact
optimal policy and its expected value — no Monte Carlo, no RNG.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

__all__ = [
    "RogueModel",
    "RogueReport",
    "alert_increment",
    "blowback_probability",
    "build_rogue_model",
    "canonical_rogue_params",
    "escalation_path",
    "expected_value_of_policy",
    "next_alert",
    "solve_optimal_policy",
]

#: Default action ladder: (stealth, covert, overt).
DEFAULT_ACTIONS = ("stealth", "covert", "overt")
#: How much each action raises the alert level.
DEFAULT_VISIBILITY = (0.5, 1.5, 3.0)
#: Expected mission-progress gain per action.
DEFAULT_GAINS = (0.8, 1.6, 3.0)


@dataclass(frozen=True)
class RogueModel:
    """Parameters of the rogue-00 escalation/blowback risk process."""

    horizon: int
    alert_max: int
    actions: tuple[str, ...]
    visibility: tuple[float, ...]
    gain: tuple[float, ...]
    beta_0: float
    beta_alert: float
    beta_exposure: float
    loss_on_blowback: float
    exposure_step: float = 1.0
    escalation_loss: float = 0.1
    exposure_cap: int = 20

    def __post_init__(self) -> None:
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        if self.alert_max <= 0:
            raise ValueError("alert_max must be positive")
        if not (len(self.actions) == len(self.visibility) == len(self.gain)):
            raise ValueError("actions, visibility, and gain must be the same length")
        if len(self.actions) == 0:
            raise ValueError("at least one action is required")
        if any(v < 0.0 for v in self.visibility):
            raise ValueError("visibility must be non-negative")
        if self.exposure_cap <= 0:
            raise ValueError("exposure_cap must be positive")


def build_rogue_model(horizon: int = 10, alert_max: int = 10) -> RogueModel:
    """Canonical revoked-licence model with the film's escalation flavour."""
    return RogueModel(
        horizon=horizon,
        alert_max=alert_max,
        actions=DEFAULT_ACTIONS,
        visibility=DEFAULT_VISIBILITY,
        gain=DEFAULT_GAINS,
        beta_0=-5.0,
        beta_alert=0.8,
        beta_exposure=0.5,
        loss_on_blowback=4.0,
        exposure_step=1.0,
        escalation_loss=0.05,
        exposure_cap=20,
    )


def alert_increment(model: RogueModel, action_idx: int) -> int:
    """Integral alert step an action contributes on the DP's alert lattice.

    The dynamic program in :func:`solve_optimal_policy` optimises over the
    *integer* alert states ``0 .. alert_max``, so the visibility ladder is
    quantised by truncation onto that lattice. This function is the single
    definition of that transition; :func:`escalation_path` and
    :func:`expected_value_of_policy` use it too, so the projected escalation
    curve is the curve the DP actually optimised rather than a differently
    quantised one.

    Consequence worth knowing: a visibility below 1.0 (the canonical
    ``stealth`` action at 0.5) contributes **no** alert on this lattice. That
    is a documented modelling boundary of the integer lattice, not an
    accident — see ``manuscript/07_scope_and_related_work.md``.
    """
    return int(model.visibility[action_idx])


def next_alert(alert: float, model: RogueModel, action_idx: int) -> float:
    """Alert level after taking ``action_idx``, clamped at ``alert_max``."""
    return float(min(model.alert_max, alert + alert_increment(model, action_idx)))


def blowback_probability(alert: float, exposure: float, model: RogueModel) -> float:
    """Logistic blowback hazard: P(retaliation) = σ(β₀ + β_a·alert + β_e·exposure)."""
    z = model.beta_0 + model.beta_alert * alert + model.beta_exposure * exposure
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1.0 + exp_z)


def escalation_path(model: RogueModel, actions_indices: Sequence[int]) -> tuple[dict[str, float | str | int], ...]:
    """Deterministically project alert/exposure/blowback over an action sequence.

    Each row carries the state the step is *entered* with (``alert``,
    ``exposure``, ``blowback``) **and** the alert the step's own action leaves
    behind (``alert_after``). Both are needed: the hazard a step faces is a
    function of the entering state, but a table of entering states alone can
    never show what the last action did — under the canonical optimal policy
    (nine stealth steps then one overt close) the entering-alert column is
    identically zero, which reads as "the optimal policy never escalates"
    when in fact its final action raises alert to 3.
    """
    alert = 0.0
    exposure = 0.0
    path: list[dict[str, float | str | int]] = []
    for step_no, action_idx in enumerate(actions_indices):
        hazard = blowback_probability(alert, exposure, model)
        alert_after = next_alert(alert, model, action_idx)
        path.append(
            {
                "step": step_no,
                "action": model.actions[action_idx],
                "alert": alert,
                "alert_after": alert_after,
                "exposure": exposure,
                "blowback": hazard,
            }
        )
        alert = alert_after
        exposure += model.exposure_step
    return tuple(path)


def expected_value_of_policy(
    model: RogueModel, actions_indices: Sequence[int]
) -> tuple[float, tuple[dict[str, float | str | int], ...]]:
    """Expected net mission value of a concrete action sequence (no RNG)."""
    alert = 0.0
    exposure = 0.0
    value = 0.0
    for action_idx in actions_indices:
        hazard = blowback_probability(alert, exposure, model)
        gain = model.gain[action_idx]
        cost = model.escalation_loss * exposure
        value += gain * (1.0 - hazard) - hazard * model.loss_on_blowback - cost
        alert = next_alert(alert, model, action_idx)
        exposure += model.exposure_step
    return value, escalation_path(model, actions_indices)


@dataclass(frozen=True)
class RogueReport:
    """Deterministic optimal-policy report for a rogue-00 operation."""

    horizon: int
    alert_max: int
    actions: tuple[str, ...]
    optimal_value: float
    first_action: str
    escalation: tuple[dict[str, float | str | int], ...]
    peak_blowback: float
    policy_cells: int
    #: Highest alert level the trajectory *reaches*, including the level left
    #: behind by the final action. Taken over ``alert_after``, not over the
    #: entering-alert column, so a policy whose only escalation is its last
    #: step is reported honestly instead of as a flat zero.
    peak_alert: float
    #: Alert level standing when the horizon ends (nothing is left to be
    #: exposed to it — this is the finite-horizon end effect, priced at zero).
    terminal_alert: float

    def as_dict(self) -> dict[str, object]:
        return {
            "horizon": self.horizon,
            "alert_max": self.alert_max,
            "actions": list(self.actions),
            "optimal_value": self.optimal_value,
            "first_action": self.first_action,
            "peak_blowback": self.peak_blowback,
            "peak_alert": self.peak_alert,
            "terminal_alert": self.terminal_alert,
            "policy_cells": self.policy_cells,
            "escalation": [dict(e) for e in self.escalation],
        }


def solve_optimal_policy(model: RogueModel) -> RogueReport:
    """Backward-induction DP over the (t, alert, exposure) state lattice.

    Both state dimensions are quantised: exposure onto an integer lattice
    (``exposure_cap + 1`` cells, each ``exposure_step`` wide) and alert onto
    ``0 .. alert_max`` via the shared :func:`next_alert` transition. Because
    the projection functions use the same transition, replaying the returned
    action sequence through :func:`expected_value_of_policy` reproduces
    ``optimal_value`` exactly (pinned by
    ``tests/test_rogue_ops.py::test_dp_value_equals_replayed_optimal_sequence``).

    Returns the exact optimal expected value, the first-period optimal
    action, and the escalation curve that follows from following the optimal
    policy greedily thereafter. Deterministic; argmax tie-breaks to the first
    action.
    """
    horizon, alert_max = model.horizon, model.alert_max
    exposure_cap = model.exposure_cap
    n_actions = len(model.actions)

    # value[alert][e] for the current remaining-horizon layer.
    value: list[list[float]] = [[0.0] * (exposure_cap + 1) for _ in range(alert_max + 1)]
    policy: list[list[list[int]]] = []

    def exposure_value(e: int) -> float:
        return float(e) * model.exposure_step

    for _ in range(horizon):
        new_value: list[list[float]] = [[0.0] * (exposure_cap + 1) for _ in range(alert_max + 1)]
        layer_policy: list[list[int]] = [[0] * (exposure_cap + 1) for _ in range(alert_max + 1)]
        for alert in range(alert_max + 1):
            for e in range(exposure_cap + 1):
                exposure = exposure_value(e)
                best_val = -math.inf
                best_action = 0
                for action_idx in range(n_actions):
                    hazard = blowback_probability(float(alert), exposure, model)
                    alert_next = int(next_alert(float(alert), model, action_idx))
                    e_next = min(exposure_cap, e + 1)
                    immediate = (
                        model.gain[action_idx] * (1.0 - hazard)
                        - hazard * model.loss_on_blowback
                        - model.escalation_loss * exposure
                    )
                    candidate = immediate + value[alert_next][e_next]
                    if candidate > best_val:
                        best_val = candidate
                        best_action = action_idx
                new_value[alert][e] = best_val
                layer_policy[alert][e] = best_action
        value = new_value
        policy.append(layer_policy)

    optimal_value = value[0][0]
    first_action = model.actions[policy[-1][0][0]]

    # Follow the optimal policy to build the escalation curve.
    alert = 0
    e = 0
    action_seq: list[int] = []
    for layer in reversed(policy):
        action_idx = layer[alert][e]
        action_seq.append(action_idx)
        alert = int(next_alert(float(alert), model, action_idx))
        e = min(exposure_cap, e + 1)
    escalation = escalation_path(model, action_seq)
    # ``horizon >= 1`` is enforced by ``RogueModel.__post_init__``, so the
    # escalation table always has at least one row here. No ``default=`` and
    # no emptiness guard: neither could ever be reached (Rule 8).
    peak_blowback = max(float(step["blowback"]) for step in escalation)
    peak_alert = max(float(step["alert_after"]) for step in escalation)
    terminal_alert = float(escalation[-1]["alert_after"])

    return RogueReport(
        horizon=horizon,
        alert_max=alert_max,
        actions=model.actions,
        optimal_value=optimal_value,
        first_action=first_action,
        escalation=escalation,
        peak_blowback=peak_blowback,
        policy_cells=len(policy) * (alert_max + 1) * (exposure_cap + 1),
        peak_alert=peak_alert,
        terminal_alert=terminal_alert,
    )


def canonical_rogue_params() -> dict[str, Any]:
    """Single source of truth for the canonical revoked-licence scenario.

    Mirrors the ``mission.rogue`` block of ``manuscript/config.yaml`` (bound
    by ``tests/test_canonical_params.py``) and is consumed by ``mission.py``,
    ``manuscript_variables.py``, and ``figures/plots.py``.
    """
    model = build_rogue_model()
    return {
        "model": model,
        "horizon": model.horizon,
        "alert_max": model.alert_max,
        "actions": model.actions,
        "exposure_cap": model.exposure_cap,
    }
