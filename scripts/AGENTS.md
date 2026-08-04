# scripts/ — thin ROGUE mission CLIs

Thin orchestrators only. They bootstrap `sys.path` (via `_bootstrap.py`),
drive the `MissionProvider` (or the manuscript/figure pipeline), and
print/serialise. No business logic lives here.

- `_bootstrap.py` — shared helper: injects repo root + `src/` on `sys.path`,
  exposes `PROVIDER` and `OUTPUT`.
- `00_preflight.py` — gate checks (protocol surface, provider conformance,
  gadgets, domain-core imports). Exit 0 iff all pass.
- `mission_brief.py` / `mission_recon.py` / `mission_plan.py` /
  `mission_execute.py` / `mission_debrief.py` — one CLI per mission phase.
  `mission_execute.py` persists `output/data/mission_outcome.json`.
- `z_generate_manuscript_variables.py` — writes
  `output/data/{mission_results,manuscript_variables}.json`, renders
  `output/manuscript/*.md`, and generates `output/figures/*.png`. Strict by
  default; `--allow-draft` relaxes unresolved-token failures.

Run from the package root: `uv run python scripts/<name>.py`.
