# TODO — licence_to_kill (ROGUE)

`licence_to_kill` is the PROJECT BOND film package for *Licence to Kill*
(1989), mission codename **ROGUE**: six pure, deterministic domain cores
(laundering graph, vessel forensics, rogue-00 policy DP, narcotics finance,
operations logistics, surveillance) behind the frozen `bond-api`
`MissionProvider` protocol, with a token-driven manuscript and a zero-mock
test suite. Measured on this tree on **2026-08-05** (Python 3.14.6, working
tree clean at `f67f90d` plus the wall-clock removal): **192 tests passed, 0
failed, 0 skipped**, and **100.00 % line + branch coverage** on `src/` — all
nine modules at 100 % (`ruff check`, `ruff format --check`, and
`mypy src/ scripts/` also clean; `z_generate_manuscript_variables.py` emits
107 tokens, 4 figures, 9 rendered sections, and two consecutive runs produce
byte-identical output). Re-measure rather than trust that line: it records one run, not a
standing guarantee. The standing guarantee is `--cov-fail-under=90`.

This file is forward-only. Completed work is not logged here — `git log` is
the history.

---

## Open work

### Correctness — things that are wrong

**C1 · The rogue alert lattice truncates the visibility ladder to zero for
the canonical stealth action.**
`alert_increment()` returns `int(model.visibility[action_idx])`
(`src/licence_to_kill/rogue_ops.py:93-109`), so the DP optimises over integer
alert states and the canonical `stealth` visibility of **0.5** contributes
*no* alert increase at all. The model is internally self-consistent — the
optimiser, `escalation_path()`, and `expected_value_of_policy()` all share
this one transition via `next_alert()` (`rogue_ops.py:112-115`), and the
suite pins that replaying the optimal sequence reproduces the optimal value
exactly — but it is coarser than the parameter values suggest, and the
optimal policy's "stealth is free" shape is an artefact of the lattice
rather than of the hazard model. Currently disclosed in
`manuscript/07_scope_and_related_work.md` (Limitations, rogue bullet) and in
the `alert_increment` docstring rather than fixed.
*Carried from* `output/verify/licence_to_kill.unresolved.json` *entry 3.*
**Done looks like:** either a half-integer (or finer) alert lattice in
`solve_optimal_policy`, or an explicitly integral visibility ladder in
`DEFAULT_VISIBILITY`, chosen deliberately — both change the canonical
optimal policy and therefore every pinned `ROGUE_*` token. Whichever is
chosen, `manuscript/07` loses this bullet and a test asserts that a
sub-unit-visibility action produces a non-zero alert increase.
**Command:** `uv run pytest tests/test_rogue_ops.py tests/test_manuscript_variables.py -v`
(the pinned `ROGUE_*` token assertions must be re-derived, not relaxed).

### Extension — genuine future work, nothing broken

**E1 · A canonical gadget set on which exact DP beats greedy.**
On the canonical 7-gadget / 25 kg instance the exact 0/1-knapsack DP and a
greedy value-density pass select the *same* five items at the same value
(32) and the same weight (17.7 kg), so the film's own data cannot
demonstrate the DP's advantage. Both facts are already pinned so the prose
cannot re-inflate the claim
(`tests/test_operations_logistics.py::test_greedy_matches_exact_on_the_canonical_instance`
and `::test_greedy_value_density_is_suboptimal_on_a_counterexample`), and
`manuscript/03_results.md:129-137` states it plainly. Fixing this means
choosing a canonical gadget set on which the two genuinely diverge — which
moves `LOG_KNAPSACK_*` and every pinned number downstream of it, so it is a
deliberate decision, not a drive-by edit.
*Carried from* `output/verify/licence_to_kill.unresolved.json` *entry 2.*
**Done looks like:** a `canonical_logistics_params()` gadget set on which
greedy is strictly suboptimal;
`test_greedy_matches_exact_on_the_canonical_instance` inverts to assert
divergence; `manuscript/03_results.md` makes the DP's point from the film's
data instead of from a constructed counterexample.
**Command:** `uv run pytest tests/test_operations_logistics.py tests/test_canonical_params.py -v`

**E2 · Correlated per-leg interdiction risk.**
`shortest_path` builds route survival as `math.prod(1.0 - leg.risk ...)`
(`src/licence_to_kill/operations_logistics.py:224`) and the risk weight
`-ln(1-r)` (`:155-157`) is additive only because the legs are assumed
independent. That is the least defensible assumption in the module —
interdiction is neither static nor independent in reality — and a correlated
variant would change the *optimal route*, not merely its score. Disclosed in
`manuscript/07_scope_and_related_work.md`.
**Done looks like:** a correlated-risk survival model (e.g. a shared latent
factor per corridor) behind the same `weight=` selector, with a test
exhibiting an instance where the correlated optimum differs from the
independent one.
**Command:** `uv run pytest tests/test_operations_logistics.py -v`

