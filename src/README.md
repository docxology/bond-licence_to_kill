# src/ — licence_to_kill

Importable source for the ROGUE mission (Licence to Kill, 1989).

| Module | Role |
|---|---|
| `laundering_graph.py` | Sanchez money-laundering graph — layering/integration detection |
| `vessel_forensics.py` | Wavekrest-class vessel forensic physics & anomaly scan |
| `rogue_ops.py` | Revoked-licence (rogue-00) escalation + blowback risk DP |
| `narcotics_finance.py` | Supply-chain price/purity ladder + US-note cash physics + hold manifest |
| `operations_logistics.py` | Risk-adjusted Dijkstra routing + exact 0/1-knapsack loadout + voyage plan |
| `surveillance.py` | Watchlist detection hazard + survival-optimal action ordering |
| `mission.py` | Frozen `bond_api` `MissionProvider` adapter + gadgets |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from config + deterministic results |
| `figures/plots.py` | Deterministic matplotlib figures |

Pure by design: no module imports the monorepo `infrastructure` tree, and
only `mission.py` imports `bond_api`. All results are deterministic
(seed 0), and each domain declares its scenario once in a
`canonical_*_params()` function shared by the mission adapter, the token
generator, and the figures. See `../docs/architecture.md` for the full layer
contract and a module-by-module walkthrough.
