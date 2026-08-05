# licence_to_kill TODO

Forward-only backlog for the ROGUE film package (*Licence to Kill*, 1989),
mission codename **ROGUE**.

## Deep improvement (phase-4, this pass)

- **Three new pure domain modules** (`src/licence_to_kill/`):
  - `narcotics_finance.py` — supply-chain price/purity ladder (export →
    wholesale → street), US-currency note cash physics (mass/volume via
    `canonical_finance_params`, billed at the $5M opening intercept), hold
    manifest feasibility, trip count.
  - `operations_logistics.py` — risk-adjusted Dijkstra routing (edge weight
    −ln(1−r) over the survival product; cost/distance weights also
    supported), exact 0/1-knapsack gadget loadout (gram-scaled DP with a
    correct per-item `selected` reconstruction), fuel-endurance trip
    projection with mid-leg refuelling.
  - `surveillance.py` — logistic detection hazard over a covert-action
    sequence, product-survival, exact permutation ordering (n ≤ 8) and the
    Smith-rule ratio heuristic, and compromise-step timing.
- **Protocol-stable deepening** — `mission.py` keeps the frozen
  `MissionProvider` (brief/recon/plan/execute/debrief) and
  `GADGET_REGISTRY`; brief grows to six objectives/assets, results gain
  `narcotics_finance` / `operations_logistics` / `surveillance` keys, and
  gadgets gain `narcotics_finance` / `operations_router` /
  `surveillance_model` (additive only).
- **Presentation** — manuscript tokens `FIN_*` / `LOG_*` / `SURV_*` added
  from the new `canonical_*_params()` single sources; a fourth figure
  (`operations_logistics.png`) added; `references.bib` extended with real
  sources (Dijkstra 1959, Kellerer/Pferschy/Pisinger 2004, Smith 1956, BEP
  currency facts, DEA price analyses).
- **Tests** — `test_narcotics_finance.py`, `test_operations_logistics.py`,
  `test_surveillance.py` added and the mission/manuscript/figure tests
  extended. 124 passed, ~99.6 % line + branch coverage on `src/`.

## Built (phase-1 conversion, this pass)

- **Pure domain core** (`src/licence_to_kill/`):
  - `laundering_graph.py` — `TransactionGraph`, DFS cycle detection, funnel
    analysis, dirty-flow propagation, integration score, mixing entropy,
    composite layering score, seeded `build_sanchez_network`.
  - `vessel_forensics.py` — IMO gross tonnage, hydrostatic displacement,
    cubic-law fuel endurance, route plausibility, `anomaly_scan`.
  - `rogue_ops.py` — logistic blowback hazard, escalation projection, exact
    backward-induction `solve_optimal_policy` DP.
- **Protocol adapter** `mission.py` — frozen `bond_api` `MissionProvider`
  (brief/recon/plan/execute/debrief), `GadgetRegistry` registration,
  deterministic provenance (`input_hash`, seed 0, `wall_time_s = 0.0`).
- **Presentation** — `manuscript_variables.py` ({{TOKEN}} hydration) and
  `figures/plots.py` (three deterministic figures).
- **Thin CLIs** — `scripts/00_preflight.py`,
  `scripts/mission_{brief,recon,plan,execute,debrief}.py`,
  `scripts/z_generate_manuscript_variables.py`, shared `scripts/_bootstrap.py`.
- **Tests** — zero-mock, real-data; 73 passed, ~99 % line + branch coverage
  on `src/` (gate ≥ 90 %).
- **Manuscript + docs + metadata** — token-driven sections, `config.yaml`,
  `references.bib`, docs hub, metadata sidecars.

## Verification evidence (2026-08)

- `uv run pytest tests/ --cov=src --cov-fail-under=90` → **124 passed**,
  **~99.6 %** line + branch coverage on `src/` (all six domain modules at or
  above 99 %; figures/laundering/narcotics/operations/surveillance at 100 %).
- `uv run ruff check src/ scripts/ tests/` + `ruff format` + `uv run mypy
  src/ scripts/` → clean.
- Zero leftover lineage strings (lineage grep excludes `uv.lock`/`.git`).

## Declared integration points

- **bond-api protocol (FROZEN, done)** — bound via the local path dependency
  in `pyproject.toml` `[tool.uv.sources]`. `mission.py` implements the frozen
  surface; discovery imports `licence_to_kill.mission` → `MissionProvider`.
- **bond-utilities provenance** — not yet bound. If `record_provenance_outcome`
  (Layer 0) should persist ROGUE outcomes in the shared mission-record
  format, delegate outcome persistence to it. Acceptance: mission_execute
  writes via `bond_utilities.mission_io` when available; otherwise the
  package's own tagged-JSON outcome file remains authoritative.
- **bond-coordinator / operators** — the orchestrator discovers ROGUE by slug
  via `bond_api.discovery`; no change needed once coordinator handoff lands.
- **Fleet manuscript rendering** — token hydration is local
  (`output/manuscript/`); adoption of the fleet renderer is optional.

## Open items

- Revisit the layering-path enumeration cap (200): the canonical network
  saturates it, so `LAUNDERING_PATHS` reports the cap, not the true count.
  Either raise `max_paths` for a sparser corpus or document the cap (it is
  documented in the manuscript).
- Optionally extend the rogue DP to a continuous/uncapped exposure lattice
  and a richer action ladder.
