# Methodology

This section specifies the six deterministic algorithms that constitute the
ROGUE analytical core. Deep familiarity with each module's source is the
intended reader path: `src/licence_to_kill/laundering_graph.py`,
`vessel_forensics.py`, `rogue_ops.py`, `narcotics_finance.py`,
`operations_logistics.py`, and `surveillance.py`.

Every declared constant below is reported as an injected token drawn from
that module's `canonical_*_params()` function or its named module constants,
so changing a parameter in source rewrites this section rather than silently
contradicting it.

## 2.1 Money-laundering graph

A laundering network is a directed, weighted graph
$G = (V, E)$ whose nodes $V$ are financial entities (collectors, shell
fronts, seafood/currency fronts, banks, legitimate exporters) and whose
directed edges $E$ carry a positive value flow. Dirty value is *placed* at
source nodes, moves through the graph, and *integrates* at sink nodes.

**Cycle detection.** Money-returning loops are the signature of layering.
We enumerate elementary cycles by depth-limited depth-first search, rotating
each discovered cycle to a canonical form (start at its lexicographically
smallest node) so duplicates collapse (`TransactionGraph.find_cycles`).

**Funnel analysis.** A node is a *collector* when it fans in from ≥ 2 unique
sources with a degree-imbalance ratio
$\rho = (\text{sources}+1)/(\text{targets}+1) \geq \tau$, and a
*distributor* when it fans out to ≥ 2 unique targets with $\rho \leq 1/\tau$
($\tau = {{LAUNDERING_FUNNEL_THRESHOLD}}$). Trivial linear pass-throughs are
excluded.

**Dirty-flow propagation.** Dirty mass is conservatively re-distributed
along edges in proportion to edge weight; a node with no out-edges retains
its mass (it is a sink). Iteration converges to the pooling dirty
distribution (`TransactionGraph.propagate_dirty`). From it we derive the
per-sink dirty fraction
$d_i = \text{dirty}_i / \text{in\_amount}_i$, the integration score
$1 - \bar{d}$ (how diluted the placed value has become), and the Shannon
entropy of the dirty distribution across sinks (how dispersed it is).

**Composite layering score.** Three normalised components — cycles,
layering-chain depth, and funnel imbalance — are blended
${{LAYERING_WEIGHT_CYCLE}}\cdot C_\text{cyc} +
{{LAYERING_WEIGHT_DEPTH}}\cdot C_\text{depth} +
{{LAYERING_WEIGHT_FUNNEL}}\cdot C_\text{funnel}$ into a single score in
$[0, 1]$ (`analyze_laundering`). The weights are declared as
`LAYERING_WEIGHTS` in source and injected here; they are heuristic, and
Section 7 says so.

## 2.2 Vessel forensics

For a declared `VesselProfile` of the Wavekrest-class mothership we compute,
from first principles:

- **Enclosed hull volume** $V = L \cdot B \cdot D \cdot C_b$.
- **Gross tonnage** (IMO 1969): $\mathrm{GT} = K_1 V$ with
  $K_1 = 0.2 + 0.02 \log_{10} V$.
- **Hydrostatic displacement** $\Delta = \rho_\text{sw} \cdot L \cdot B \cdot
  \text{draft} \cdot C_b$, $\rho_\text{sw} = {{VESSEL_SEAWATER_DENSITY}}\
  \text{t/m}^3$, $C_b = {{VESSEL_BLOCK_COEFFICIENT}}$.
- **Fuel endurance**: at speed $v$ the required shaft power follows the
  cubic law $P(v) = P_\text{max}(v/v_\text{max})^3$, burning
  $P(v) \cdot \text{SFC}$ kg/h (SFC = {{VESSEL_DIESEL_SFC}} kg/kWh), giving
  range $\text{nm} = (\text{fuel mass}/\text{burn rate}) \cdot v$.

The forensic scan (`anomaly_scan`) then flags physical implausibilities: a
cargo bulk-density above the fish ceiling
({{VESSEL_CARGO_DENSITY_CEILING}} t/m³), a declared displacement more than
{{VESSEL_DISPLACEMENT_TOLERANCE}} from the draft-predicted value (hidden
ballast), a route whose required average speed exceeds capability, a voyage
beyond the fuel endowment, or an over-powered hull. The scan deliberately
does *not* trap errors from the underlying physics: a profile that cannot
support an endurance computation raises rather than being scored as
anomaly-free, because "no anomaly" and "could not check" are different
findings and only one of them is safe to report.

## 2.3 Rogue-00 risk model

