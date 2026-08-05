# Introduction

## The ROGUE mission

In *Licence to Kill* (1989) an operator pursues the drug lord Franz Sanchez
after his 00 licence is revoked, assembling an unsanctioned campaign that
moves from the street level of the cartel's cash economy, through the
Wavekrest-class mothership used to smuggle the proceeds, to a final
confrontation. This package formalises that campaign as a research problem:
a *special-agent mission* whose analytical core quietly mirrors the six
things a field analyst must actually determine. The first three concern what
the adversary is doing.

1. **Where is the money going?** The cartel's value is laundered in the
   textbook three stages — *placement* of cash, *layering* through a web of
   intermediaries, and *integration* into legitimate banks. We model this as
   a directed financial-flow graph and build deterministic detectors that
 score how heavily the structure is being layered and how dilute the dirty
 value has become (Section 2, `src/licence_to_kill/laundering_graph.py`).
2. **Is the mothership lying about what it carries?** A fishing vessel
   cannot silently move contraband without its own physics giving it away
   — a hold full of something denser than fish, a draft that disagrees with
   the declared displacement, a fuel budget that cannot cover its route. We
   compute those quantities from first principles
   (`src/licence_to_kill/vessel_forensics.py`).
3. **What should the operation do next?** With a revoked licence the
   operator has no sanctioned exit; every action escalates the adversary's
   alert level and precipitates blowback. We solve the optimal engagement
   policy exactly with dynamic programming
   (`src/licence_to_kill/rogue_ops.py`).

The remaining three concern what the operation itself can physically afford.

4. **How much money is actually moving, and can it move?** The film opens on
   an intercepted courier carrying a cash parcel. A supply-chain price and
   purity ladder says what that value represents in product; US-currency note
   physics say what it weighs and how much hold it occupies, and therefore
   whether one hull can carry it at all
   (`src/licence_to_kill/narcotics_finance.py`).
5. **By what route, carrying what?** Legs between the operational hubs trade
   distance, dollar cost, and interdiction risk against each other, and a
   weight-bounded gadget loadout has to be chosen before departure. Both are
   classical optimisation problems solved exactly — shortest path over a
   risk-additive weight, and 0/1 knapsack
   (`src/licence_to_kill/operations_logistics.py`).
6. **How long before the operator is burned?** Every covert action teaches
   the adversary's watchlist something. Survival to the end of the campaign
   is a product of per-step non-detection probabilities, and the only free
   variable is the order in which the actions are taken
   (`src/licence_to_kill/surveillance.py`).

The six are deliberately coupled at the scenario level rather than in code:
the Wavekrest-class hold sized in Section 2.2 is the same hold the cash
manifest must fit in Section 2.4 and the same hull whose endurance bounds
the voyage in Section 2.5, because all three read the one canonical
parameter set.

## Design principles

The package follows the BOND guardrails exactly. The six domain modules are
*pure* — infrastructure-free and bond-api-free, importable in any Python 3.10+
environment (verified by `tests/test_mission.py`). The `MissionProvider`
adapter in `src/licence_to_kill/mission.py` is the only module that touches
the frozen `bond-api` protocol, and it simply wires the domain results into
the five-stage mission lifecycle (brief → recon → plan → execute → debrief).
Everything is deterministic: the network is built from a seeded generator,
the forensic physics are closed-form, the dynamic program is exact backward
induction with no Monte Carlo, the routing and knapsack solvers are exact,
and the survival-optimal action order is found by exhaustive permutation
search at this problem size.

Each domain also exposes a `canonical_*_params()` function that is the sole
declaration of its scenario. The mission adapter, the manuscript token
generator, and the figure generators all read those functions rather than
carrying their own copies, so a figure cannot depict a scenario the prose
does not describe.

This manuscript is produced from `manuscript/config.yaml` and
`src/licence_to_kill/manuscript_variables.py`: every numeric value in the
prose is injected as a generated token and never hand-authored.
