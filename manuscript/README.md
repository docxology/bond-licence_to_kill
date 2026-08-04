# licence_to_kill manuscript — quick reference

`licence_to_kill` (1989) · mission codename **ROGUE**.

- **Sections** `00_abstract` … `07_scope_and_related_work` + `99_references`.
- **Tokens** — injected via `src/licence_to_kill/manuscript_variables.py`.
- **Figures** — three PNGs generated deterministically by
  `src/licence_to_kill/figures/plots.py` into `output/figures/` and
  referenced by `@fig:laundering` / `@fig:rogue` / `@fig:vessel`.

Regenerate everything with:

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

This writes `output/data/mission_results.json`,
`output/data/manuscript_variables.json`, `output/manuscript/*.md`, and
`output/figures/*.png`.

See [`SYNTAX.md`](SYNTAX.md) for the token / citation / figure syntax and
[`AGENTS.md`](AGENTS.md) for maintenance rules.
