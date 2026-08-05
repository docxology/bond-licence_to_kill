# licence_to_kill TODO

Forward-only backlog for the ROGUE film package (*Licence to Kill*, 1989).
Completed work is not logged here — `git log` is the history. This file
holds only what is **still open**, plus the dated verification record that
the README and AGENTS.md point at instead of quoting stale numbers.

## Verification record

Measured 2026-08-05 on this tree, Python 3.14.6 / NumPy 2.4.2:

| Command | Result |
|---|---|
| `uv run pytest tests/ --cov=src --cov-fail-under=90` | **191 passed**, 0 failed, 0 skipped — **100.00 %** line + branch on `src/` (all nine modules at 100 %) |
| `uv run ruff check src/ scripts/ tests/` | clean |
| `uv run ruff format --check src/ scripts/ tests/` | clean (39 files) |
| `uv run mypy src/ scripts/` | clean (20 source files) |
| `uv run python scripts/z_generate_manuscript_variables.py` | 108 tokens, 4 figures, 9 rendered sections |

Re-measure rather than trust this table; it is a record of one run, not a
standing guarantee. The standing guarantee is the `--cov-fail-under=90`
gate.

## Open — modelling

- **Rogue alert lattice is coarse.** The DP optimises over integer alert
  states, so the visibility ladder is truncated onto it and the canonical
  stealth intensity (visibility 0.5) contributes *no* alert increase. The
  optimiser and the reported trajectory now share one transition
  (`next_alert`), and replaying the optimal sequence reproduces the optimal
  value exactly — so the model is self-consistent — but it is coarser than
  the parameters suggest. Options: a half-integer alert lattice, or an
  explicitly integral visibility ladder. Either changes the canonical
  optimal policy, so it needs a deliberate decision, not a drive-by fix.
  Documented in `manuscript/07_scope_and_related_work.md`.
- **Layering-path enumeration saturates its cap.** `LAUNDERING_PATHS`
  reports the cap (200), not the true chain count, so the depth component of
  the layering score is computed over a truncated sample. Either raise the
  cap and measure the cost, or switch to a sampled-with-replacement estimate
  with a stated confidence. Currently disclosed in the manuscript rather
  than fixed.
- **Layering-score weights are unjustified.** `LAYERING_WEIGHTS` (0.4 / 0.3
  / 0.3) are a hand-chosen blend. They make the score useful for ranking
  structures against each other but meaningless as an absolute. A
  sensitivity sweep over the weight simplex would at least bound how much
  the ranking depends on them.
- **The canonical gadget instance does not discriminate exact from greedy.**
  The exact 0/1-knapsack DP and a greedy value-density pass select the same
  five items at the same value and weight on the canonical set, so the
  campaign data cannot demonstrate the DP's advantage; the advantage is
  demonstrated on a constructed counterexample instead
  (`test_greedy_value_density_is_suboptimal_on_a_counterexample`). A
  canonical gadget set on which the two genuinely diverge would let the
  manuscript make the point from the film's own data. Both facts are pinned
  by tests so the prose cannot re-inflate the claim.
- **Per-leg interdiction risks are independent and static.** The route
  survival product assumes independence across legs, which is the least
  defensible assumption in `operations_logistics.py`. A correlated-risk
  variant would change the optimal route, not just its score.

## Open — integration

- **`bond-utilities` provenance is not bound.** Outcome persistence is still
  the package's own tagged-JSON writer. If `record_provenance_outcome`
  (Layer 0) should own the shared mission-record format, delegate to it.
  Acceptance: `scripts/mission_execute.py` writes via
  `bond_utilities.mission_io` when importable, falling back to the current
  writer otherwise.
- **Fleet manuscript renderer not adopted.** Token hydration is local
  (`output/manuscript/`). Adopting the fleet renderer is optional and has no
  blocker; it simply has not been done.
- **`bond-api` (frozen) and coordinator handoff** need no work — discovery
  by slug already works through the local path dependency.

## Not open (deliberate non-goals)

- No remote, no push, no Zenodo/GitHub deposit. This is a local-only tree.
- No Monte Carlo anywhere. Every domain is closed-form or exact by
  construction, and the determinism proofs depend on it.
- No change to the frozen protocol surface (`MissionProvider`,
  `GADGET_REGISTRY`, `run_rogue_mission`) — other packages consume it.
