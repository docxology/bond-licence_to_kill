# tests/ — ROGUE test suite

Zero-mock, all-real-data tests. 124 tests, ~99.6 % line + branch coverage on
`src/` (gate ≥ 90 %).

- `conftest.py` — pins `MPLBACKEND=Agg`, puts repo root + `src/` on path.
- `test_laundering_graph.py` — graph structure, detectors, integration.
- `test_vessel_forensics.py` — analytic physics + anomaly branches.
- `test_rogue_ops.py` — DP, logistic hazard, escalation, determinism.
- `test_narcotics_finance.py` — price/purity chain, cash physics, manifest.
- `test_operations_logistics.py` — Dijkstra routing (incl. stale-heap and
  unreachable branches), knapsack, trip plan.
- `test_surveillance.py` — detection, product-survival, exact/heuristic
  ordering, compromise timing.
- `test_mission.py` — protocol conformance, full flow, provenance, gadgets,
  bond-api-free domain guard.
- `test_manuscript_variables.py` — token map + live cross-reference gate.
- `test_figures.py` — figure presence + byte determinism (four figures).
- `test_scripts_smoke.py` — subprocess runs of every thin CLI.

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
