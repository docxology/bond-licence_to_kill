# licence_to_kill — ROGUE

PROJECT BOND film package for *Licence to Kill* (1989), mission codename
**ROGUE**. Deterministic special-agent mission software implementing the
frozen `bond-api` `MissionProvider` protocol over six pure domain cores.

## What it does

1. **Money-laundering graph** (`src/licence_to_kill/laundering_graph.py`) —
   models the Sanchez cartel's placement→layering→integration flow and
   detects money-returning cycles, funnels, layering chains, and how
   integrated (diluted) the placed dirty value has become.
2. **Vessel forensics** (`src/licence_to_kill/vessel_forensics.py`) —
   computes IMO gross tonnage, hydrostatic displacement, and fuel endurance
   from first principles and flags covert cargo on the Wavekrest-class
   mothership.
3. **Rogue-00 risk model** (`src/licence_to_kill/rogue_ops.py`) — exact
   finite-horizon dynamic programming for a revoked-licence operation,
   trading mission gain against escalating alert and blowback.
4. **Narcotics-finance economics** (`src/licence_to_kill/narcotics_finance.py`) —
   supply-chain price/purity ladder and cash physics (note mass/volume,
   hold manifest feasibility, trips) behind the cartel's courier parcel.
5. **Operations logistics** (`src/licence_to_kill/operations_logistics.py`) —
   risk-adjusted Dijkstra routing, exact 0/1-knapsack gadget loadout, and
   trip projection against fuel endurance.
6. **Surveillance / watchlist** (`src/licence_to_kill/surveillance.py`) —
   logistic detection risk over a covert-action sequence with exact (n ≤ 8)
   and ratio-rule survival-optimal ordering.

All six are deterministic (seeded network, closed-form physics, exact DP),
infrastructure-free, and exposed through a thin `MissionProvider` adapter
(`src/licence_to_kill/mission.py`).

## Quick start

```bash
# Install (binds bond-api via its path dependency)
uv sync --extra dev

# Gate: tests + ≥ 90 % coverage
uv run pytest tests/ --cov=src --cov-fail-under=90

# Drive the mission (thin CLIs)
uv run python scripts/00_preflight.py
uv run python scripts/mission_brief.py
uv run python scripts/mission_execute.py       # writes output/data/mission_outcome.json
uv run python scripts/mission_debrief.py

# Hydrate the manuscript + figures (writes output/{data,manuscript,figures}/)
uv run python scripts/z_generate_manuscript_variables.py
```

## Layout

```
src/licence_to_kill/
  laundering_graph.py      # Sanchez laundering graph (cycle/funnel/integration)
  vessel_forensics.py      # Wavekrest-class forensic physics
  rogue_ops.py             # revoked-licence risk DP
  narcotics_finance.py     # supply-chain price/purity + cash physics
  operations_logistics.py  # Dijkstra routing + gadget knapsack + trip plan
  surveillance.py          # watchlist detection + survival-optimal ordering
  mission.py               # bond-api MissionProvider adapter + gadget registry
  manuscript_variables.py
  figures/plots.py         # 4 deterministic figures
scripts/                   # thin phase CLIs (brief/recon/plan/execute/debrief) + preflight + z_generate
tests/                     # zero-mock, real-data, 99 %+ line & branch coverage
manuscript/                # token-driven ROGUE manuscript + config.yaml + references.bib
docs/                      # agent instructions, architecture, testing philosophy
```

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # 124 tests, ~99.6 % line+branch
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

This is a local-only working tree: there is no remote and it is never pushed.
