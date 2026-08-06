# Scope and Related Work

## Scope

This package models the *analytical scaffolding* of the ROGUE mission, not
its fiction. It does not attempt to simulate human behaviour, the cartel's
actual personnel, or the film's events; it provides reproducible,
first-principles tools a field analyst would use. All six inference objects
are deliberately stylised: the laundering graph abstracts real banking
structure, the vessel profile abstracts a real vessel class, the rogue model
abstracts an operator's options into a three-intensity action ladder, the
price ladder abstracts a market into fixed multipliers, the campaign network
abstracts world geography into {{LOG_HUB_COUNT}} hubs, and the surveillance
model abstracts an intelligence apparatus into a single logistic hazard.
Generalisations to genuine transaction histories, real vessel data, market
price series, real route networks, or richer action spaces are natural
extensions but are out of scope here.

## Related work

- **Money laundering.** Layering and integration are standard in the
  financial-crime literature; our cycle + funnel + dirty-flow propagation
  operationalises them on an explicit graph. Financial Action Task Force
  recommendations and typology reporting [@fatf2020] describe the
  placement–layering–integration lifecycle this model encodes.
- **Narcotics finance and cash physics.** Supply-chain price/purity ladders
  follow the order-of-magnitude cost structure reported in US Drug
  Enforcement Administration price analyses [@dea_prices]; the conversion of
  value into note mass/volume follows US Bureau of Engraving and Printing
  currency specifications [@bep_currency].
- **Graph algorithms.** Depth-first cycle enumeration follows Tarjan's
  depth-first-search framing [@tarjan1972]; risk-adjusted routing is
  Dijkstra's algorithm [@dijkstra1959]; the gadget loadout is the 0/1
  knapsack problem solved by dynamic programming [@kellerer2004].
- **Vessel forensics.** Gross-tonnage computation implements the
  International Convention on Tonnage Measurement of Ships, 1969
  [@imo1969]; endurance modelling uses the standard cubic propulsion-power
  law and diesel specific fuel consumption.
- **Sequential decision-making.** The rogue-00 model is a finite-horizon
  Markov decision process solved exactly by dynamic programming [@bellman1957];
  the surveillance ordering rule follows Smith's ratio rule for
  single-stage scheduling [@smith1956].
- **Source material.** The mission is drawn from the 1989 film directed by
  John Glen [@licence1989].

## Limitations

Determinism is a feature, but also a boundary: results are exact *for the
modelled objects*, and the objects are idealised.

- The composite laundering score's component weights
  ({{LAYERING_WEIGHT_CYCLE}} / {{LAYERING_WEIGHT_DEPTH}} /
  {{LAYERING_WEIGHT_FUNNEL}}) are heuristics, not estimates from labelled
  data. The score is not a calibrated absolute quantity, and its *ranking* of
  two structures is not invariant to the weights either: over a coarse
  sampling of the weight simplex ({{LAYERING_RANKING_SAMPLES}} weight
  triples) the ordering of two deliberately distinct reference structures
  matches the canonical-weight ordering on only
  {{LAYERING_RANKING_STABILITY}} of the samples. Measured, not assumed — the
  number is a token from `layering_ranking_stability()` in
  `manuscript_variables.py`, and the non-invariance is a pinned test
  (`test_layering_score_ranking_is_weight_dependent`). Treat the composite
  score as a screening heuristic for gross differences, never as a stable
  single-number ordering.
- `LAUNDERING_PATHS` is the exact source→sink chain count for the canonical
  network, not a truncated sample: the enumeration cap
  ({{LAUNDERING_MAX_PATHS}}) sits strictly above the true count and the depth
  component is computed over the full chain population (see
  `test_canonical_layering_path_count_is_exact_not_saturated`).
- The vessel physics ignore sea state, hull fouling, and auxiliary loads;
  endurance is a flat-water, single-speed idealisation.
- **The rogue model's alert dimension is an integer lattice**, so the
  visibility ladder is truncated onto it. At the canonical parameters the
  stealth intensity's visibility ({{ROGUE_STEALTH_VISIBILITY}}) truncates to
  *no* alert increase, which is why the optimal policy enters every one of
  its steps at alert 0 and the blowback hazard it faces is driven by
  exposure alone. Its single escalation is the closing overt action, which
  leaves alert at {{ROGUE_TERMINAL_ALERT}} with no remaining horizon to be
  exposed to it — reported as `ROGUE_PEAK_ALERT`
  ({{ROGUE_PEAK_ALERT}}) rather than folded into the entering-alert curve,
  because a peak taken over entering alert alone is identically zero for
  this policy and would misdescribe it. This is the most consequential
  simplification in the package and it is stated here rather than buried:
  a finer alert lattice, or an explicitly integral visibility ladder, would
  change the optimal policy. The quantisation is at least *consistent* — the
  optimiser and the reported trajectory share one transition function, and
  the test suite pins that replaying the optimal sequence reproduces the
  optimal value exactly.
- The narcotics prices are order-of-magnitude anchors [@dea_prices] rather
  than market data, and the stage multipliers are fixed rather than
  estimated.
- The logistics network abstracts real geography into {{LOG_HUB_COUNT}} hubs
  with static per-leg risks; interdiction risk in reality is neither static
  nor independent across legs, and the survival-product metric assumes
  independence.
- The surveillance model's exact ordering is brute-force for small n
  (n ≤ {{SURV_EXACT_LIMIT}}), with a ratio-rule heuristic beyond; the
  heuristic carries no optimality guarantee for this objective.

Each of these is documented where the corresponding parameter lives in
source, and each is open to principled extension behind the same frozen
`bond-api` protocol.
