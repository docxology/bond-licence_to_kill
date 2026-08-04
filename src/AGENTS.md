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
- `licence_to_kill/mission.py` — frozen `bond_api` `MissionProvider` adapter
  + `GadgetRegistry` registration (the only `bond_api` import).
- `licence_to_kill/manuscript_variables.py` — `{{TOKEN}}` hydration.
- `licence_to_kill/figures/plots.py` — three deterministic figures.

## Rules

- The three domain modules import only stdlib + numpy. Guarded by
  `tests/test_mission.py::test_pure_domain_modules_are_bond_api_free`.
- Deterministic: fixed seed, no random draws in detectors, no wall-clock in
  persisted outputs.
- Every public function has type hints and a docstring; `ruff` and `mypy`
  are clean on this tree.
