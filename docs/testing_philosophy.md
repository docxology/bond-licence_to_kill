# Testing philosophy — licence_to_kill (ROGUE)

## Why zero mocks

No `unittest.mock`, `MagicMock`, `@patch`, `create_autospec`, or any other
mocking framework appears anywhere in `tests/`. Every test runs the real
algorithm on real, deterministic input.

The reason is specific to what this package is. Every module here computes a
number that the manuscript then publishes. A mock that returns a plausible
value proves the *call* happened, not that the arithmetic is right — and an
arithmetic error is exactly the failure this package cannot afford, because
it would propagate silently into a token, into prose, and into a figure. So
the tests compute the answer independently (a closed-form formula, a
hand-derived expectation, an exhaustive alternative) and compare.

The corollary discipline: a test that only asserts a value's *shape* — that
it is a float, that a dict has keys, that a list is non-empty — has not
tested the algorithm. Where shape assertions appear here they sit alongside
a value assertion, never instead of one.

## What "deterministic" buys, and how it is proved

Determinism is not a stylistic preference; it is what makes the manuscript
auditable. Four independent proofs run in the suite:

- **Seeded generation.** `test_laundering_graph.py` asserts `seed 0`
  reproduces an identical edge set *and* that a different seed changes it.
  The second half matters: a generator that ignored its seed would pass the
  first assertion trivially.
- **Byte-identical figures.** `test_figures.py` renders every figure twice
  into independent directories and compares bytes.
- **End-to-end mission determinism.** `test_mission.py` executes the full
  mission twice and asserts equal result dictionaries and equal provenance
  hashes.
- **Whole-regeneration byte identity.**
  `test_manuscript_variables.py::test_regeneration_is_byte_identical` runs
  the production generator script twice, a real second apart, into two copies
  of the package and compares every emitted artifact byte for byte. Its
  predecessor injected a fixed `now` and asserted the timestamp moved with
  it — a test that froze the only varying input and so certified a false
  claim: `GENERATION_TIMESTAMP` was persisted into
  `output/data/manuscript_variables.json` and made every rerun differ. The
  clock is gone, the exception with it, and
  `test_no_token_carries_a_wall_clock_value` keeps it out.

## What each suite actually proves

- **`test_laundering_graph.py`** — structure and accessors; validation
  errors; cycle detection, canonical deduplication, and capping; funnel and
  path statistics; dirty propagation including a pure circulation that must
  conserve mass; integration and entropy; `analyze_laundering`; generator
  determinism.
- **`test_vessel_forensics.py`** — the analytic physics against known
  formulas (IMO GT, displacement, endurance); validation errors; route
  plausibility; every `anomaly_scan` branch in *both* directions, including
  a clean voyage that flags nothing; that an invalid profile raises rather
  than scoring zero anomalies; and that the anomaly ceilings are the named
  constants, checked just under and just over each threshold.
- **`test_rogue_ops.py`** — model validation; logistic bounds and
  monotonicity; escalation projection; the shared integral alert transition;
  that the DP dominates *every* constant policy, not just one; and that
  replaying the DP's own optimal sequence reproduces its value exactly.
- **`test_narcotics_finance.py`** — price and purity chain; US-note cash
  physics; every manifest feasibility branch; trip counting.
- **`test_operations_logistics.py`** — Dijkstra over cost, distance, and
  risk, plus the stale-heap guard and the unreachable case; exact 0/1
  knapsack; trip planning with and without mid-leg refuelling.
- **`test_surveillance.py`** — logistic detection; product survival; exact
  versus heuristic ordering; compromise timing.
- **`test_mission.py`** — protocol conformance by `isinstance` against the
  runtime-checkable protocol; the full `run_mission` flow; end-to-end
  determinism; provenance; gadget registration; and the structural guard
  that no pure domain module mentions `bond_api`.
- **`test_canonical_params.py`** — that `manuscript/config.yaml`'s
  `mission:` block equals the executable parameters; that the declared
  search bounds are genuinely consumed; and that `mission.py` and
  `manuscript_variables.py` produce identical reports.
- **`test_manuscript_variables.py`** — the token map; determinism under a
  fixed `now`; and the live manuscript gates below.
- **`test_figures.py`** — every figure exists, is a valid PNG, renders
  byte-identically, and the unreachable-destination guard actually fires.
- **`test_scripts_smoke.py`** — every thin CLI runs as a real subprocess
  (`sys.executable`, `cwd=project_root`) and produces its declared artifact.
  Real processes, not imported `main()` calls, because the thing under test
  is that the script works when invoked the way the README says it is.

## The gates that protect the manuscript

Four tests enforce "never hand-author a metric" as a mechanism rather than a
hope:

1. **Every cited token is generated.** Any `{{TOKEN}}` appearing in
   `manuscript/[0-9]*.md` must exist in `generate_variables()`. Catches
   typos and deleted tokens.
2. **Every generated token is cited.** A token nobody references is dead
   weight that will silently drift out of correctness. The exception list is
   now empty — `GENERATION_TIMESTAMP` was its only entry, and removing the
   wall clock removed it. This gate found two orphaned tokens the day it was
   added.
3. **Every declared parameter is bound end to end.** For each canonical
   parameter the test asserts the token carries the exact canonical value
   *and* that at least one numbered section cites the token. This catches
   the tempting regression: someone "simplifying" prose by typing the number
   directly, severing it from source.
4. **No unresolved placeholder survives.** After substitution, no `{{...}}`
   may remain in any numbered section.

## Guards must be able to fail

A branch no input can reach is indistinguishable from no branch at all. Two
consequences visible in this package:

- Dead defensive code is removed rather than left for coverage to paper
  over. `TransactionGraph.funnels` carried an isolated-node guard that could
  never fire (nodes only enter the graph via edges) and could not have
  changed the result if it had; it is gone, and the docstring records why.
- Where a guard is genuinely needed but unreachable with canonical data, the
  function takes an injectable parameter so a test can reach it —
  `plot_operations_logistics(outdir, params=...)` exists for exactly that
  reason.

## Coverage

The gate is ≥ 90 % line **and** branch on `src/`, enforced in
`pyproject.toml` via `--cov-fail-under=90`. Branch coverage is the point:
line coverage alone would let a two-way condition pass having only ever been
observed in one direction, which is how an inverted comparison survives a
green suite.

Measured figures are not quoted in these docs. The gate is the claim; the
current measurement lives in `TODO.md` with a date, where it can be checked
against a command rather than trusted.

## Canonical run

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```
