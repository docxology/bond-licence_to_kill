# src/ — licence_to_kill

Importable source for the ROGUE mission (Licence to Kill, 1989).

| Module | Role |
|---|---|
| `laundering_graph.py` | Sanchez money-laundering graph — layering/integration detection |
| `vessel_forensics.py` | Wavekrest-class vessel forensic physics & anomaly scan |
| `rogue_ops.py` | Revoked-licence (rogue-00) escalation + blowback risk DP |
| `mission.py` | Frozen `bond_api` `MissionProvider` adapter + gadgets |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from config + deterministic results |
| `figures/plots.py` | Deterministic matplotlib figures |

Pure by design: no module imports the monorepo `infrastructure` tree, and
only `mission.py` imports `bond_api`. All results are deterministic
(seed 0). See `docs/architecture.md` for the layer contract.
