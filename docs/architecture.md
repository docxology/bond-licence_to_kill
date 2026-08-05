# Architecture — licence_to_kill (ROGUE)

How this package is put together, module by module, and how it plugs into
the BOND fleet. Read [`agent_instructions.md`](agent_instructions.md) first
for the rules; this document explains the shape those rules protect.

## 1. Layer topology

Four layers, one direction of dependency. Nothing ever imports upward, and
no module imports the monorepo `infrastructure` tree.

| Layer | Location | May import | Responsibility |
|---|---|---|---|
| **Domain core** | `src/licence_to_kill/{laundering_graph,vessel_forensics,rogue_ops,narcotics_finance,operations_logistics,surveillance}.py` | stdlib, numpy | Pure deterministic algorithms |
| **Protocol adapter** | `src/licence_to_kill/mission.py` | `bond_api` + domain core | The frozen five-stage `MissionProvider`, the gadget registry |
| **Presentation** | `src/licence_to_kill/manuscript_variables.py`, `src/licence_to_kill/figures/plots.py` | domain core, config, matplotlib | Token hydration, deterministic figures |
| **Thin CLIs** | `scripts/` | `_bootstrap`, `bond_api.serialization`, the above | Drive one mission phase each |

```
scripts/  ─────────────────►  mission.py  ──────►  bond_api (frozen)
                                  │
manuscript_variables.py  ─────────┼──────────►  domain core (pure)
figures/plots.py         ─────────┘
```

`mission.py` is the **only** module in the package that imports `bond_api`.
That is structural, not stylistic: it means the six domain modules stay
importable in any Python 3.10+ environment even if the path dependency on
`bond-api` breaks, and it is enforced by
`tests/test_mission.py::test_pure_domain_modules_are_bond_api_free`, which
greps each domain module's source for the string `bond_api`.

## 2. The domain core, module by module

Every module is closed-form or exact — no Monte Carlo anywhere in the
package. Each one also exposes a `canonical_*_params()` function which is
the single declaration of its scenario (see §4).

### `laundering_graph.py` — the Sanchez money-laundering network

`TransactionGraph` is a directed weighted graph of financial entities built
from validated `Transaction` records (self-loops and non-positive amounts
are rejected at insertion, so no downstream detector has to defend against
them). On top of it:

- `find_cycles` — depth-limited DFS enumerating elementary cycles, each
  rotated to a canonical form (starting at its lexicographically smallest
  node) so rotations of one loop collapse to a single finding.
- `funnels` / `concentration` — per-node degree and volume imbalance,
  classifying collectors (fan-in, ratio ≥ τ) and distributors (fan-out,
  ratio ≤ 1/τ). Trivial pass-throughs are excluded by requiring ≥ 2 unique
  counterparts on the dense side.
- `layering_paths` — bounded enumeration of source→sink chains. The cap is
  a *reported* quantity, not a hidden one: the canonical network saturates
  it and the manuscript says so explicitly.
- `propagate_dirty` — iterative re-distribution of dirty mass in proportion
  to edge weight, with out-degree-zero nodes retaining their mass. Converges
  to the pooling distribution; `max_iter` guards ill-posed pure circulations.
- `integration_score`, `mixing_entropy` — how diluted, and how dispersed,
  the placed value has become across the integration sinks.
- `analyze_laundering` — the composite pass, blending cycle, depth, and
  funnel components under `LAYERING_WEIGHTS`.
- `build_sanchez_network` — the seeded generator. Structure is fixed (the
  cartel typology); amounts are drawn from a seeded RNG, which makes the
  same seed reproduce the same graph and is itself the determinism proof.

### `vessel_forensics.py` — Wavekrest-class marine physics

Closed-form naval architecture, all from named constants:
`hull_volume` (L·B·D·Cb), `gross_tonnage` (IMO 1969, K₁ = 0.2 + 0.02·log₁₀V),
`displacement_from_draft`, `fuel_mass_tonnes`, `propulsion_power_at_speed`
(cubic law), `fuel_consumption_kgph`, `endurance_range_nm`, and
`route_plausibility`.

`anomaly_scan` composes them into forensic findings: cargo denser than
`CARGO_DENSITY_CEILING`, declared displacement outside
`DISPLACEMENT_TOLERANCE` of the draft-predicted value, a route beyond speed
capability or fuel endowment, and a hull above `POWER_DENSITY_CEILING`.

It deliberately does **not** trap errors from the physics it calls. An
invalid profile raises rather than scoring zero anomalies, because "clean"
and "could not check" are different findings and only one of them is safe to
report. `forensic_report` wraps the scan with the computed quantities.

### `rogue_ops.py` — the revoked-licence control problem