**E3 · Bind outcome persistence to `bond_utilities.mission_io`.**
`scripts/mission_execute.py` writes `output/data/mission_outcome.json` with
the package's own `bond_api.serialization.to_json`. Layer 0 already owns a
shared mission-record format: `record_provenance_outcome(...)` at
`../bond-utilities/src/bond_utilities/mission_io.py:153`, which bundles
`mission_id`, derived seed, version, hashed `input_payload`, and `outcomes`
into one validated record. `bond-utilities` is **not** currently a
dependency (`pyproject.toml:20-25` lists numpy, matplotlib, pyyaml, and
bond-api only), so this needs a dependency addition as well as a call.
**Done looks like:** `scripts/mission_execute.py` persists via
`bond_utilities.mission_io.record_provenance_outcome` when importable and
falls back to the current writer otherwise; a smoke test covers both
branches.
**Command:** `uv run pytest tests/test_scripts_smoke.py -v && uv run python scripts/mission_execute.py`

**E4 · Adopt the fleet manuscript renderer.**
Token hydration is local: `scripts/z_generate_manuscript_variables.py` writes
`output/manuscript/` (9 sections) itself.
`../bond-manuscript/src/bond_manuscript/` provides a fleet-wide renderer plus
`compendium.py`. There is no blocker — this is optional consolidation that
simply has not been done.
**Done looks like:** the 9 rendered sections and 4 figures are byte-identical
before and after the swap, produced by the fleet renderer.
**Command:** `uv run python scripts/z_generate_manuscript_variables.py && uv run pytest tests/test_manuscript_variables.py tests/test_figures.py -v`

**E5 · Generalise the idealised objects.**
`manuscript/07_scope_and_related_work.md` (Scope) lists the natural
extensions: real transaction histories in place of the seeded network, real
vessel data in place of the abstracted Wavekrest profile, market price series
in place of fixed stage multipliers, real route networks in place of the hub
abstraction, and a richer action space than the three-intensity rogue ladder.
Each sits behind the same frozen `bond-api` protocol, so none of them
requires reshaping the fleet surface.
**Done looks like:** whichever generalisation is chosen ships with its own
`canonical_*_params()` mirror in `manuscript/config.yaml` and passes
`tests/test_canonical_params.py`.
**Command:** `uv run pytest tests/ --cov=src --cov-fail-under=90`

### Lint configuration — recorded, and one open red

**V4 · The vendored copy is excluded from this package's lint gate, and this
records what that exclusion changes.**
`pyproject.toml` already declared this package's own configuration
(`line-length = 120`, `select = ["E4", "E7", "E9", "F"]`) rather than
inheriting the suite's; the vendoring added `extend-exclude = ["vendor"]` to
that table and `exclude = ["(^|/)vendor/"]` to `[tool.mypy]`, so the gate
judges this package's files and not the recorded copy's bytes. Measured at
ruff 0.16.1 with a two-arm control that keeps the table in this file and
varies only its body, whole-tree scope:

| Command | `extend-exclude = ["vendor"]` | that line removed |
|---|---|---|
| `ruff check .` | rc=0, `All checks passed!` | rc=0, `All checks passed!` |
| `ruff format --check .` | rc=1, **1** file, 71 already formatted | rc=1, **2** files, 79 already formatted |

So the exclusion removes nine files from the whole-tree file set and one
reformat target — `vendor/bond-api/README.md:95:1`, a fenced block in the
vendored copy's own README — while `ruff check` is clean either way. The
documented gate is scoped to `src/ scripts/ tests/` and moves only by the two
files the vendoring added (39 → 41, all formatted). The checker
`scripts/vendor.py` conforms to this package's declared width: clean under
`--line-length 120` (the gate above) and `ruff format --check --line-length 88
scripts/vendor.py` reports 1 file to reformat.
**Command:** `uv run ruff format --check . && uv run ruff format --check src/ scripts/ tests/`

