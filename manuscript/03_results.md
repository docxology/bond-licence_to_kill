# Results

All results below are deterministic outputs of the canonical seeded run
(seed {{SEED}}) and are re-computed verbatim by
`src/licence_to_kill/manuscript_variables.py` — the plain numbers you read
are injected tokens, not hand-typed values.

## 3.1 Layering and integration in the Sanchez network

The canonical network built by `build_sanchez_network(seed=0)` contains
**{{LAUNDERING_NODES}}** nodes and **{{LAUNDERING_EDGES}}** directed edges,
carrying a placed dirty value of **{{PLACEMENT}}** currency units. The
detectors identify:

- **{{LAUNDERING_CYCLES}}** money-returning cycle(s) — the direct layering loop
  that returns cash through the shell grid;
- **{{LAUNDERING_FUNNELS}}** funnels (collectors that concentrate the flow and
  distributors that scatter it);
- **{{LAUNDERING_PATHS}}** representative placement→integration chains
  (enumeration capped at 200), whose mean depth drives the depth component.

The composite **layering score** is **{{LAYERING_SCORE}}** (of a possible 1),
reflecting the substantial but deliberately incomplete obscuring structure.
The **integration score** is **{{INTEGRATION_SCORE}}**: the placed dirty
value is diluted to that degree by the legitimate exporter flows feeding the
same banks, with a **mixing entropy** of **{{MIXING_ENTROPY}}** nats across
the four integration sinks.

![Sanchez money-laundering graph; node colour is the dirty-flow share, laid
out left-to-right by laundering stage.](figures/laundering_network.png){#fig:laundering}

## 3.2 Wavekrest-class vessel forensics

The canonical profile resolves:

| Quantity | Value |
|---|---|
| Enclosed hull volume | {{VESSEL_HULL_VOLUME}} m³ |
| Gross tonnage (IMO) | {{VESSEL_GROSS_TONNAGE}} |
| Draft-predicted displacement | {{VESSEL_DISPLACEMENT}} t |
| Usable fuel | {{VESSEL_FUEL_TONNES}} t |
| Full-tank endurance | {{VESSEL_ENDURANCE_NM}} nm |

The forensic scan flags **{{VESSEL_ANOMALIES}}** anomalies (aggregate score
{{VESSEL_ANOMALY_SCORE}}): a cargo bulk-density inconsistent with boxed fish,
and a declared displacement that disagrees with the draft-predicted value —
consistent with concealed contraband load. The Wavekrest's own physics betray
its cargo before its crew does (@fig:vessel).

![Wavekrest-class forensic profile: hull volume, gross tonnage, fuel, and
draft-predicted displacement.](figures/vessel_forensics.png){#fig:vessel}

## 3.3 Rogue-00 optimal policy

For the canonical revoked-licence model (horizon {{ROGUE_HORIZON}} steps,
alert ceiling {{ROGUE_ALERT_MAX}}, action card *{{ROGUE_ACTION_CARD}}*), the
dynamic program evaluates **{{ROGUE_POLICY_CELLS}}** state cells and returns:

- an **optimal expected mission value** of **{{ROGUE_OPTIMAL_VALUE}}**;
- a **{{ROGUE_FIRST_ACTION}}** opening — the least-escalating intensity,
  confirming that a revoked-licence operator must build capability
  surreptitiously before any overt strike;
- a **peak blowback hazard** of **{{ROGUE_PEAK_BLOWBACK}}** late in the
  horizon, the point beyond which continued operation becomes nearly certain
  to draw retaliation (@fig:rogue).

![Rogue-00 escalation: alert/exposure build while the blowback hazard climbs
under the optimal policy.](figures/rogue_escalation.png){#fig:rogue}