A revoked licence means the operator faces a finite-horizon control problem.
State is $(a, e)$: adversary *alert* and cumulative *exposure*. Each step the
operator picks an intensity $i \in \{\text{stealth}, \text{covert},
\text{overt}\}$ with gain $g_i$ and visibility $v_i$; alert rises
$a \leftarrow \min(a_\text{max}, a + v_i)$, exposure rises by one step, and
*blowback* (a retaliatory strike destroying the period's value) arrives with
logistic hazard
$p = \sigma(\beta_0 + \beta_a a + \beta_e e)$.

We solve exactly by backward induction over the discrete
$(\text{step}, a, e)$ lattice (`solve_optimal_policy`), producing the
expected optimal value, the first-period action, and the escalation curve
that follows. No randomness is involved — the result is reproducible to the
last float.

Both state dimensions are quantised: exposure onto {{ROGUE_EXPOSURE_CELLS}}
cells and alert onto the integers $0..{{ROGUE_ALERT_MAX}}$. The visibility
ladder is therefore truncated onto the alert lattice by a single shared
transition (`next_alert`), which the projection and valuation functions use
as well. That sharing is what makes the model self-checking: replaying the
DP's own optimal action sequence through `expected_value_of_policy` must
reproduce `optimal_value` exactly, and the test suite asserts it does. A
model whose optimiser and whose reported trajectory used different
transitions would pass every individual test and still describe a process
nobody optimised.

## 2.4 Narcotics-finance economics

The money behind the cartel is modelled in `narcotics_finance.py` in two
layers. First, the **supply chain**: a base production cost per kilogram is
multiplied through the distribution stages (export → wholesale → street) to
give the stage prices ({{FIN_STAGE_LADDER}}), and purity adjustment divides
the retail price by the purity fraction so unit economics are stated per
*pure* gram (`price_chain`, `purity_adjusted_price`). Second, the **cash
itself**: using the mass and volume of a US currency note
({{FIN_BILL_MASS_G}} g, {{FIN_BILL_VOLUME_CM3}} cm³ [@bep_currency]), we
convert a parcel's value into whole notes, kilograms of mass, and cubic
metres of volume (`cash_mass_kg`, `cash_volume_m3`), then check whether that
parcel physically fits the Wavekrest-class hold — volume *and* mass — and
how many trips it needs (`manifest_feasibility`, `trips_required`). Note
counts round up: a partial note cannot be carried, so the conservative
direction is the only defensible one for a feasibility check.

## 2.5 Operations logistics

The physical campaign is planned in `operations_logistics.py`. The
{{LOG_NETWORK_LEGS}} transport legs between the film's {{LOG_HUB_COUNT}}
hubs (Isthmus City, Bogota, Hong Kong, Florida) each carry a distance, a
dollar cost, and an interdiction risk. `shortest_path` runs Dijkstra's
algorithm [@dijkstra1959] over one of three additive weights; for risk the
per-leg weight is $-\ln(1-r)$ so the cumulative survival product becomes a
sum and the returned route minimizes the honest $1-\prod(1-r_i)$
cumulative-risk metric. The baseline that route is reported against is the
**direct leg** itself — the single {{LOG_ORIGIN}}→{{LOG_DESTINATION}} edge,
read straight out of the network by `direct_leg` — and not the
distance-minimal path, which on this network happens to be that same leg
and so cannot be told apart from it by inspection alone.
`gadget_knapsack` solves the 0/1 equipment-loadout
problem exactly by dynamic programming [@kellerer2004] over gram-scaled
weights, selecting from {{LOG_GADGET_CANDIDATES}} candidate gadgets under a
{{LOG_CAPACITY_KG}} kg budget; the per-item selection flag is recorded
during that item's own DP pass, because a final-array equality check
false-negatives once a later item has already absorbed the same capacity
cell. `trip_plan` projects the chosen route's legs against the vessel's
{{LOG_SPEED_KNOTS}} kn cruise, its {{LOG_ENDURANCE_NM}} nm endurance, and
{{LOG_REFUEL_HOURS}} h refuelling stops, counting stops and elapsed time.

## 2.6 Surveillance and watchlist

An unsanctioned operator's exposure to the adversary's surveillance
apparatus is modelled in `surveillance.py`. Each covert action has a
*signature* (detectability) and a *watch increment* (how much it teaches the
watchlist); the step-$t$ detection hazard is the logistic
$p_t = \sigma(\beta_0 + \beta_w w_t + \beta_s s_i)$ where $w_t$ is the
accumulated watchlist weight. A sequence survives only if every step goes
undetected, so its success probability is $\prod_t(1-p_t)$. The order that
maximises survival is found exactly by exhaustive permutation search for up
to {{SURV_EXACT_LIMIT}} actions (`exact_action_order`) and by a
value-per-exposure ratio rule (Smith's rule [@smith1956]) beyond that
(`heuristic_action_order`); `compromise_step` reports the first step at
which cumulative detection crosses the threshold {{SURV_THRESHOLD}}. The
canonical detection coefficients are $\beta_0 = {{SURV_BETA_0}}$,
$\beta_w = {{SURV_BETA_WATCH}}$, and $\beta_s = {{SURV_BETA_SIGNATURE}}$.

