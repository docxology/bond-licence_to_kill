# docs/ — licence_to_kill (ROGUE)

Index of this directory. Read
[`agent_instructions.md`](agent_instructions.md) before modifying any file —
it is the binding rulebook. Then [`architecture.md`](architecture.md) for
where things live and how `mission.py` implements the frozen protocol, and
[`testing_philosophy.md`](testing_philosophy.md) for the zero-mock testing
contract. [`README.md`](README.md) is the navigational front door.

## Hard constraints enforced here

- **Frozen protocol surface.** `MissionProvider` (no-arg constructor;
  `brief`/`recon`/`plan`/`execute`/`debrief`), `GADGET_REGISTRY`, and
  `run_rogue_mission` are consumed by `bond-cli`, the coordinator, and the
  orchestrator. Deepen inside; extend gadgets additively only.
- **Pure domain core.** The six concept modules never import `bond_api` or
  `infrastructure` — structurally verified in `tests/test_mission.py`.
- **Token-only manuscripts.** Every numeric value, result *and* parameter,
  is an injected token. Four gates in `tests/test_manuscript_variables.py`
  enforce it in both directions.
- **One declaration per scenario.** `canonical_*_params()` per domain, read
  by the mission adapter, the token generator, and the figure generators
  alike; `manuscript/config.yaml`'s `mission:` block is a mirror asserted
  equal by `tests/test_canonical_params.py`.
- **No mocks, no silent failure paths, no unreachable guards.**
- **≥ 90 % line + branch coverage** on `src/`, enforced by
  `--cov-fail-under=90` in `pyproject.toml`. The measured figure lives in
  `../TODO.md` with a date, never hard-coded in prose.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py
git status --short   # clean after a path-scoped commit
```

Local-only tree: no remote, never pushed.
