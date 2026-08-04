# agent_instructions.md — operating rules for licence_to_kill

`licence_to_kill` is PROJECT BOND's film package for *Licence to Kill*
(1989), mission codename **ROGUE**. These rules bind any agent or developer
modifying the package.

## Rule 1 — Never mock

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Every test runs the real algorithms on real (deterministic) data.
A mock that passes because it stubs the wrong call signature hides a broken
algorithm — that is the failure mode we forbid.

## Rule 2 — Keep the domain core pure

`src/licence_to_kill/laundering_graph.py`, `vessel_forensics.py`, and
`rogue_ops.py` import only the standard library and numpy. They must never
import `bond_api` or `infrastructure`. The single allowed protocol import is
inside the adapter `src/licence_to_kill/mission.py`. Verification:
`tests/test_mission.py::test_pure_domain_modules_are_bond_api_free`.

## Rule 3 — Thin orchestrators

`scripts/` are thin CLIs. Business logic lives in `src/`. A script imports a
provider, drives a phase, and prints/serialises; it does not implement
algorithms.

## Rule 4 — Never hand-author metrics in prose

Every numeric value in `manuscript/[0-9]*.md` is an injected `{{TOKEN}}`
produced by `src/licence_to_kill/manuscript_variables.py::generate_variables()`.
Do not write a literal number that could change when config or the data
changes; do not write literal `{{TOKEN}}` placeholder text.

## Rule 5 — Determinism

Fixed seed (0), no random draws in detectors, no wall-clock in persisted
outputs (the `GENERATION_TIMESTAMP` diagnostic is the documented exception).
Figures must be byte-reproducible (`tests/test_figures.py`).

## Rule 6 — Types and docstrings

All public functions carry type hints and docstrings; `uv run ruff check`
and `uv run mypy src/ scripts/` must both pass clean.

## Rule 7 — Scope discipline

Only `projects/working/bond/licence_to_kill/` is yours. Never touch
siblings, bond root files, or the template repo. Local-only: no remote,
never push.

## Verification checklist (run before reporting done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo clean
git status --short   # clean after a path-scoped commit
```

Live coverage and test count live in the shared monorepo
`docs/_generated/COUNTS.md` (never hardcoded here).
