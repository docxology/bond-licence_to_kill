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
- **{{LAUNDERING_PATHS}}** representative placement→integration chains,
  whose mean depth drives the depth component. This is the enumeration cap
  ({{LAUNDERING_MAX_PATHS}}), not the true chain count: the canonical network
  saturates it, so the figure should be read as "at least this many".

The composite **layering score** is **{{LAYERING_SCORE}}** (of a possible 1),
reflecting the substantial but deliberately incomplete obscuring structure.
The **integration score** is **{{INTEGRATION_SCORE}}**: the placed dirty
value is diluted to that degree by the legitimate exporter flows feeding the
same banks, with a **mixing entropy** of **{{MIXING_ENTROPY}}** nats across
the {{LAUNDERING_SINK_COUNT}} integration sinks.

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
- a close on **{{ROGUE_LAST_ACTION}}**. The optimal policy holds the
  least-visible intensity for the whole horizon and spends its escalation on
  the final step, when there is no remaining future for the raised alert to
  damage — the classic finite-horizon end effect, arrived at here without
  being written in;
- a **peak blowback hazard** of **{{ROGUE_PEAK_BLOWBACK}}**, reached on the
  last step, and a **peak alert** of **{{ROGUE_PEAK_ALERT}}** —
  the level the closing overt action *leaves behind*, which is therefore
  also the terminal alert ({{ROGUE_TERMINAL_ALERT}}) (@fig:rogue). Read
  those two numbers carefully, because they say different things. No step
  in the horizon is ever exposed to that alert: it is raised by the final
  action and the mission then ends, which is exactly why the dynamic
  program is willing to buy it. Every step the operator actually faces is
  *entered* at alert 0, so the hazard he faces climbs on **accumulated
  exposure** alone — on the integer alert lattice the stealth intensity's
  visibility rounds to no alert increase at all. That is a boundary of the
  quantisation, not a claim that stealth is free — Section 7 states it
  plainly. The distinction is not cosmetic: a peak taken over the alert
  each step is entered with would report a flat zero for this policy and
  read as "the optimum never escalates", which is false.

![Rogue-00 escalation under the optimal policy. Two alert series are drawn:
the level each step is *entered* with (flat at zero here) and the level each
step's own action *leaves behind* — the second is the only one that shows
the closing overt escalation. Exposure and the blowback hazard climb
throughout.](figures/rogue_escalation.png){#fig:rogue}

## 3.4 Narcotics-finance economics

The canonical courier parcel is valued at **${{FIN_VALUE_USD}}** in
**${{FIN_DENOMINATION}}** notes — **{{FIN_BILLS}}** bills. US-currency note
physics give a bulk-cash mass of **{{FIN_CASH_MASS_KG}} kg** and a volume of
just **{{FIN_CASH_VOLUME_M3}} m³** (bulk density ≈ {{FIN_CASH_DENSITY}}
kg/m³). From a base production cost of **${{FIN_BASE_COST_PER_KG}}**/kg the
supply chain ({{FIN_STAGE_LADDER}}) prices a kilogram at
**${{FIN_WHOLESALE_PER_KG}}** wholesale and **${{FIN_STREET_PER_KG}}** at
street level (**${{FIN_STREET_PER_GRAM}}** per gram), or
**${{FIN_STREET_PURE_GRAM}}** per *pure* gram at {{FIN_PURITY}} purity — the
same value is quietly present at every stage.

Against the Wavekrest-class hold ({{FIN_HOLD_VOLUME_M3}} m³,
{{FIN_HOLD_MASS_T}} t usable mass), the parcel is
**{{FIN_MANIFEST_FEASIBLE}}** to fit and needs **{{FIN_TRIPS}}** trip(s).
The money is compact; the hard constraint is the cover cargo that must blend
with it — not the cash itself.

## 3.5 Operations logistics

Risk-optimal routing over the campaign network returns the layered path
**{{LOG_ROUTE}}** ({{LOG_ROUTE_LEGS}} legs, {{LOG_ROUTE_NM}} nm, costing
**${{LOG_ROUTE_COST}}**) with a cumulative interdiction risk of
**{{LOG_ROUTE_RISK}}** — against **{{LOG_DIRECT_RISK}}** for the direct
single leg, a **{{LOG_RISK_REDUCTION}}** reduction — the same pairing the
finance graph demonstrates in the money layer (@fig:operations). The voyage
requires **{{LOG_REFUELS}}** refuelling stops (against the Wavekrest's
{{LOG_ENDURANCE_NM}} nm endurance at {{LOG_SPEED_KNOTS}} kn) for roughly
**{{LOG_TRIP_DAYS}}** days at sea (**{{LOG_TRIP_HOURS}}** hours). The gadget
loadout under a {{LOG_CAPACITY_KG}} kg budget selects
**{{LOG_KNAPSACK_ITEMS}}** of {{LOG_GADGET_CANDIDATES}} candidates
(including the Walther PPK, explosive charges, and the surveillance kit)
worth **{{LOG_KNAPSACK_VALUE}}** mission points at
**{{LOG_KNAPSACK_WEIGHT}} kg**, computed by exact 0/1-knapsack dynamic
programming over the full capacity lattice.

On *this* instance that exactness buys nothing observable: a greedy
value-density pass returns the same {{LOG_KNAPSACK_ITEMS}} items at the
same value and the same weight, which
`tests/test_operations_logistics.py::test_greedy_matches_exact_on_the_canonical_instance`
records rather than hides. The claim being made for the DP is therefore not
"it beat greedy here" — it did not — but that it is optimal on *every*
instance, where greedy is not;
`test_greedy_value_density_is_suboptimal_on_a_counterexample` exhibits an
instance on which the greedy pass leaves value on the table.

![ROGUE operations network with the risk-optimal route highlighted against
the direct single leg.](figures/operations_logistics.png){#fig:operations}

## 3.6 Surveillance and watchlist

Across the **{{SURV_ACTION_COUNT}}**-action covert campaign, the
survival-optimal order — opening with *{{SURV_FIRST_ACTION}}*, the lowest-
signature move, and closing with *{{SURV_LAST_ACTION}}* — achieves a
probability of completing undetected of **{{SURV_SUCCESS}}**. Cumulative
detection crosses the {{SURV_THRESHOLD}} threshold on the
**{{SURV_COMPROMISE_STEP_ONE}}**th action, and the peak step hazard reaches
**{{SURV_PEAK_HAZARD}}**: the adversary's watchlist eventually prices the
campaign in, and the operator wins only by doing the cheaply-detectable work
first and the compounding-mistake last.

Because {{SURV_ACTION_COUNT}} ≤ {{SURV_EXACT_LIMIT}}, this ordering is the
exhaustively-verified optimum rather than the ratio-rule heuristic — no
permutation of these actions survives more often.

