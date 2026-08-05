# Reproducibility

## Determinism contract

The ROGUE mission is deterministic by construction:

- **Fixed seed.** The canonical network uses `seed {{SEED}}`; a seeded
  generator draws the edge amounts, so the same seed always yields the same
  graph and the same report. `tests/test_laundering_graph.py` asserts that
  `seed 0` reproduces an identical edge set and that a different seed
  changes it.
- **No random draws in the detectors.** Cycle, funnel, dirty-flow,
  integration, entropy, forensic-physics, and dynamic-programming routines
  are pure arithmetic.
- **No wall-clock in persisted outputs.** Provenance `wall_time_s` is fixed
  at `0.0`; the only time-sensitive artifact is the `GENERATION_TIMESTAMP`
  diagnostic, which is explicitly excluded from byte reproducibility.
- **Byte determinism of figures.** `tests/test_figures.py` renders each
  figure twice into independent directories and asserts byte-identical PNGs.
- **End-to-end determinism.** `tests/test_mission.py` executes the mission
  twice and asserts identical result dictionaries and provenance hashes.

## Provenance

Every `MissionOutcome` carries a `Provenance` with the package version
({{BOND_VERSION}}), the `seed` ({{SEED}}), a `sha256` `input_hash` over the
canonical network (node set and edge amounts), and `wall_time_s = 0.0`. The
hash makes any ROGUE outcome independently auditable without re-running the
film: re-compute the hash over the same inputs and it must match.

## Test coverage

The source tree is covered well above the enforced 90 % line + branch floor
(`uv run pytest tests/ --cov=src --cov-fail-under=90`). Coverge levels and the
live test count are tracked in the shared monorepo
`docs/_generated/COUNTS.md` and are never hard-coded here.

## Artifacts

Regenerable output (git-ignored) lives under `output/`:

- `output/data/mission_outcome.json` — tagged `MissionOutcome` from
  `scripts/mission_execute.py`;
- `output/data/mission_results.json` and `output/data/manuscript_variables.json`
  from `scripts/z_generate_manuscript_variables.py`;
- `output/manuscript/*.md` — numbered sections with generated tokens substituted;
- `output/figures/*.png` — the four ROGUE figures.

Re-running `scripts/z_generate_manuscript_variables.py` regenerates all of
these deterministically. Environment: Python {{PYTHON_VERSION}}, NumPy
{{NUMPY_VERSION}}, film `{{BOND_FILM}}`, codename `{{BOND_CODENAME}}`,
package version {{BOND_VERSION}}.