**V5 · The whole-tree format check is red on a code block this gate does not
read, at both ends of this change.**
`ruff 0.16.1` formats fenced Python blocks in Markdown, so `ruff format
--check .` reports `README.md:71:31` at the pre-vendoring head `cc987b3` (1
file, 69 already formatted) and at this head (1 file, 71 already formatted).
Nothing regressed — the documented gate is scoped to `src/ scripts/ tests/`
and has never included `README.md` — but a whole-tree invocation is red on a
file the gate does not read, and this row exists so that red is not silently
carried by an expectation that does not mention its scope. Not fixed here:
the vendoring change does not own that line, and a README edit does not
belong in a dependency commit.
**Command:** `uv run ruff format --check .` (expect rc=1, `README.md:71:31`)

---

## Known limitations (not bugs)

These are accepted. Recording them here is what stops them being
re-litigated as findings.

- **No DOI, no registrar deposit.** The package is published as source at
  <https://github.com/docxology/bond-licence_to_kill> (branch `main`).
  `.zenodo.json`, `codemeta.json`, and `CITATION.cff` exist as metadata
  sidecars with all DOI/registrar fields dropped, so nothing in the tree
  announces a DOI it does not have.
- **No Monte Carlo anywhere.** Every domain is closed-form or exact by
  construction — seeded generation, analytic physics, exact DP, exact
  shortest path and knapsack, exhaustive permutation search. The determinism
  proofs (`seed = 0`, `wall_time_s = 0.0`, byte-deterministic figures) depend
  on this, so it is a design constraint, not an omission.
- **The frozen protocol surface does not change.** `MissionProvider`,
  `GADGET_REGISTRY`, and `run_rogue_mission` are consumed across package
  boundaries by `bond-cli`, the coordinator, and the orchestrator. Additive
  changes only. See V3 for the one place the test does not yet express this.
- **The DP's optimality is demonstrated on a constructed counterexample, not
  on the film's data.** This is the honest scope the audit forced: the
  canonical instance cannot discriminate exact from greedy (see E1), so the
  manuscript claims only that the DP is optimal on *every* instance, and
  proves it on an instance where greedy is not. That is a real claim, just a
  narrower one than "it beat greedy here".
- **`ROGUE_PEAK_ALERT` (3.0) is the alert the closing overt action *leaves
  behind*, not an alert any step is entered at.** Every step in the optimal
  policy is entered at alert 0 (see C1), so a peak taken over entering alert
  would be identically zero and would read as "the optimum never escalates",
  which is false. The two-series distinction is stated in
  `manuscript/03_results.md:70-84` and pinned at
  `tests/test_manuscript_variables.py:289-291`. This is an accepted reporting
  choice, not a defect.
- **The provenance `input_hash` changed** (`a1cd6fb6…` → `146ef283…`) as a
  necessary consequence of extending hash coverage to all six domains.
  Nothing pinned the old value and `output/` is git-ignored and was
  regenerated, but any external record of the previous hash is stale by
  design. *Carried from* `output/verify/licence_to_kill.unresolved.json`
  *entry 4* — informational, no action.
- **The exact surveillance ordering is brute force for small n**
  (n ≤ `SURV_EXACT_LIMIT`), with a ratio-rule heuristic beyond it; the
  heuristic carries no optimality guarantee for this objective. Stated in
  `manuscript/07_scope_and_related_work.md`.
- **Vessel physics ignore sea state, hull fouling, and auxiliary loads.**
  Endurance is a flat-water, single-speed idealisation. Stated in
  `manuscript/07_scope_and_related_work.md`.
- **Narcotics prices are order-of-magnitude anchors** from DEA price
  analyses, not market data, and the stage multipliers are fixed rather than
  estimated. Stated in `manuscript/07_scope_and_related_work.md`.

Checked and found *not* open: the six unreachable conditional guards the
audit flagged in `manuscript_variables.py` are gone — each is now a named,
documented, both-branches-tested helper (`direct_leg_risk`,
`risk_reduction`, `last_escalation_action`, `compromise_step_label`,
`order_endpoint`, at `manuscript_variables.py:141-188`). The `input_hash`
domain-coverage defect is closed and gated by a per-domain mutation test
(`tests/test_mission.py:170-203`). `.zenodo.json`, `codemeta.json`, and
`CITATION.cff` all name six domains. `docs/` carries no stale coverage
figure.

---

## Verification

Run from the repository root (a standalone clone of
`docxology/bond-licence_to_kill`). All six must be clean; the first is the
gate.