A finite-horizon MDP over `(alert, exposure)`. `blowback_probability` is the
logistic hazard; `solve_optimal_policy` is exact backward induction over the
`(step, alert, exposure)` lattice, returning the optimal value, the first
action, the escalation curve, and the lattice size.

The load-bearing detail is `next_alert` / `alert_increment`: **one** shared
definition of the alert transition, used by the DP, by `escalation_path`,
and by `expected_value_of_policy`. Before it was factored out, the DP
truncated visibility onto the integer lattice while the projection used raw
floats — the optimiser and the reported trajectory described different
processes, and every individual test still passed. The invariant that pins
it now is
`tests/test_rogue_ops.py::test_dp_value_equals_replayed_optimal_sequence`:
replaying the DP's own action sequence must reproduce its value exactly.

Each escalation row carries both the alert the step is *entered* with
(`alert`, what its hazard is priced on) and the alert its own action leaves
behind (`alert_after`). `RogueReport.peak_alert` / `terminal_alert` are
taken over the latter. The reason is not tidiness: the canonical optimum is
nine stealth steps then one overt close, so the entering-alert column is
identically zero and a "peak alert" read off it reports 0.0 — a number
structurally incapable of showing the escalation the policy actually
chooses. `test_peak_alert_records_the_final_action_consequence` pins the
gap between the two.

### `narcotics_finance.py` — cash economics and manifest physics

`price_chain` applies sequential stage multipliers; `purity_adjusted_price`
restates unit economics per pure gram. The cash side converts value to whole
notes (`cash_bills`, rounding *up* — a partial note cannot be carried) and
then to mass, volume, and bulk density. `manifest_feasibility` and
`trips_required` check the parcel against a hold's volume and mass.

### `operations_logistics.py` — routing, loadout, voyage

`OperationNetwork` holds validated `MissionLeg`s. `shortest_path` is
Dijkstra over one of three additive weights; for `risk` the per-leg weight
is −ln(1−r), which makes the survival *product* additive so the returned
route genuinely minimises the reported 1−∏(1−rᵢ) metric rather than a proxy.
`direct_leg` returns the single origin→destination edge — the baseline the
manuscript compares the layered route against. It is a separate function
precisely because `shortest_path(..., weight="distance")` returns that same
leg on the canonical network, so calling the distance-minimal path "the
direct leg" produced correct numbers for the wrong reason and would have
diverged silently the moment a shorter two-hop pair was added.

`gadget_knapsack` is exact 0/1 knapsack over gram-scaled integer weights.
Its selection flag is recorded during each item's own DP pass; the tempting
shortcut of comparing the final `dp` array during reconstruction
false-negatives once a later item has already absorbed the same capacity
cell.

`trip_plan` projects legs against cruise speed and endurance, counting
mid-leg refuelling stops, with an `allow_mid_leg_refuel=False` mode that
reports infeasibility instead.

### `surveillance.py` — watchlist detection and action ordering

`detection_probability` is the logistic hazard in accumulated watchlist
weight and action signature. `simulate_sequence` gives product-survival plus
per-step traces; `compromise_step` reports the first step crossing the
threshold. Ordering is exact by exhaustive permutation up to
`EXACT_ORDER_LIMIT` actions, with Smith's ratio rule beyond;
`optimal_action_order` picks between them and `analyze_surveillance`
assembles the report.

### `figures/plots.py` — four deterministic figures

`plot_laundering_network`, `plot_rogue_escalation`,
`plot_vessel_forensic_scan`, `plot_operations_logistics`. The Agg backend is
selected before pyplot import; all layout coordinates are derived from data,
never sampled, so reruns are byte-identical.
`plot_operations_logistics` accepts injectable `params` specifically so its
unreachable-destination guard is a branch a test can reach rather than one
that can never fire.

### `manuscript_variables.py` — token hydration

`generate_variables()` returns the full `{{TOKEN}} → value` map: identity
tokens from `manuscript/config.yaml`'s `paper:` block, and every analytic
and parameter token from a fresh deterministic run of the six domains.
`substitute()` replaces tokens in text and deliberately leaves unknown ones
verbatim so unresolved placeholders are detectable rather than silently
blank.

## 3. How `mission.py` implements the frozen `MissionProvider`

`bond_api` defines a runtime-checkable `MissionProvider` protocol. Discovery
(`bond_api.discovery`) imports `licence_to_kill.mission`, instantiates
`MissionProvider()` with **no arguments**, and drives five stages. The class
name, the constructor arity, and the five method signatures are frozen —
`bond-cli`, the coordinator's reconcile pass, and the orchestrator all
consume them across packages, so changing their shape breaks the fleet.
Deepening happens *inside* the methods.

