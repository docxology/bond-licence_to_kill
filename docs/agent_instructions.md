# Agent instructions — licence_to_kill (ROGUE)

`licence_to_kill` is PROJECT BOND's film package for *Licence to Kill*
(1989), mission codename **ROGUE**. These rules bind any agent or developer
modifying the package. They are ordered by how expensive it is to get them
wrong.

## Rule 1 — Do not change the frozen protocol surface

`src/licence_to_kill/mission.py` exposes three things the rest of the fleet
imports across package boundaries:

- the `MissionProvider` class — constructible with **no arguments**, with
  the five methods `brief`, `recon`, `plan`, `execute`, `debrief`;
- the module-level `GADGET_REGISTRY`;
- `run_rogue_mission(request) -> Debrief`.

`bond-cli`, the coordinator's reconcile pass, and the orchestrator consume
these by name. Renaming a method, changing an argument list, adding a
required constructor argument, or removing a gadget entry breaks other
packages you are not allowed to touch. **Deepen inside the methods; extend
the gadget registry additively only.** See
[`architecture.md`](architecture.md) §3 for the full contract.

## Rule 2 — Never mock

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Every test runs the real algorithm on real deterministic data. A
mock that passes because it stubs the wrong call signature hides a broken
algorithm — and every algorithm here feeds a published number.

Assert values, not shapes. `isinstance(x, float)` is not a test of
arithmetic.

## Rule 3 — Keep the domain core pure

These six modules import only the standard library and numpy:

```
laundering_graph.py   narcotics_finance.py
vessel_forensics.py   operations_logistics.py
rogue_ops.py          surveillance.py
```

They must never import `bond_api` or `infrastructure`. The single allowed
protocol import in the whole package is inside the adapter
`src/licence_to_kill/mission.py`. Verified by
`tests/test_mission.py::test_pure_domain_modules_are_bond_api_free`.

## Rule 4 — Thin orchestrators

`scripts/` are thin CLIs: import a provider, drive one phase, serialise,
print. They do not implement algorithms. If you find yourself writing
arithmetic in `scripts/`, it belongs in `src/`.

## Rule 5 — Never hand-author a metric in prose

Every number in `manuscript/[0-9]*.md` is an injected `{{TOKEN}}` produced
by `manuscript_variables.generate_variables()`. This covers *parameters* as
well as results: the hold volume, the gadget budget, the detection
threshold, and the search caps are all tokens.

Four live gates in `tests/test_manuscript_variables.py` enforce this — every
cited token must be generated, every generated token must be cited, every
declared parameter must reach prose as a token carrying its canonical value,
and no `{{...}}` may survive substitution. If you add a quantitative claim,
add the variable first, then cite the token.

## Rule 6 — One declaration per scenario

Each domain declares its scenario in a `canonical_*_params()` function.
`mission.py`, `manuscript_variables.py`, and `figures/plots.py` all read
those functions — do not reintroduce local copies of the constants. Mirror
any new parameter into the `mission:` block of `manuscript/config.yaml`;
`tests/test_canonical_params.py` asserts the two agree and will fail if you
change one without the other. **Change the Python first, then the YAML.**

## Rule 7 — Determinism

Fixed seed (0), no random draws in the detectors, no wall-clock in persisted
outputs — **no exceptions**. There used to be one (`GENERATION_TIMESTAMP`),
and it silently falsified the manuscript's byte-for-byte claim while a
fixed-`now` test declared it safe. Do not reintroduce a clock reading under
any name; `test_no_token_carries_a_wall_clock_value` rejects clock-shaped
token values and any `datetime` use in `manuscript_variables.py`. Figures
must stay byte-reproducible (`tests/test_figures.py`), and the whole
regeneration must stay byte-identical
(`test_regeneration_is_byte_identical`), which reruns the real generator
script twice and compares every artifact.

## Rule 8 — No silent failure paths, no unreachable guards

Do not wrap a computation in a bare `except` that substitutes a default.
"Clean" and "could not check" are different findings, and only one of them
is safe to report. `vessel_forensics.anomaly_scan` carried exactly this bug
— an invalid profile was silently scored as anomaly-free — and it is now
allowed to raise. Do not reintroduce the pattern.

Equally: do not write a guard no input can reach. Either delete it (and say
why in the docstring, as `TransactionGraph.funnels` does) or make it
reachable by injecting the parameter a test needs, as
`plot_operations_logistics` does.

## Rule 9 — Types and docstrings

All public functions carry type hints and docstrings. `ruff check`,
`ruff format --check`, and `mypy src/ scripts/` must all pass clean.

## Rule 10 — Scope and git discipline

Only this repository is yours — never touch whichever fleet monorepo
(`bond-api`, sibling film packages, template) supplied the `bond-api` path
dependency, and never edit that checkout from here. `main` is the default
branch and is published at <https://github.com/docxology/bond-licence_to_kill>:
commit path-scoped, never force-push, never rewrite published history.

## Verification checklist

Run all of these before reporting done, and read the output rather than the
exit code alone:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # regenerates output/
git status --short                                          # clean after commit
```

If you changed a number that appears in the manuscript, also read the
rendered section under `output/manuscript/`. A token can resolve correctly
and still sit inside a sentence the new value has made false — the prose
*around* a token is not covered by any gate, only by your reading. That is
the one failure mode the test suite structurally cannot catch for you.
