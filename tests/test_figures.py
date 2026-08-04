"""Figure generation tests: presence, PNG format, and byte determinism.

Two independent renders into different temp dirs must be byte-identical —
the canonical proof that figure generation is deterministic.
"""

from __future__ import annotations

from licence_to_kill.figures.plots import (
    generate_figures,
    plot_laundering_network,
    plot_rogue_escalation,
    plot_vessel_forensic_scan,
)


def test_generate_figures_produces_all(tmp_path):
    figures = generate_figures(tmp_path / "figures")
    assert set(figures) == {
        "laundering_network",
        "rogue_escalation",
        "vessel_forensic_scan",
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
