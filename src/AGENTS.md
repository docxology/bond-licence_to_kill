# src/ — licence_to_kill domain core & presentation

The importable logic for the ROGUE mission. The pure domain core is
bond-api-free and infrastructure-free; the only protocol import lives in the
adapter (`mission.py`).

## Package layout

- `licence_to_kill/laundering_graph.py` — `TransactionGraph`, cycle/funnel
  detectors, dirty-flow integration, seeded `build_sanchez_network`.
- `licence_to_kill/vessel_forensics.py` — IMO gross tonnage, hydrostatic
  displacement, fuel endurance, route plausibility, `anomaly_scan`.
- `licence_to_kill/rogue_ops.py` — logistic blowback, escalation,
  exact DP `solve_optimal_policy`.
- `licence_to_kill/narcotics_finance.py` — price/purity ladder, cash
  physics, hold manifest feasibility.
- `licence_to_kill/operations_logistics.py` — Dijkstra routing, 0/1
  knapsack loadout, fuel-endurance trip plan.
- `licence_to_kill/surveillance.py` — watchlist detection, survival-optimal
  action ordering (exact ≤ 8, ratio heuristic beyond).
- `licence_to_kill/mission.py` — frozen `bond_api` `MissionProvider` adapter
  + `GadgetRegistry` registration (the only `bond_api` import).
- `licence_to_kill/manuscript_variables.py` — `{{TOKEN}}` hydration.
- `licence_to_kill/figures/plots.py` — four deterministic figures.

## Rules

- The six domain modules (`laundering_graph`, `vessel_forensics`,
  `rogue_ops`, `narcotics_finance`, `operations_logistics`, `surveillance`)
  import only stdlib + numpy — no `bond_api`, no `infrastructure`. Guarded by
  `tests/test_mission.py::test_pure_domain_modules_are_bond_api_free`.
- Each domain declares its scenario in one `canonical_*_params()` function,
  read by `mission.py`, `manuscript_variables.py`, and `figures/plots.py`
  alike. Do not reintroduce local copies of those constants; the
  `manuscript/config.yaml` mirror is asserted equal by
  `tests/test_canonical_params.py`.
- No silent failure paths: never wrap a computation in a bare `except` that
  substitutes a default, and never write a guard no input can reach.
- Deterministic: fixed seed, no random draws in detectors, no wall-clock in
  persisted outputs.
- Every public function has type hints and a docstring; `ruff` and `mypy`
  are clean on this tree.
