# Experimental Setup

All experiments are deterministic and reproducible under Python
{{PYTHON_VERSION}} with NumPy {{NUMPY_VERSION}}. Parameters are declared in
`manuscript/config.yaml` (the `mission:` block) and consumed by the domain
core; nothing is hard-coded in prose.

## Laundering network

- Placement sources (street collectors): `S1`–`S3`.
- Integration sinks (banks): `B1`–`B4`, mixed with legitimate exporter flows
  (`L1`–`L3`) into the same sinks so integration is non-trivial.
- Edge amounts drawn from a seeded generator (`seed {{SEED}}`): the same seed
  always yields the same graph and therefore the same report.
- Detector limits: cycle search depth 8 (capped at 50 cycles), layering-path
  enumeration capped at 200 chains.

## Vessel forensics

- Profile: the canonical Wavekrest-class mothership
  (`WAVEKREST_CLASS` in `vessel_forensics.py`).
- Observed quantities that expose covert modification: dry cargo mass
  {{VESSEL_ANOMALY_SCORE}}-triggering density and an under-declared
  displacement (see `mission._VESSEL_OBSERVED`).

## Rogue-00 risk model

- Horizon {{ROGUE_HORIZON}} steps; discrete alert states 0..{{ROGUE_ALERT_MAX}}.
- Action card *{{ROGUE_ACTION_CARD}}* with visibility and gain ladders.
- Continuous exposure quantised onto a 21-cell lattice
  (`exposure_cap 20`), giving a backward-induction lattice of
  {{ROGUE_POLICY_CELLS}} state cells.

## Narcotics-finance economics

- Intercepted courier parcel: US${{FIN_VALUE_USD}} in ${{FIN_DENOMINATION}}
  notes (the film's opening intercept), against the Wavekrest-class hold
  (520 m³, 300 t usable mass).
- Supply chain: base cost $1,500/kg through export → wholesale → street
  multipliers, at 60 % purity. US-currency note mass 1.0 g and volume
  1.13 cm³ per note.
- Source of truth: `canonical_finance_params()` in `narcotics_finance.py`.

## Operations logistics

- Campaign network connecting Isthmus City (IC), Bogota (BOG), Hong Kong
  (HK), and Florida (FL); per-leg distance, cost, and interdiction risk.
- Weight keys: `risk` (via −ln(1−r) survival weights), `cost`, `distance`.
- Gadget budget 25 kg over the canonical film loadout; Wavekrest cruise
  10 kn and ~4,257 nm endurance with 24 h refuel stops.
- Source of truth: `canonical_logistics_params()` in `operations_logistics.py`.

## Surveillance and watchlist

- Five covert actions, each with a signature, watch increment, and value.
- Detection logistic β₀ = −4.0, β_watch = 1.2, β_signature = 1.5, threshold
  0.5; exact survival-optimal ordering (n ≤ 8) with ratio-rule fallback.
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