| Stage | Signature | What ROGUE does |
|---|---|---|
| `brief` | `() -> MissionBrief` | Declares six objectives (one per domain), six `Asset`s (network, vessel, risk model, finance manifest, operations network, watchlist model), and a `determinism` `Constraint` |
| `recon` | `(ReconRequest) -> ReconReport` | Runs all six analyses and emits eight labelled `Finding`s: `goal`, `layering`, `integration`, `vessel`, `rogue`, `finance`, `logistics`, `surveillance` |
| `plan` | `(MissionBrief) -> MissionPlan` | Seven deterministic `Step`s — one per domain plus a `verify` cross-check step |
| `execute` | `(MissionPlan) -> MissionOutcome` | Runs the six domains; returns `results` keyed by domain plus `seed` and `input_hash`, with a `Provenance` record |
| `debrief` | `(MissionOutcome) -> Debrief` | Wraps the outcome with seven standing lessons |

Three package-level surfaces are equally frozen and equally consumed by the
fleet:

- `MissionProvider` — the class itself, discoverable by slug
  `licence_to_kill`.
- `GADGET_REGISTRY` — a `GadgetRegistry` populated at import time with eight
  entries: seven callables (`laundering_analyzer`, `laundering_network`,
  `vessel_forensics`, `rogue_risk_model`, `narcotics_finance`,
  `operations_router`, `surveillance_model`) and one `network_manifest`
  data payload. **Additive changes only** — removing or renaming an entry
  breaks cross-package gadget lookup.
- `run_rogue_mission(request) -> Debrief` — a convenience driver over
  `bond_api.protocol.run_mission`.

Determinism is part of the contract, not a nicety. `Provenance` carries the
package version, `seed = 0`, `wall_time_s = 0.0` (a real elapsed time would
make outcomes non-comparable across runs), and a sha256 `input_hash`
computed over the built transaction graph (node set and edge amounts) plus
every parameter of all six `canonical_*_params()` scenarios — laundering
search bounds, the vessel profile and its observations, the full rogue
model, finance parameters, logistics legs and gadgets, and surveillance
actions and coefficients. Any ROGUE outcome can therefore be audited without
re-running the mission: recompute the hash over the same inputs and it must
match.

The payload is serialised from `mission.canonical_domain_inputs()` by a
recursive dataclass walk, so this is not a hand-maintained list that can
fall behind the domains: a parameter added to any `canonical_*_params()`
enters the hash without an edit here. The claim is enforced rather than
asserted — `tests/test_mission.py::test_input_hash_covers_every_domain`
mutates one domain's inputs at a time and requires the hash to change. It
exists because the first version of this hash covered four domains while
documenting six: every vessel and rogue parameter could change with the
"audit" hash unmoved.

## 4. One declaration per scenario

Each domain exposes a `canonical_*_params()` function. All three consumers —
`mission.py`, `manuscript_variables.py`, `figures/plots.py` — read those
functions rather than carrying their own copies of the constants. This
matters more than it looks: these three modules previously each held their
own `_SOURCES` / `_SINKS` / `_SEED` / `_VESSEL_OBSERVED` literals, so a
figure could have depicted a scenario the manuscript did not describe and
nothing would have caught it.

The `mission:` block of `manuscript/config.yaml` mirrors those functions for
human readers. The domain core is dependency-free and does not read YAML, so
that block is a *declared mirror*, not an input — and
`tests/test_canonical_params.py` asserts every key equal to the value the
code actually uses, plus that the search bounds are genuinely consumed
rather than merely named. Change the Python first, then the YAML.

## 5. Adding a concept

1. Add the function or type to the relevant domain module. Keep it pure —
   stdlib and numpy only, no `bond_api`, no `infrastructure`.
2. Give it a real-data test in `tests/test_<module>.py`, including its error
   paths. No mocks.
3. If it introduces a parameter, put it in that module's
   `canonical_*_params()` and mirror it into `manuscript/config.yaml`'s
   `mission:` block; `tests/test_canonical_params.py` will hold the two
   together.
4. Wire it into `mission.py` if it belongs in the mission lifecycle —
   additively, never changing the five method signatures or removing a
   gadget entry.
5. Add a token in `manuscript_variables.py` and cite it in prose. The
   manuscript gates require every generated token to be cited somewhere and
   every cited token to be generated, so a token cannot rot unnoticed.

## 6. Packaging and import bootstrap

The package is non-workspace and standalone. `scripts/_bootstrap.py` injects
the repo root and `src/` onto `sys.path` for the thin CLIs;
`tests/conftest.py` does the same for tests and pins `MPLBACKEND=Agg`. The
only non-stdlib runtime dependencies are numpy, matplotlib, PyYAML, and the
local path dependency on `bond-api`.
