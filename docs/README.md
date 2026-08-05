# docs/ — documentation hub for licence_to_kill (ROGUE)

Everything an agent or a new reader needs in order to change this package
without breaking the fleet or the manuscript. Three documents, each with a
distinct job.

| File | Read it when | Answers |
|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | **First, always** — before editing anything | The ten binding rules: what is frozen, what may never be mocked, what must never be hand-authored, and the verification checklist |
| [`architecture.md`](architecture.md) | You need to find something, or change how pieces fit | Layer topology; every `src/` module and what it computes; how `mission.py` implements the frozen `bond_api` `MissionProvider`; the one-declaration-per-scenario rule; how to add a concept |
| [`testing_philosophy.md`](testing_philosophy.md) | You are writing or reviewing a test | Why zero mocks; how determinism is proved rather than asserted; what each suite covers; the four manuscript gates; why guards must be able to fail |
| [`AGENTS.md`](AGENTS.md) | You want the short version | A one-screen index of the hard constraints and the verify commands |

## The short version

`licence_to_kill` models six domains from *Licence to Kill* (1989) — the
Sanchez laundering graph, Wavekrest-class vessel forensics, the revoked-
licence policy DP, narcotics-finance cash physics, operations logistics, and
surveillance/watchlist scheduling — behind one frozen mission protocol.

Three properties are load-bearing, and each has a mechanism rather than a
convention behind it:

- **The protocol surface is frozen.** Other packages import
  `MissionProvider`, `GADGET_REGISTRY`, and `run_rogue_mission` by name.
- **The domain core is pure.** Six modules, stdlib + numpy only, no
  `bond_api` — structurally verified by a test that reads their source.
- **No number is hand-written.** Results *and* parameters reach the
  manuscript only as generated tokens, held there by four live gates.

## Related documents outside this directory

- [`../README.md`](../README.md) — what the package is, install and run
  commands, the module map.
- [`../AGENTS.md`](../AGENTS.md) — build/test/verify quick reference.
- [`../TODO.md`](../TODO.md) — remaining work, and the dated verification
  record (the measured coverage and test count live there, not in prose
  here, so they can be checked against a command rather than trusted).
- [`../manuscript/`](../manuscript/) — the token-driven ROGUE manuscript;
  `SYNTAX.md` there covers the markup conventions.
