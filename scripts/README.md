# scripts/ — quick reference

Thin CLIs for the ROGUE mission:

```bash
uv run python scripts/00_preflight.py
uv run python scripts/mission_brief.py
uv run python scripts/mission_recon.py "your goal"
uv run python scripts/mission_plan.py
uv run python scripts/mission_execute.py     # writes output/data/mission_outcome.json
uv run python scripts/mission_debrief.py
uv run python scripts/z_generate_manuscript_variables.py   # hydrate manuscript + figures
```

All exit 0 on success; preflight and z_generate may exit 1 on gate
failures. See `AGENTS.md` for responsibilities.
