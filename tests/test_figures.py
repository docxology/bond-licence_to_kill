"""Figure generation tests: presence, PNG format, and byte determinism.

Two independent renders into different temp dirs must be byte-identical —
the canonical proof that figure generation is deterministic.
"""

from __future__ import annotations

import pytest

from licence_to_kill.figures.plots import (
    generate_figures,
    plot_laundering_network,
    plot_operations_logistics,
    plot_rogue_escalation,
    plot_vessel_forensic_scan,
)
from licence_to_kill.operations_logistics import (
    MissionLeg,
    OperationNetwork,
    canonical_logistics_params,
    shortest_path,
)


def test_generate_figures_produces_all(tmp_path):
    figures = generate_figures(tmp_path / "figures")
    assert set(figures) == {
        "laundering_network",
        "rogue_escalation",
        "vessel_forensic_scan",
        "operations_logistics",
    }
    for path in figures.values():
        assert path.exists()
        assert path.suffix == ".png"
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_figures_are_byte_deterministic(tmp_path):
    first = generate_figures(tmp_path / "a")
    second = generate_figures(tmp_path / "b")
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()


def test_individual_plotters_return_paths(tmp_path):
    assert plot_laundering_network(tmp_path).exists()
    assert plot_rogue_escalation(tmp_path).exists()
    assert plot_vessel_forensic_scan(tmp_path).exists()
    assert plot_operations_logistics(tmp_path).exists()


def test_operations_figure_rejects_unreachable_destination(tmp_path):
    """The unreachable-destination guard must actually be able to fire.

    A guard that no input can trigger is indistinguishable from no guard at
    all, so the plotter takes an injectable ``params`` and this exercises the
    failure branch on a network whose destination has no inbound leg.
    """
    params = dict(canonical_logistics_params())
    # FL is a known node (it is the HK leg's destination) but no path leads
    # to it from IC — so shortest_path returns None rather than raising for
    # an unknown node, which is the branch under test.
    params["legs"] = (
        MissionLeg("IC", "BOG", 900.0, 8_000.0, 0.04),
        MissionLeg("HK", "FL", 8700.0, 150_000.0, 0.12),
    )
    with pytest.raises(ValueError, match="unreachable"):
        plot_operations_logistics(tmp_path, params=params)


def test_operations_figure_requires_a_real_direct_leg(tmp_path):
    """The figure's baseline must be the direct leg, not a distance-minimal path.

    Behavioural discriminator, not a comment: this network has a perfectly
    good IC→HK→FL path but **no** direct IC→FL leg. Computing the baseline as
    ``shortest_path(..., weight="distance")`` — what the plotter used to do —
    finds the two-hop route, labels it "direct", and renders happily. Reading
    the direct leg finds nothing and refuses. Reverting the plotter turns this
    test red.
    """
    params = dict(canonical_logistics_params())
    params["legs"] = (
        MissionLeg("IC", "HK", 8300.0, 120_000.0, 0.10),
        MissionLeg("HK", "FL", 8700.0, 150_000.0, 0.12),
    )
    assert shortest_path(OperationNetwork(params["legs"]), "IC", "FL", weight="distance") is not None
    with pytest.raises(ValueError, match="unreachable"):
        plot_operations_logistics(tmp_path, params=params)


def test_operations_figure_accepts_injected_params_equivalently(tmp_path):
    """Passing the canonical params explicitly renders the same bytes."""
    default = plot_operations_logistics(tmp_path / "default")
    injected = plot_operations_logistics(tmp_path / "injected", params=canonical_logistics_params())
    assert default.read_bytes() == injected.read_bytes()
