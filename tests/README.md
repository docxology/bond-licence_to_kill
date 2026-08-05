# tests/ — quick reference

```bash
uv run pytest tests/ -q                 # all tests
uv run pytest tests/ --cov=src --cov-fail-under=90   # coverage gate
uv run pytest tests/test_rogue_ops.py -k "solve_optimal" -v
```

Every test uses real, deterministic computation — no `unittest.mock`,
`MagicMock`, `@patch`, or `create_autospec`.

The coverage gate is >= 90 % line + branch on `src/`, enforced by
`--cov-fail-under=90`. The current measured figure lives in
[`../TODO.md`](../TODO.md) with the date it was taken; it is deliberately
not quoted here. Rationale and per-suite coverage:
[`../docs/testing_philosophy.md`](../docs/testing_philosophy.md).