| Command | Expected |
|---|---|
| `uv run pytest tests/ --cov=src --cov-fail-under=90` | all tests pass; total coverage ≥ 90 % line **and** branch on `src/` (measured **197 passed / 100.00 %** — 1211 statements / 302 branches — on 2026-11-04; 192 passed on 2026-08-05) |
| `uv run ruff check src/ scripts/ tests/` | `All checks passed!` (measured 2026-11-04; `extend-exclude = ["vendor"]` keeps the vendored copy out of this file set — see V4) |
| `uv run ruff format --check src/ scripts/ tests/` | `41 files already formatted` (measured 2026-11-04; 39 before `vendor/bond-api` arrived — the two new files are `scripts/vendor.py` and `tests/test_vendor_provenance.py`) |
| `uv run mypy src/ scripts/` | `Success: no issues found in 21 source files` (measured 2026-11-04; 20 before `scripts/vendor.py`) |
| `uv run python scripts/z_generate_manuscript_variables.py` | writes `output/data/manuscript_variables.json` (**109 tokens**, measured 2026-11-04; 107 on 2026-08-05), `output/data/mission_results.json`, 4 figures, and 9 rendered sections under `output/manuscript/` |
| the same command twice with `sleep 1` between, comparing `find output -type f \| sort \| xargs cat \| md5` | identical hashes — the byte-for-byte claim the manuscript makes. `tests/test_manuscript_variables.py::test_regeneration_is_byte_identical` runs this in-suite; the shell form is the independent check |

Install first if the environment is cold: `uv sync --extra dev` (a bare
`uv sync` prunes pytest, and `uv run pytest` then silently resolves a
different interpreter). The install resolves `bond-api` from
`vendor/bond-api`, so a standalone clone needs no sibling checkout; a cold
clone of this repository is the configuration these numbers were measured in.

Sandbox note: `uv` cannot initialise its cache under the default sandbox
(`Failed to initialize cache at <home>/.cache/uv`). Re-run the same command
with the sandbox disabled if you hit that; it is not a package failure.

---

## Round-2 (2026-08-06)

Deep-improvement pass on a clean tree at `75fc750`. Baseline: 192 passed / 0
failed / 0 skipped, 100.00 % line + branch coverage; `ruff check`, `ruff
format --check`, and `mypy src/ scripts/` clean. Closed four open-work items
(C2, V1, V2, V3) and both documentation items (D1, D2):

- **C2 (closed) — `LAUNDERING_PATHS` reported the enumeration cap, not the
  chain count.** The canonical network saturated `max_paths = 200`, so the
  reported figure was a lower bound and the depth component came from a
  truncated, order-biased sample. Raised the cap to `DEFAULT_MAX_PATHS = 1000`
  (strictly above the true count, 720) in `laundering_graph.py` and mirrored
  it in `manuscript/config.yaml`; `LAUNDERING_PATHS` is now the exact count and
  the depth component is computed over the full chain population. Test evidence:
  `test_canonical_layering_path_count_is_exact_not_saturated` (pins the exact
  720 and the non-saturating cap; still limited by the halved cap, proving the
  bound binds). `LAUNDERING_PATHS` 200→720; `LAYERING_SCORE` 0.515→0.513. The
  "read as at least this many" caveats in `03_results.md` and
  `07_scope_and_related_work.md` are removed.

- **V1 (closed) — the direct-leg baseline binding was lexical, not
  behavioural.** `generate_variables()` and `_run_mission_analyses()` now accept
  an injectable `logistics_network`;
  `test_direct_baseline_binds_behaviourally_through_generate_variables` injects
  a network on which the direct `IC→FL` leg (risk 0.500) and the risk-optimal
  two-hop path (0.19) differ, and asserts `LOG_DIRECT_RISK` carries the direct
  leg's value through the production entry point. The old source-text guard
  `test_direct_baseline_is_not_computed_by_shortest_path` (defeatable by an
  alias import) is deleted.

- **V2 (closed) — the layering-score ranking overclaim is now measured and
  honest.** The composite score's induced order of two structurally distinct
  networks is *not* invariant to the weight blend: across the 21-point weight
  simplex both orderings occur and the canonical-weight ordering is reproduced
  on only 38 % of samples. The manuscript's "useful for ranking structures
  against each other" claim is weakened to that measured share, carried as
  tokens `LAYERING_RANKING_STABILITY` / `LAYERING_RANKING_SAMPLES` from a new
  `layering_ranking_stability()` helper in `manuscript_variables.py`. Test
  evidence: `test_layering_score_ranking_is_weight_dependent` (both orderings
  occur; share strictly in (0,1)) and
  `test_layering_ranking_tokens_are_live_and_consistent`.

