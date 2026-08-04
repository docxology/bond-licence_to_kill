# testing_philosophy.md — licence_to_kill

## Zero-mock policy

All tests execute the real domain algorithms on real, deterministic inputs.
No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`. Coverage is
enforced at ≥ 90 % line + branch on `src/` via `pyproject.toml`
(`--cov-fail-under=90`); the current suite measures well above that.

## What the tests prove

- **`test_laundering_graph.py`** — structure and accessors, validation
  errors, cycle detection/dedup/capping, funnel and path statistics, dirty
  propagation (incl. a pure circulation conserving mass), integration and
  entropy, `analyze_laundering`, and generator determinism.
- **`test_vessel_forensics.py`** — analytic physics (IMO GT, displacement,
  endurance), validation errors, route plausibility, every `anomaly_scan`
  branch, and forensic-report determinism.
- **`test_rogue_ops.py`** — model validation, logistic bounds/monotonicity,
  escalation, policy valuation, DP-beats-naive, and report determinism.
- **`test_mission.py`** — protocol conformance (`isinstance` against the
  runtime-checkable protocol), full `run_mission` flow, end-to-end
  determinism, provenance, gadget registration, and the bond-api-free guard
  on the pure modules.
- **`test_manuscript_variables.py`** — token map, determinism under fixed
  `now`, and the live cross-reference gate over `manuscript/[0-9]*.md`.
- **`test_figures.py`** — every figure exists, is a valid PNG, and renders
  byte-identically across independent runs.
- **`test_scripts_smoke.py`** — every thin CLI runs via a real subprocess
  (`sys.executable`, `cwd=project_root`) and produces its declared artifact.

## Determinism patterns

- A fixed `seed 0` throughout; figures rendered twice and byte-compared.
- End-to-end determinism: the mission is executed twice and result
  dictionaries plus provenance hashes are asserted equal.
- The only time-variant token (`GENERATION_TIMESTAMP`) is asserted to change
  with the injected `now`, while all analytic tokens stay identical.

## Canonical run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```
