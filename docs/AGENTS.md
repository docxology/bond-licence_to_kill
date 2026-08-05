# docs/ — licence_to_kill

Technical guide for the ROGUE mission package. Read
[`agent_instructions.md`](agent_instructions.md) before modifying any file —
it is the binding rulebook. Then [`architecture.md`](architecture.md) for
layer boundaries and [`testing_philosophy.md`](testing_philosophy.md) for
the zero-mock testing contract.

## Hard constraints enforced here

- **Pure domain core** — the six concept modules never import `bond_api`
  or `infrastructure` (structural guard in `tests/test_mission.py`).
- **Token-only manuscripts** — every numeric result is an injected token.
- **≥ 90 % line + branch coverage** on `src/` (live number in the shared
  `docs/_generated/COUNTS.md`).
- **No mocks**, deterministic figures, thin scripts.

## Verification

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
git status --short   # clean after a path-scoped commit
```
