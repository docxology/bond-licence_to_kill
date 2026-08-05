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

**C2 · `LAUNDERING_PATHS` reports the enumeration cap, not the chain count.**
`canonical_laundering_params()` sets `max_paths: 200`
(`src/licence_to_kill/laundering_graph.py:474`) and the canonical network
saturates it — `tests/test_canonical_params.py:145` asserts
`len(baseline.layering_paths) == max_paths`, which is exactly the saturation
proof. So the reported `{{LAUNDERING_PATHS}}` = 200 is a lower bound, and the
depth component of the composite layering score
(`laundering_graph.py:386`) is computed over a truncated, enumeration-order-
biased sample rather than over the chain population. Disclosed in
`manuscript/03_results.md:19-22` and
`manuscript/07_scope_and_related_work.md:56-58` rather than fixed.
**Done looks like:** either the cap is raised until the canonical network no
longer saturates it (and the enumeration cost is measured and recorded), or
the depth component is switched to a sampled estimate with a stated
confidence interval. Either way `test_canonical_params.py:145` flips from
asserting equality-with-the-cap to asserting strictly-below-the-cap, and the
"read as at least this many" caveats leave the manuscript.
**Command:** `uv run pytest tests/test_canonical_params.py tests/test_laundering_graph.py -v`

### Verification — claims not yet bound by a test that can fail for the right reason

**V1 · The direct-leg baseline binding is lexical, not behavioural.**
`{{LOG_DIRECT_RISK}}` must come from the *direct leg* IC→FL, not from the
distance-minimal path. On the canonical network the two coincide (both give
0.300), so no value assertion on `generate_variables` can discriminate the
two implementations. The guard that stops the token generator regressing to
routing is `tests/test_manuscript_variables.py:223-236`, which asserts
`"shortest_path" not in source` on the text of
`src/licence_to_kill/manuscript_variables.py`. It is falsifiable (proven red
on revert) and honestly documented as a source-text guard in its own
docstring, but it is defeated by an alias import (`from ... import
shortest_path as _sp`) and it forbids any future legitimate use of routing
in that module. The semantic and behavioural discrimination lives elsewhere
(`test_direct_leg_risk_reads_the_direct_leg_not_the_shortest_path`,
`tests/test_figures.py::test_operations_figure_requires_a_real_direct_leg`).
*Carried from* `output/verify/licence_to_kill.unresolved.json` *entry 1.*
**Done looks like:** a behavioural binding on the production entry point —
inject a network into `generate_variables` (or into the params it reads) on
which the direct leg and the distance-minimal path give *different* risks,
and assert the token equals the direct-leg value. When that test exists, the
lexical guard at :223 can be deleted.
**Command:** `uv run pytest tests/test_manuscript_variables.py -v` — the new
test must go red when `direct_leg_risk` is swapped for a `shortest_path`
call, with the lexical guard removed.

**V2 · The layering score's "useful for ranking" claim is unbound.**
`LAYERING_WEIGHTS = (0.4, 0.3, 0.3)`
(`src/licence_to_kill/laundering_graph.py:53`, consumed at `:386`) is a
hand-chosen blend. `manuscript/07_scope_and_related_work.md:52-56` concedes
the score is meaningless as an absolute but asserts it is "useful for
ranking structures against each other". Nothing tests that ranking claim: no
test perturbs the weights and checks that the ordering of two distinct
networks survives. As written the manuscript makes a stability claim the
suite cannot falsify.
**Done looks like:** a test that builds ≥2 structurally distinct networks,
sweeps the weight simplex (a coarse grid is enough), and asserts the induced
ranking is invariant — or, if it is not invariant, the manuscript sentence
is weakened to the measured share of the simplex on which it holds, with
that number carried as a token.
**Command:** `uv run pytest tests/test_laundering_graph.py -v`

**V3 · The frozen-registry test does not express the additive-only rule.**
`AGENTS.md` ("Protocol integration") and `README.md` state that
`GADGET_REGISTRY` is frozen with **additive changes only**.
`tests/test_mission.py:140-151` asserts exact set equality against the eight
current names, so an addition and a removal are indistinguishable to the
gate — both simply require editing the literal. The rule "removals are
forbidden, additions are allowed" is stated only in prose.
**Done looks like:** the seven frozen callables plus `network_manifest`
asserted as a required *subset* (removal fails), with a separate explicit
assertion or comment recording that additions are permitted — so the diff
that adds a gadget does not look like the diff that deletes one.
**Command:** `uv run pytest tests/test_mission.py::test_gadget_registry_register -v`