- **V3 (closed) — the frozen-registry test now expresses the additive-only
  rule.** `test_gadget_registry_register` asserts the eight frozen entries as a
  required *subset* (`_FROZEN_GADGET_NAMES <= gadgets`), so removing one fails
  the suite while adding a ninth stays legal. The old exact-set-equality test
  could not distinguish a removal from an addition.

- **D1 (closed) — `pyproject.toml` described a three-domain package.** The
  header comment and `description` now name all six domain cores; `narcotics`
  appears in `pyproject.toml` and (after `uv sync`) in the rebuilt
  `src/licence_to_kill.egg-info/PKG-INFO`.

- **D2 (closed) — `STANDALONE.md` named three domains and a stale coverage
  figure.** The opening description names all six domains and drops the
  "~99 %" number, pointing at this file's dated measurement instead.

Manuscript deepened: added a headline-results overview table (`3.0`) to
`03_results.md` built from live tokens (so it cannot disagree with the
analysis), corrected the abstract and results for the exact chain count, added
an honest scope statement for the new ranking-stability measurement in
`07_scope_and_related_work.md`, and cited Shannon 1948 (`@shannon1948`) at the
mixing-entropy definition in `02_methodology.md`.

Final gates on this tree: **195 passed / 0 failed / 0 skipped, 100.00 % line +
branch coverage**; `ruff check` and `ruff format --check` clean; `mypy
src/ scripts/` clean; the manuscript regenerates 109 tokens, 4 figures and 9
sections byte-identically across two runs (hash `0d25044d…`).

Left for a future round (deliberately not closed this round): **C1** — the
rogue-alert integer lattice truncates the canonical stealth visibility to a
zero alert increase; changing it (half-integer lattice or an explicitly
integral ladder) alters the optimal policy and every pinned `ROGUE_*` token and
is a standalone, deliberate decision. The extension items **E1–E5** remain as
scoped future work; all are unchanged in behaviour this round.

---

## Maintenance pass (2026-10-25)

Legacy-and-documentation pass on a clean tree at `a7d0ea0`. No domain code
changed, no behaviour moved, no dependency or lockfile change:

- The "local-only tree, no remote, never pushed" claim (README, STANDALONE,
  AGENTS, `docs/`, this file, `manuscript/config.yaml` + `SYNTAX.md`) predated
  the GitHub remote and is replaced by the real source of record.
- Closed items **C2, V1, V2, V3, D1, D2** were still listed above as *open*
  work with "Done looks like" instructions — the state the Round-2 section
  already records as closed. They are removed from Open work; **C1** and
  **E1–E5** remain.
- `pyproject.toml` gained an explicit `[tool.ruff]` block (`line-length = 120`,
  the historical `E4,E7,E9,F` set). Modern ruff defaults (88 columns, a much
  wider rule set) failed the documented `ruff check` / `ruff format --check`
  gate on code nobody had reformatted — a red gate on an unchanged tree. The
  gate is now version-stable, and widening the rule set is a deliberate
  whole-tree migration rather than a tool-upgrade side effect.
- `scripts/00_preflight.py` asserted the three-domain gadget subset; it now
  asserts the eight frozen registry entries (subset, additive-only).
- `tests/test_manuscript_variables.py::test_project_root_path` required the
  checkout directory to be named `licence_to_kill`; the published repository is
  `bond-licence_to_kill`, so a canonical clone failed it. It now asserts
  repository markers, with the package directory name checked separately.
- `domain_profile.yaml` declared 3 figures (there are 4);
  `experiment_plan.yaml` now says where the phase-4 runs are declared.

Verification on this host (2026-10-25): `ruff check` and `ruff format --check`
clean under both the locked ruff 0.16.1 and 0.17.2; `mypy src/ scripts/` clean
under 2.3.0 and 2.4.0; 168 passed / 2 failed in the `bond-api`-free subset
(9 of 11 suites). Both failures are `ModuleNotFoundError: No module named
'bond_api'` — the dependency is a local path source with no checkout on this
host, so `test_mission.py` and `test_scripts_smoke.py`, and therefore the
full-suite test count and the byte-identical regeneration check, could not be
run here. Re-run the full gate where `[tool.uv.sources]` resolves.

## Workflowz review — 2026-11-10

Bounded review coverage: the supplied excerpts of the root guidance, README, existing TODO, Python/runtime and dependency configuration, package initializers, three domain modules, and three phase CLIs were inspected. No new concrete, independently closable improvement survived the evidence gate; existing TODO items were not duplicated. Re-review on a concrete failure or a relevant source/configuration change.
