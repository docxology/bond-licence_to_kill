# Methodology

This section specifies the three deterministic algorithms that constitute
the ROGUE analytical core. Deep familiarity with each module's source is the
intended reader path: `src/licence_to_kill/laundering_graph.py`,
`src/licence_to_kill/vessel_forensics.py`, and
`src/licence_to_kill/rogue_ops.py`.

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
($\tau = 1.5$). Trivial linear pass-throughs are excluded.

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
$0.4\cdot C_\text{cyc} + 0.3\cdot C_\text{depth} + 0.3\cdot C_\text{funnel}$
into a single score in $[0, 1]$ (`analyze_laundering`).

## 2.2 Vessel forensics

For a declared `VesselProfile` of the Wavekrest-class mothership we compute,
from first principles:

- **Enclosed hull volume** $V = L \cdot B \cdot D \cdot C_b$.
- **Gross tonnage** (IMO 1969): $\mathrm{GT} = K_1 V$ with
  $K_1 = 0.2 + 0.02 \log_{10} V$.
- **Hydrostatic displacement** $\Delta = \rho_\text{sw} \cdot L \cdot B \cdot
  \text{draft} \cdot C_b$, $\rho_\text{sw} = 1.025\ \text{t/m}^3$.
- **Fuel endurance**: at speed $v$ the required shaft power follows the
  cubic law $P(v) = P_\text{max}(v/v_\text{max})^3$, burning
  $P(v) \cdot \text{SFC}$ kg/h (SFC ≈ 0.195 kg/kWh), giving range
  $\text{nm} = (\text{fuel mass}/\text{burn rate}) \cdot v$.

The forensic scan (`anomaly_scan`) then flags physical implausibilities: a
cargo bulk-density above the fish ceiling (~1.4 t/m³), a declared
displacement more than 15 % from the draft-predicted value (hidden ballast),
a route whose required average speed exceeds capability, a voyage beyond the
fuel endowment, or an over-powered hull.

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

## 2.4 Narcotics-finance economics

The money behind the cartel is modelled in `narcotics_finance.py` in two
layers. First, the **supply chain**: a base production cost per kilogram is
multiplied through the distribution stages (export → wholesale → street) to
give the stage prices, and purity adjustment divides the retail price by the
purity fraction so unit economics are stated per *pure* gram
(`price_chain`, `purity_adjusted_price`). Second, the **cash itself**: using
the size and mass of a US currency note (≈ 1.0 g, ≈ 1.13 cm³), we convert a
parcel's value into whole notes, kilograms of mass, and cubic metres of
volume (`cash_mass_kg`, `cash_volume_m3`), then check whether that parcel
physically fits the Wavekrest-class hold — volume *and* mass — and how many
trips it needs (`manifest_feasibility`, `trips_required`).

## 2.5 Operations logistics

The physical campaign is planned in `operations_logistics.py`. Transport
legs between the film's hubs (Isthmus City, Bogota, Hong Kong, Florida)
carry a distance, a dollar cost, and an interdiction risk. `shortest_path`
runs Dijkstra's algorithm [@dijkstra1959] over one of three additive
weights; for risk the per-leg weight is $-\ln(1-r)$ so the cumulative
survival product becomes a sum and the returned route minimizes the honest
$1-\prod(1-r_i)$ cumulative-risk metric. `gadget_knapsack` solves the 0/1
equipment-loadout problem exactly by dynamic programming [@kellerer2004]
over gram-scaled weights. `trip_plan` projects the chosen route's legs
against the vessel's speed and fuel endurance, counting refuel stops and
elapsed time.

## 2.6 Surveillance and watchlist

An unsanctioned operator's exposure to the adversary's surveillance
apparatus is modelled in `surveillance.py`. Each covert action has a
*signature* (detectability) and a *watch increment* (how much it teaches the
watchlist); the step-$t$ detection hazard is the logistic
$p_t = \sigma(\beta_0 + \beta_w w_t + \beta_s s_i)$ where $w_t$ is the
accumulated watchlist weight. A sequence survives only if every step goes
undetected, so its success probability is $\prod_t(1-p_t)$. The order that
maximises survival is found exactly by exhaustive permutation search for up
to 8 actions (`exact_action_order`) and by a value-per-exposure ratio rule
(Smith's rule [@smith1956]) beyond that (`heuristic_action_order`);
`compromise_step` reports the first step at which cumulative detection
crosses a threshold.

