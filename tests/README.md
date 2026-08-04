# tests/ — quick reference

```bash
uv run pytest tests/ -q                 # all tests
uv run pytest tests/ --cov=src --cov-fail-under=90   # coverage gate
uv run pytest tests/test_rogue_ops.py -k "solve_optimal" -v
```

Every test uses real, deterministic computation — no `unittest.mock`,
`MagicMock`, `@patch`, or `create_autospec`. Coverage tracked (not
hardcoded) in the shared `docs/_generated/COUNTS.md`.
