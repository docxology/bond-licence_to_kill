# Experimental Setup

All experiments are deterministic and reproducible under Python
{{PYTHON_VERSION}} with NumPy {{NUMPY_VERSION}}.

## Where the parameters actually live

Each domain module declares its own scenario in a `canonical_*_params()`
function, and those functions are the *executable* source of truth. The
domain core is deliberately dependency-free (standard library plus NumPy)
and does not read YAML, so `manuscript/config.yaml`'s `mission:` block is a
**declared mirror** of those functions rather than their input.

That mirror is enforced, not trusted: `tests/test_canonical_params.py`
asserts every key of the `mission:` block equal to the value the code
computes with, and fails the suite if the two drift. The same tests assert
that the declared search bounds are genuinely *consumed* — halving the path
cap must halve the enumerated chains — so a parameter cannot become
decorative without a test noticing. Nothing below is hard-coded in prose;
every value is an injected token read from the same functions.

## Laundering network

- Placement sources (street collectors): {{LAUNDERING_SOURCE_COUNT}} nodes,
  `S1`–`S3`.
- Integration sinks (banks): {{LAUNDERING_SINK_COUNT}} nodes, `B1`–`B4`,
  mixed with legitimate exporter flows (`L1`–`L3`) into the same sinks so
  integration is non-trivial.
- Edge amounts drawn from a seeded generator (`seed {{SEED}}`): the same seed
  always yields the same graph and therefore the same report.
- Detector bounds: cycle search depth {{LAUNDERING_MAX_DEPTH}}, capped at
  {{LAUNDERING_MAX_CYCLES}} cycles; layering-path enumeration capped at
  {{LAUNDERING_MAX_PATHS}} chains; funnel degree-imbalance threshold
  {{LAUNDERING_FUNNEL_THRESHOLD}}.
- Source of truth: `canonical_laundering_params()` in `laundering_graph.py`.

## Vessel forensics

- Profile: the canonical Wavekrest-class mothership (`WAVEKREST_CLASS` in
  `vessel_forensics.py`) — cargo volume {{VESSEL_CARGO_VOLUME_M3}} m³, block
  coefficient {{VESSEL_BLOCK_COEFFICIENT}}, maximum speed
  {{VESSEL_MAX_SPEED_KNOTS}} kn.
- Observed quantities that expose covert modification: a declared cargo mass
  of {{VESSEL_OBSERVED_CARGO_T}} t (above the
  {{VESSEL_CARGO_DENSITY_CEILING}} t/m³ fish ceiling for that hold) and a
  declared displacement of {{VESSEL_OBSERVED_DISPLACEMENT_T}} t (outside the
  {{VESSEL_DISPLACEMENT_TOLERANCE}} tolerance around the draft-predicted
  value).
- Physical constants: seawater density {{VESSEL_SEAWATER_DENSITY}} t/m³,
  diesel specific fuel consumption {{VESSEL_DIESEL_SFC}} kg/kWh.
- Source of truth: `canonical_vessel_params()` in `vessel_forensics.py`.

## Rogue-00 risk model

- Horizon {{ROGUE_HORIZON}} steps; discrete alert states
  0..{{ROGUE_ALERT_MAX}}.
- Action card *{{ROGUE_ACTION_CARD}}* with visibility and gain ladders,
  truncated onto the integer alert lattice by the shared `next_alert`
  transition.
- Continuous exposure quantised onto a {{ROGUE_EXPOSURE_CELLS}}-cell lattice
  (`exposure_cap {{ROGUE_EXPOSURE_CAP}}`), giving a backward-induction
  lattice of {{ROGUE_POLICY_CELLS}} state cells.
- Source of truth: `canonical_rogue_params()` in `rogue_ops.py`.

## Narcotics-finance economics

- Intercepted courier parcel: US${{FIN_VALUE_USD}} in ${{FIN_DENOMINATION}}
  notes (the film's opening intercept), against the Wavekrest-class hold
  ({{FIN_HOLD_VOLUME_M3}} m³, {{FIN_HOLD_MASS_T}} t usable mass).
- Supply chain: base cost ${{FIN_BASE_COST_PER_KG}}/kg through the
  {{FIN_STAGE_LADDER}} multipliers, at {{FIN_PURITY}} purity. US-currency
  note mass {{FIN_BILL_MASS_G}} g and volume {{FIN_BILL_VOLUME_CM3}} cm³ per
  note [@bep_currency].
- Source of truth: `canonical_finance_params()` in `narcotics_finance.py`.

## Operations logistics

- Campaign network: {{LOG_NETWORK_LEGS}} legs across {{LOG_HUB_COUNT}} hubs
  — Isthmus City (IC), the refinery at Bogota (BOG), Hong Kong (HK), and
  Florida (FL) — each with a distance, cost, and interdiction risk. The
  routed problem is `{{LOG_ORIGIN}}` → `{{LOG_DESTINATION}}`.
- Weight keys: `risk` (via −ln(1−r) survival weights), `cost`, `distance`.
- Gadget budget {{LOG_CAPACITY_KG}} kg over {{LOG_GADGET_CANDIDATES}}
  candidate items from the film's loadout; Wavekrest cruise
  {{LOG_SPEED_KNOTS}} kn and {{LOG_ENDURANCE_NM}} nm endurance with
  {{LOG_REFUEL_HOURS}} h refuel stops.
- Source of truth: `canonical_logistics_params()` in
  `operations_logistics.py`.

## Surveillance and watchlist

- {{SURV_ACTION_COUNT}} covert actions, each with a signature, watch
  increment, and value.
- Detection logistic β₀ = {{SURV_BETA_0}}, β_watch = {{SURV_BETA_WATCH}},
  β_signature = {{SURV_BETA_SIGNATURE}}, threshold {{SURV_THRESHOLD}};
  exact survival-optimal ordering up to {{SURV_EXACT_LIMIT}} actions with a
  ratio-rule fallback beyond.
- Source of truth: `canonical_surveillance_params()` in `surveillance.py`.

## Software environment

- Package version {{BOND_VERSION}}; film identity `{{BOND_FILM}}`; codename
  `{{BOND_CODENAME}}`.
- Rendered variable map written to `output/data/manuscript_variables.json`;
  canonical mission results to `output/data/mission_results.json`.

> **On the timestamp:** `GENERATION_TIMESTAMP` is a wall-clock diagnostic and
> is the *only* token that varies between runs; every analytic token above is
> identical across reruns. This is the documented exception that keeps the
> rest of the output byte-reproducible.
