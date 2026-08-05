# licence_to_kill — licence to kill (1989) · mission codename ROGUE

`licence_to_kill` is a PROJECT BOND film package: deterministic
special-agent mission software that implements the FROZEN `bond-api`
`MissionProvider` protocol over three pure domain cores drawn from the film
*Licence to Kill*.

## Mission concept

Franz Sanchez runs a drug cartel; the money he earns is laundered from cash
placement through shell-front layering into legitimate banks, the proceeds
smuggled on a Wavekrest-class mothership; and the operator who pursues him
does so with a **revoked 00 licence** — unsanctioned, escalating, at risk of
blowback. The package turns each of those three problems into a real,
deterministic algorithm.

| Domain | Module | Algorithms |
|---|---|---|
| Money-laundering graph | `src/licence_to_kill/laundering_graph.py` | DFS cycle detection, funnel/concentration analysis, conservative dirty-flow propagation, integration score, mixing entropy, composite layering score |
| Vessel forensics | `src/licence_to_kill/vessel_forensics.py` | IMO gross tonnage, hydrostatic displacement, cubic-law fuel endurance, route plausibility, anomaly scan |
| Rogue-00 risk model | `src/licence_to_kill/rogue_ops.py` | Logistic blowback hazard, escalation projection, exact backward-induction dynamic programming |
| Narcotics-finance economics | `src/licence_to_kill/narcotics_finance.py` | Supply-chain price/purity ladder, note mass/volume cash physics, hold manifest feasibility, trip count |
| Operations logistics | `src/licence_to_kill/operations_logistics.py` | Risk-adjusted Dijkstra routing, exact 0/1-knapsack gadget loadout, fuel-endurance trip projection |
| Surveillance / watchlist | `src/licence_to_kill/surveillance.py` | Logistic detection hazard, product-survival, exact/ratio-rule survival-optimal ordering |

## Layer contract

| Surface | Rule |
|---|---|
| `src/licence_to_kill/{laundering_graph,vessel_forensics,rogue_ops}.py` | Pure domain core — stdlib + numpy only; **no** `bond_api`, **no** `infrastructure` |
| `src/licence_to_kill/mission.py` | Thin protocol adapter — the only module importing `bond_api` |
| `src/licence_to_kill/manuscript_variables.py`, `figures/` | Token hydration + deterministic matplotlib figures |
| `scripts/` | Thin orchestrators (phase CLIs, preflight, manuscript generation) |

Manuscript variables are injected from `manuscript/config.yaml` +
`src/licence_to_kill/manuscript_variables.py` — never hand-authored in
prose. Live counts (test total, coverage %) are tracked in the shared
monorepo `docs/_generated/COUNTS.md`; do not hardcode them.

## Protocol integration

`src/licence_to_kill/mission.py` exposes a top-level `MissionProvider` class
discoverable by slug `licence_to_kill` via `bond_api.discovery`, registers
its gadgets with the `GadgetRegistry` (laundering analyzer/network, vessel
forensics, rogue risk model, network manifest), and drives the five-stage
lifecycle (brief → recon → plan → execute → debrief) deterministically
(seed 0, `wall_time_s = 0.0`, sha256 `input_hash` in `Provenance`).

## Quick reference

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90   # 124 tests, ~99.6 % line+branch
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Thin CLIs: `scripts/00_preflight.py`, `scripts/mission_{brief,recon,plan,execute,debrief}.py`,
and `scripts/z_generate_manuscript_variables.py` (writes `output/`).

## Rules for agents

Read `docs/agent_instructions.md` first. Keep the domain core pure
(`tests/test_mission.py` guards it); never mock; keep manuscripts
token-driven; stay inside this package only; commit path-scoped; never push
(local-only tree).

## Publishing

Local-only: no remote and no Zenodo/GitHub deposits. The `bond-api` protocol
dependency is a local path source. Author: Daniel Ari Friedman (Active
Inference Institute).