### Documentation

**D1 · `pyproject.toml` still describes a three-domain package.**
`pyproject.toml:15` reads `description = "Licence to Kill: ROGUE —
special-agent mission software (money-laundering graph, vessel forensics,
rogue-00 risk model)"`, and the header comment at `pyproject.toml:1-5` says
the same. The package has had **six** domain cores since `c87e302`;
`narcotics_finance`, `operations_logistics`, and `surveillance` are absent.
This is the same defect the audit raised against `.zenodo.json` and
`codemeta.json` — those two were fixed and now name all six, but
`pyproject.toml` was not, so the stale text is republished into
`src/licence_to_kill.egg-info/PKG-INFO:4` on every build.
*Residue of* `output/verify/licence_to_kill.json` *finding 6.*
**Done looks like:** `pyproject.toml:15` and the `:1-5` comment name all six
domains, matching `.zenodo.json`'s description in substance; a rebuild
regenerates `PKG-INFO` with the corrected summary.
**Command:** `grep -c narcotics pyproject.toml src/licence_to_kill.egg-info/PKG-INFO`
— both counts must be ≥ 1.

**D2 · `STANDALONE.md` names three domains and quotes a stale coverage number.**
`STANDALONE.md:7-10` describes "a pure domain core (money-laundering graph,
vessel forensics, rogue-00 risk DP)" — three of six — and claims "a zero-mock
test suite at ~99 % line + branch coverage". The measured figure today is
100.00 %, and quoting any percentage there contradicts the package's own
convention, stated in `README.md` ("Coverage and test counts are
deliberately not quoted here") and in `AGENTS.md`, that the only coverage
number lives in this file with its measurement date. Note `STANDALONE.md:19-24`
is already correct — it names all six domains — so the file contradicts
itself.
*Residue of* `output/verify/licence_to_kill.json` *finding 6.*
**Done looks like:** `STANDALONE.md:7-10` names all six domain cores and
either drops the percentage entirely (pointing at `TODO.md`, as README and
AGENTS.md do) or quotes the dated measurement from this file's opening
paragraph.
**Command:** `grep -n "99 %\|surveillance" STANDALONE.md` — no `99 %` match,
and `surveillance` present in the opening description.

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

---

## Known limitations (not bugs)

These are accepted. Recording them here is what stops them being
re-litigated as findings.

- **No remote, no push, no deposit.** This is a local-only working tree with
  no git remote. `.zenodo.json`, `codemeta.json`, and `CITATION.cff` exist as
  metadata sidecars with all DOI/registrar fields dropped; they are never
  submitted anywhere.
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

Run from the package root (`projects/working/bond/licence_to_kill`). All
six must be clean; the first is the gate.

| Command | Expected |
|---|---|
| `uv run pytest tests/ --cov=src --cov-fail-under=90` | all tests pass; total coverage ≥ 90 % line **and** branch on `src/` (measured 192 passed / 100.00 % on 2026-08-05) |
| `uv run ruff check src/ scripts/ tests/` | `All checks passed!` |
| `uv run ruff format --check src/ scripts/ tests/` | `39 files already formatted` |
| `uv run mypy src/ scripts/` | `Success: no issues found in 20 source files` |
| `uv run python scripts/z_generate_manuscript_variables.py` | writes `output/data/manuscript_variables.json` (107 tokens), `output/data/mission_results.json`, 4 figures, and 9 rendered sections under `output/manuscript/` |
| the same command twice with `sleep 1` between, comparing `find output -type f \| sort \| xargs cat \| md5` | identical hashes — the byte-for-byte claim the manuscript makes. `tests/test_manuscript_variables.py::test_regeneration_is_byte_identical` runs this in-suite; the shell form is the independent check |

Install first if the environment is cold: `uv sync --extra dev` (a bare
`uv sync` prunes pytest, and `uv run pytest` then silently resolves a
different interpreter).

Sandbox note: `uv` cannot initialise its cache under the default sandbox
(`Failed to initialize cache at /Users/4d/.cache/uv`). Re-run the same
command with the sandbox disabled if you hit that; it is not a package
failure.
