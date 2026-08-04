"""licence_to_kill — Licence to Kill (1989) · mission codename ROGUE.

Pure deterministic domain core for the ROGUE mission.

Modules
-------
- :mod:`laundering_graph`  — Sanchez drug-cartel money-laundering graph
  (placement → layering → integration detection).
- :mod:`vessel_forensics`  — Wavekrest-class mothership forensic anomaly
  detection from first-principles marine physics.
- :mod:`rogue_ops`         — revoked-licence (rogue-00) operation risk model:
  escalation dynamics and blowback via finite-horizon dynamic programming.

These modules are deliberately bond-api-free and infrastructure-free: they
import only the standard library and numpy, so the domain core remains
importable even if the ``bond-api`` path dependency ever fails. The thin
protocol adapter (:mod:`licence_to_kill.mission`) is the only module that
imports ``bond_api``.
"""

from __future__ import annotations

__version__ = "0.1.0"

#: Film identity (matches the BOND roster slug).
FILM = "licence_to_kill"

#: Mission codename.
CODENAME = "ROGUE"

__all__ = ["__version__", "FILM", "CODENAME"]
