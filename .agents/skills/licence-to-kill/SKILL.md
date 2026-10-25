---
name: licence-to-kill
description: Use when working on the PROJECT BOND licence_to_kill (ROGUE) film package — domain core, bond-api MissionProvider, manuscript, or gates.
---

# licence-to-kill

PROJECT BOND film package for *Licence to Kill* (1989), mission codename
**ROGUE**: deterministic special-agent mission software.

## When to use

- Running/editing the ROGUE domain core: laundering graph, vessel
  forensics, rogue-policy DP, narcotics finance, operations logistics,
  surveillance/watchlist
- Wiring or verifying the `bond-api` `MissionProvider` adapter
- Regenerating manuscript tokens/figures or running the gates

## Layout

- `src/licence_to_kill/laundering_graph.py` — Sanchez laundering graph
  (cycle/funnel/integration)
- `src/licence_to_kill/vessel_forensics.py` — Wavekrest-class forensic
  physics + anomaly scan
- `src/licence_to_kill/rogue_ops.py` — revoked-licence risk DP
- `src/licence_to_kill/narcotics_finance.py` — price/purity ladder + cash
  physics + hold manifest
- `src/licence_to_kill/operations_logistics.py` — Dijkstra routing +
  gadget knapsack + trip plan
- `src/licence_to_kill/surveillance.py` — watchlist detection +
  survival-optimal ordering
- `src/licence_to_kill/mission.py` — `bond-api` `MissionProvider` (the only
  `bond_api` import)
- `src/licence_to_kill/manuscript_variables.py` + `figures/plots.py`
- `scripts/` — thin phase CLIs + preflight + manuscript generation
- `tests/` — zero-mock, real-data; gate is >= 90 % line+branch, measured
  figure recorded in `TODO.md`

## Quick commands

```bash
# run from the repository root (standalone clone of docxology/bond-licence_to_kill)
# uv sync needs a local bond-api checkout: see [tool.uv.sources] in pyproject.toml
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py
```

## Pitfalls

- Domain core must stay bond-api-free and infrastructure-free (guarded by
  `tests/test_mission.py`). Only `mission.py` imports `bond_api`.
- All persisted results are deterministic (seed 0, `wall_time_s 0.0`); don't
  introduce wall-clock or untracked RNG in outputs.
- Manuscript metrics are tokens injected from `manuscript_variables.py`,
  never handwritten in prose; never write literal `{{TOKEN}}` placeholder
  text in numbered sections (the cross-ref gate flags it).
- Layer contract on this package allows no `infrastructure` imports
  (`manuscript/layer_contract.yaml`).
- `MissionProvider`, `GADGET_REGISTRY`, and `run_rogue_mission` are FROZEN —
  other BOND packages import them by name. Deepen inside the methods;
  extend gadgets additively only.
- Parameters live in `canonical_*_params()` per domain; the
  `manuscript/config.yaml` `mission:` block is a mirror asserted equal by
  `tests/test_canonical_params.py`. Change the Python first.
