# licence_to_kill — ROGUE

PROJECT BOND film package for *Licence to Kill* (1989), mission codename
**ROGUE**. Deterministic special-agent mission software: six pure domain
cores behind the frozen `bond-api` `MissionProvider` protocol.

## The film as a specification

Franz Sanchez runs a cartel. Its cash is laundered from street placement
through shell-front layering into legitimate banks; the proceeds move on a
Wavekrest-class mothership; and the operator who pursues him does it with a
**revoked 00 licence** — unsanctioned, escalating, exposed. Each of those is
turned into a real algorithm rather than a themed stub, and the campaign
those algorithms describe has to be physically affordable: the money has to
fit in a hold, the hull has to reach Florida, and the operator has to stay
uncompromised long enough to finish.

| Film concept | Module | What it computes |
|---|---|---|
| Cartel money laundering | `laundering_graph.py` | Directed flow graph; DFS cycle detection, funnel/concentration analysis, dirty-flow propagation, integration score, mixing entropy, composite layering score, seeded network generator |
| The Wavekrest mothership | `vessel_forensics.py` | IMO 1969 gross tonnage, hydrostatic displacement, cubic-law fuel endurance, route plausibility, and a forensic anomaly scan that catches contraband by cargo density and draft mismatch |
| The revoked licence | `rogue_ops.py` | Finite-horizon MDP over (alert, exposure) with a logistic blowback hazard, solved exactly by backward induction |
| The opening cash intercept | `narcotics_finance.py` | Supply-chain price/purity ladder and US-note cash physics — mass, volume, bulk density, hold-manifest feasibility, trips required |
| Moving the operation | `operations_logistics.py` | Risk-adjusted Dijkstra routing (−ln(1−r) survival weights), exact 0/1-knapsack gadget loadout, fuel-endurance voyage projection with refuelling |
| Staying uncompromised | `surveillance.py` | Logistic detection hazard over a covert-action sequence, product-survival, exact and ratio-rule survival-optimal ordering, compromise timing |

Supporting modules:

| Module | Role |
|---|---|
| `mission.py` | The **only** module importing `bond_api` — the five-stage `MissionProvider` adapter, the gadget registry, deterministic provenance |
| `manuscript_variables.py` | `{{TOKEN}}` hydration: every number the manuscript prints, computed fresh |
| `figures/plots.py` | Four byte-deterministic matplotlib figures |

Everything is exact or closed-form — seeded generation, analytic physics,
exact dynamic programming, exact shortest path and knapsack, exhaustive
permutation search. There is no Monte Carlo anywhere in the package.

## Quick start

```bash
# Install. bond-api is vendored in this repository (vendor/bond-api), so a
# clone resolves on its own — no sibling checkout to point at.
uv sync --extra dev

# The gate: tests + >= 90 % line and branch coverage on src/
uv run pytest tests/ --cov=src --cov-fail-under=90

# Drive the mission (thin phase CLIs)
uv run python scripts/00_preflight.py
uv run python scripts/mission_brief.py
uv run python scripts/mission_recon.py
uv run python scripts/mission_plan.py
uv run python scripts/mission_execute.py      # writes output/data/mission_outcome.json
uv run python scripts/mission_debrief.py

# Hydrate the manuscript + figures (writes output/{data,manuscript,figures}/)
uv run python scripts/z_generate_manuscript_variables.py
```

## The MissionProvider surface

`bond_api.discovery` finds this package by slug `licence_to_kill`, imports
`licence_to_kill.mission`, and instantiates `MissionProvider()` with no
arguments. Three surfaces are **frozen** — `bond-cli`, the coordinator, and
the orchestrator consume them across package boundaries:

```python
from licence_to_kill.mission import GADGET_REGISTRY, MissionProvider, run_rogue_mission

provider = MissionProvider()          # no-arg construction is part of the contract
brief    = provider.brief()           # 6 objectives, 6 assets, determinism constraint
report   = provider.recon(ReconRequest(goal="survey the network"))
plan     = provider.plan(brief)       # 7 steps: 6 domains + verify
outcome  = provider.execute(plan)     # results per domain + seed + sha256 input_hash
debrief  = provider.debrief(outcome)  # 7 standing lessons
```

`GADGET_REGISTRY` registers eight entries under the film slug — seven
callables (`laundering_analyzer`, `laundering_network`, `vessel_forensics`,
`rogue_risk_model`, `narcotics_finance`, `operations_router`,
`surveillance_model`) plus a `network_manifest` payload. Changes must be
additive.

Every `MissionOutcome` carries `Provenance` with the package version,
`seed = 0`, `wall_time_s = 0.0`, and a sha256 `input_hash` over the built
transaction graph plus **every parameter of all six** `canonical_*_params()`
scenarios — so any outcome can be audited without re-running it. That
coverage is a tested property, not a comment: `test_input_hash_covers_every_domain`
mutates one domain at a time and requires the hash to move, which is how the
earlier version of this hash — silently blind to the entire vessel and rogue
domains — would have been caught.

## Layout

```
src/licence_to_kill/
  laundering_graph.py       # Sanchez laundering graph (cycles, funnels, integration)
  vessel_forensics.py       # Wavekrest-class forensic physics
  rogue_ops.py              # revoked-licence policy DP
  narcotics_finance.py      # price/purity ladder + cash physics
  operations_logistics.py   # Dijkstra routing + gadget knapsack + voyage plan
  surveillance.py           # watchlist detection + survival-optimal ordering
  mission.py                # bond-api MissionProvider adapter + gadget registry
  manuscript_variables.py   # {{TOKEN}} hydration
  figures/plots.py          # four deterministic figures
scripts/                    # thin phase CLIs + preflight + manuscript generation
tests/                      # zero-mock, real-data suite
manuscript/                 # token-driven ROGUE manuscript, config.yaml, references.bib
docs/                       # agent rules, architecture, testing philosophy
output/                     # regenerable artifacts (git-ignored)
```

Each domain declares its scenario once, in a `canonical_*_params()`
function. The mission adapter, the token generator, and the figure
generators all read those functions, and the `mission:` block of
`manuscript/config.yaml` is a declared mirror that
`tests/test_canonical_params.py` asserts equal — so a figure cannot depict a
scenario the prose does not describe.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90      # gate: >= 90 % line + branch
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Coverage and test counts are deliberately not quoted here — the gate above
is the claim. The current measured figures, with the date they were taken,
are in [`TODO.md`](TODO.md).

## Notes

Source: <https://github.com/docxology/bond-licence_to_kill> (branch `main`).
No DOI is minted, and the `bond-api` binding stays a local path dependency,
resolved against the recorded copy in `vendor/bond-api` (see above). Author:
Daniel Ari Friedman (Active Inference Institute). Start with
[`docs/agent_instructions.md`](docs/agent_instructions.md) before changing
anything.
