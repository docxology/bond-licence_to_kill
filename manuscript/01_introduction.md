# Introduction

## The ROGUE mission

In *Licence to Kill* (1989) an operator pursues the drug lord Franz Sanchez
after his 00 licence is revoked, assembling an unsanctioned campaign that
moves from the street level of the cartel's cash economy, through the
Wavekrest-class mothership used to smuggle the proceeds, to a final
confrontation. This package formalises that campaign as a research problem:
a *special-agent mission* whose analytical core quietly mirrors the three
things a field analyst must actually determine.

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

## Design principles

The package follows the BOND guardrails exactly. The three domain modules are
*pure* — infrastructure-free and bond-api-free, importable in any Python 3.10+
environment (verified by `tests/test_mission.py`). The `MissionProvider`
adapter in `src/licence_to_kill/mission.py` is the only module that touches
the frozen `bond-api` protocol, and it simply wires the domain results into
the five-stage mission lifecycle (brief → recon → plan → execute → debrief).
Everything is deterministic: the network is built from a seeded generator,
the forensic physics are closed-form, and the dynamic program is exact
backward induction with no Monte Carlo.

This manuscript is produced from `manuscript/config.yaml` and
`src/licence_to_kill/manuscript_variables.py`: every numeric value in the
prose is injected as a generated token and never hand-authored.
