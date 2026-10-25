"""ROGUE mission preflight — verify the package is gate-ready.

Checks (in order): bond-api protocol surface loads, a MissionProvider can be
constructed and satisfies the protocol, the film registers its expected
gadgets, and the pure domain core imports standalone. Prints each check and
exits 0 only when every check passes (argparse-style: failures exit 1).
"""

from __future__ import annotations

import sys

from _bootstrap import PROVIDER
from bond_api.protocol import MissionProvider as ProtocolType, protocol_surface

#: The frozen registry entries the film must still register (subset check, so
#: adding a gadget stays legal — same additive-only rule as
#: ``tests/test_mission.py::_FROZEN_GADGET_NAMES``).
_EXPECTED_GADGETS = {
    "laundering_analyzer",
    "laundering_network",
    "vessel_forensics",
    "rogue_risk_model",
    "narcotics_finance",
    "operations_router",
    "surveillance_model",
    "network_manifest",
}


def main() -> int:
    issues: list[str] = []
    checks: list[str] = []

    try:
        surface = protocol_surface()
        checks.append(
            f"ok  bond-api protocol_surface: identity={surface['identity']} dataclasses={len(surface['dataclasses'])}"
        )
    except Exception as exc:  # pragma: no cover - defensive
        issues.append(f"fail bond-api protocol_surface: {exc}")

    if isinstance(PROVIDER, ProtocolType):
        checks.append(f"ok  provider satisfies MissionProvider protocol (film={PROVIDER.film})")
    else:
        issues.append("fail provider does not satisfy the MissionProvider protocol")

    brief = PROVIDER.brief()
    checks.append(f"ok  brief: codename={brief.codename} objectives={len(brief.objectives)}")

    from licence_to_kill.mission import GADGET_REGISTRY

    registered = set(GADGET_REGISTRY.gadgets_for("licence_to_kill"))
    missing = _EXPECTED_GADGETS - registered
    if missing:
        issues.append(f"fail missing gadgets: {sorted(missing)}")
    else:
        checks.append(f"ok  gadgets registered: {len(registered)}")

    # Pure domain core is importable even without bond-api wired in.
    from licence_to_kill.laundering_graph import build_sanchez_network  # noqa: F401
    from licence_to_kill.vessel_forensics import WAVEKREST_CLASS  # noqa: F401
    from licence_to_kill.rogue_ops import build_rogue_model  # noqa: F401

    checks.append("ok  pure domain core imports standalone")

    for line in checks:
        print(line)
    if issues:
        for line in issues:
            print(line, file=sys.stderr)
        return 1
    print("ROGUE preflight: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
