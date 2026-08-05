# licence_to_kill — *Licence to Kill* (1989) · mission codename ROGUE

Build, test, and verify reference for this package. `licence_to_kill` is a
PROJECT BOND film package: deterministic special-agent mission software that
implements the **frozen** `bond-api` `MissionProvider` protocol over six
pure domain cores.

Binding rules live in [`docs/agent_instructions.md`](docs/agent_instructions.md).
Read that first. This file is the command reference.

## Mission concept

Franz Sanchez's cartel launders its cash through a layered network of shell
fronts into legitimate banks; the proceeds move on a Wavekrest-class
mothership; the operator pursuing him has had his **00 licence revoked**.
Six domains turn that into computation — three describing the adversary,
three describing what the operation can physically afford.

| Domain | Module | Algorithms |
|---|---|---|
| Money-laundering graph | `src/licence_to_kill/laundering_graph.py` | DFS elementary-cycle detection with canonical dedup, funnel/concentration analysis, conservative dirty-flow propagation, integration score, mixing entropy, composite layering score, seeded generator |
| Vessel forensics | `src/licence_to_kill/vessel_forensics.py` | IMO 1969 gross tonnage, hydrostatic displacement, cubic-law fuel endurance, route plausibility, anomaly scan |
| Rogue-00 risk model | `src/licence_to_kill/rogue_ops.py` | Logistic blowback hazard, shared integral alert transition, escalation projection, exact backward-induction DP |
| Narcotics-finance economics | `src/licence_to_kill/narcotics_finance.py` | Supply-chain price/purity ladder, US-note cash mass/volume physics, hold manifest feasibility, trip count |
| Operations logistics | `src/licence_to_kill/operations_logistics.py` | Risk-adjusted Dijkstra routing, exact 0/1-knapsack loadout, fuel-endurance voyage projection |
| Surveillance / watchlist | `src/licence_to_kill/surveillance.py` | Logistic detection hazard, product-survival, exact and ratio-rule survival-optimal ordering, compromise timing |

## Layer contract

| Surface | Rule |
|---|---|
| The six domain modules above | Pure core — stdlib + numpy only; **no** `bond_api`, **no** `infrastructure` (structurally verified in `tests/test_mission.py`) |
| `src/licence_to_kill/mission.py` | Thin protocol adapter — the only module importing `bond_api` |
| `src/licence_to_kill/manuscript_variables.py`, `figures/` | Token hydration + deterministic matplotlib figures |
| `scripts/` | Thin orchestrators — phase CLIs, preflight, manuscript generation; no algorithms |

Each domain declares its scenario once in a `canonical_*_params()` function,
read by the mission adapter, the token generator, and the figure generators
alike. `manuscript/config.yaml`'s `mission:` block is a declared mirror of
those functions — the domain core does not read YAML — and
`tests/test_canonical_params.py` asserts the two equal. **Change the Python
first, then the YAML.**

Manuscript metrics are never hand-authored: results *and* parameters reach
prose only as `{{TOKEN}}`s, enforced by four gates in
`tests/test_manuscript_variables.py`.

## Protocol integration (frozen — do not reshape)

`bond_api.discovery` imports `licence_to_kill.mission` and instantiates
`MissionProvider()` with no arguments. Consumed across packages by
`bond-cli`, the coordinator's reconcile pass, and the orchestrator:

- `MissionProvider` — `brief` → `recon` → `plan` → `execute` → `debrief`
- `GADGET_REGISTRY` — eight entries; **additive changes only**
- `run_rogue_mission(request) -> Debrief`

Determinism is contractual: seed 0, `wall_time_s = 0.0`, and a sha256
`input_hash` over all six domains' canonical inputs in every `Provenance`.
The hash is built from `mission.canonical_domain_inputs()`, so a parameter
added to any `canonical_*_params()` enters it automatically; the per-domain
mutation gate in `tests/test_mission.py` fails if a domain ever drops out.
Full contract: [`docs/architecture.md`](docs/architecture.md) §3.

## Build and test

```bash
uv sync --extra dev

# Gate
uv run pytest tests/ --cov=src --cov-fail-under=90

# A single suite / a single test
uv run pytest tests/test_rogue_ops.py -v
uv run pytest tests/test_mission.py::test_provider_satisfies_protocol -v

# Lint + types (all must be clean)
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/

# Regenerate artifacts under output/
uv run python scripts/z_generate_manuscript_variables.py
```

Thin CLIs: `scripts/00_preflight.py`,
`scripts/mission_{brief,recon,plan,execute,debrief}.py`, and
`scripts/z_generate_manuscript_variables.py`.

Coverage percentages and test counts are not quoted in this file — the
`--cov-fail-under=90` gate is the claim, and the dated measurement lives in
[`TODO.md`](TODO.md).

## Rules for agents

Read [`docs/agent_instructions.md`](docs/agent_instructions.md) first. In
brief: do not reshape the frozen protocol surface; never mock; keep the
domain core pure; keep manuscripts token-driven; no silent failure paths and
no guards that cannot fire; stay inside this package; commit path-scoped;
never push (local-only tree, no remote).

## Publishing

Local-only: no remote, no Zenodo or GitHub deposits. The `bond-api`
dependency is a local path source. Author: Daniel Ari Friedman (Active
Inference Institute).
