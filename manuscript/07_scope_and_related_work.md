# Scope and Related Work

## Scope

This package models the *analytical scaffolding* of the ROGUE mission, not
its fiction. It does not attempt to simulate human behaviour, the cartel's
actual personnel, or the film's events; it provides reproducible,
first-principles tools a field analyst would use. The inference objects are
deliberately stylised: the laundering graph abstracts real banking structure,
the vessel profile abstracts a real vessel class, and the rogue model
abstracts an operator's options into a three-intensity action ladder.
Generalisations to genuine transaction histories, real vessel data, or
richer action spaces are natural extensions but are out of scope here.

## Related work

- **Money laundering.** Layering and integration are standard in the
  financial-crime literature; our cycle + funnel + dirty-flow propagation
  operationalises them on an explicit graph. Financial Action Task Force
  (FATF) typology reports describe the placement–layering–integration
  lifecycle this model encodes.
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
modelled objects*, and the objects are idealised. The laundering score
weights are heuristics; the vessel physics ignore sea state, fouling, and
auxiliary loads; the dynamic program uses a quantised exposure lattice; the
narcotics prices are order-of-magnitude anchors rather than market data; the
logistics network abstracts real geography into four hubs; and the
surveillance model's exact ordering is brute-force for small n (n ≤ 8), with
a ratio-rule heuristic beyond. Each of these is documented where the
corresponding parameter lives in source, and each is open to principled
extension behind the same frozen `bond-api` protocol.
