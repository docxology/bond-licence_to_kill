# Standalone Guide — licence_to_kill (ROGUE)

## Purpose

`licence_to_kill` is PROJECT BOND's deterministic film package for *Licence
to Kill* (1989), mission codename **ROGUE**. It demonstrates a complete,
gate-verified film package: a pure domain core (money-laundering graph,
vessel forensics, rogue-00 risk DP, narcotics finance, operations logistics,
surveillance), a frozen `bond-api` `MissionProvider`
adapter, token-driven manuscript, deterministic figures, and a zero-mock
test suite run against the coverage gate recorded in `TODO.md`.

## Repository and deposit

Source lives at <https://github.com/docxology/bond-licence_to_kill> (branch
`main`). No DOI is minted for this package, so the publication metadata
sidecars (`.zenodo.json`, `codemeta.json`, `CITATION.cff`) deliberately carry
no DOI/registrar fields.

## Provenance

`mission.py` emits a `Provenance` per outcome: package version
`0.1.0`, fixed seed `0`, a sha256 `input_hash` over the canonical network
*and* every parameter of all six domain scenarios, and `wall_time_s = 0.0`
— every ROGUE result is independently audit-able. The hash's domain
coverage is enforced by a per-domain mutation test, not by assertion.

## Quick start

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/00_preflight.py
uv run python scripts/mission_debrief.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Author

Daniel Ari Friedman — Active Inference Institute
(daniel@activeinference.institute, ORCID 0000-0001-6232-9096).
