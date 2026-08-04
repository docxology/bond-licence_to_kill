# data/

Advisory validation inputs for `licence_to_kill` (ROGUE):

- `claim_ledger.yaml` — sourced numeric/algorithmic claims (IMO GT formula,
  seawater density, diesel SFC, DFS cycle enumeration, backward induction)
  mapped to the modules that use them.

This directory holds declarative inputs only. Deterministic analysis outputs
(figures, mission outcomes, variable maps) are regenerated under `output/`
by `src/` and `scripts/`, and are git-ignored.
