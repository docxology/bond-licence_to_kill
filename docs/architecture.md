# architecture.md — licence_to_kill layering

## Layers

| Layer | Location | Allowed imports | Responsibility |
|---|---|---|---|
| Domain core | `src/licence_to_kill/{laundering_graph,vessel_forensics,rogue_ops}.py` | stdlib + numpy | Pure algorithms, deterministic |
| Protocol adapter | `src/licence_to_kill/mission.py` | `bond_api` + domain core | Five-stage `MissionProvider`; gadget registry |
| Presentation | `src/licence_to_kill/manuscript_variables.py`, `src/licence_to_kill/figures/` | domain core + config + matplotlib | Token hydration, deterministic figures |
| Thin CLIs | `scripts/` | `_bootstrap`, domain, `bond_api.serialization` | Drive mission phases |

Dependency arrow is one-directional: `scripts/ → src/` and
`mission.py → domain core`. Nothing imports upward, and no module imports
the monorepo `infrastructure` tree.

## Domain modules

- **`laundering_graph.py`** — `TransactionGraph` (directed weighted graph),
  cycle detection (DFS), funnel analysis, dirty-flow propagation,
  integration score, mixing entropy, composite layering score, and the
  seeded `build_sanchez_network` generator.
- **`vessel_forensics.py`** — IMO gross tonnage, hydrostatic displacement,
  fuel endurance, route plausibility, and the `anomaly_scan` forensic
  checks over a `VesselProfile`.
- **`rogue_ops.py`** — logistic blowback hazard, escalation projection, and
  the exact backward-induction `solve_optimal_policy` dynamic program.

## How to add a concept

1. Add a function/type to the relevant domain module (keep it pure).
2. Give it a real-data test in `tests/test_<module>.py`.
3. Wire it into `mission.py` if it should appear in the mission lifecycle
   (recon/execute results).
4. Add a manuscript token in `manuscript_variables.py` and reference it in
   prose; add a figure generator if it deserves one.

## Pack framework

The package is non-workspace: `scripts/_bootstrap.py` injects the repo root
and `src/` onto `sys.path`. Test bootstrap lives in `tests/conftest.py`
(pins `MPLBACKEND=Agg` and sets `sys.path`).
