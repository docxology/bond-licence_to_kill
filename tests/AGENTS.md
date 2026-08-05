# tests/ — ROGUE test suite

Zero-mock, all-real-data tests. The gate is >= 90 % line + branch coverage
on `src/` (`--cov-fail-under=90` in `pyproject.toml`); the current measured
figure is recorded with its date in `../TODO.md` rather than quoted here,
where it would go stale silently.

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
- `test_canonical_params.py` — `manuscript/config.yaml`'s `mission:` block
  against the executable `canonical_*_params()`; that declared search bounds
  are genuinely consumed; and that `mission.py` and
  `manuscript_variables.py` produce identical reports.
- `test_manuscript_variables.py` — token map plus four live manuscript
  gates: every cited token generated, every generated token cited, every
  declared parameter bound to prose, and no unresolved placeholder.
- `test_figures.py` — figure presence + byte determinism (four figures).
- `test_scripts_smoke.py` — subprocess runs of every thin CLI.

## Run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
