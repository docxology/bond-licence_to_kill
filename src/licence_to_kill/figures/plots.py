"""Deterministic matplotlib figures for the ROGUE mission.

Figure generation is deliberately side-effect-explicit: each ``plot_*``
holds its own ``Axes`` lifecycle, uses the Agg backend (headless), and saves
to an ``outdir``. All node coordinates and colours are derived from the data
with no random layout, so a rerun reproduces byte-identical files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Headless backend must be selected before pyplot is imported.
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt  # noqa: E402  (backend set above)

from licence_to_kill.laundering_graph import (
    analyze_laundering,
    build_sanchez_network,
    canonical_laundering_params,
)
from licence_to_kill.operations_logistics import (
    OperationNetwork,
    canonical_logistics_params,
    direct_leg,
    shortest_path,
)
from licence_to_kill.rogue_ops import canonical_rogue_params, solve_optimal_policy
from licence_to_kill.vessel_forensics import canonical_vessel_params, forensic_report

__all__ = [
    "generate_figures",
    "plot_laundering_network",
    "plot_operations_logistics",
    "plot_rogue_escalation",
    "plot_vessel_forensic_scan",
]

#: Canonical inputs — the same single sources ``mission.py`` and
#: ``manuscript_variables.py`` consume, so a figure can never depict a
#: different scenario than the one the manuscript reports.
_LAUNDERING = canonical_laundering_params()
_VESSEL = canonical_vessel_params()
_SOURCES: tuple[str, ...] = _LAUNDERING["sources"]
_SINKS: tuple[str, ...] = _LAUNDERING["sinks"]
_SEED: int = int(_LAUNDERING["seed"])


def _layers() -> dict[str, int]:
    """Layer index by node-prefix for a deterministic left→right layout."""
    return {
        "S": 0,  # street collectors (placement)
        "F": 1,  # shell fronts (layering)
        "W": 2,  # seafood fronts
        "C": 2,  # currency exchanges
        "L": 3,  # legitimate exporters (mixer)
        "B": 3,  # banks (integration)
    }


def plot_laundering_network(outdir: Path) -> Path:
    """Render the Sanchez flow graph coloured by dirty fraction at each node."""
    graph = build_sanchez_network(seed=_SEED)
    analyze_laundering(
        graph,
        _SOURCES,
        _SINKS,
        max_depth=int(_LAUNDERING["max_depth"]),
        max_cycles=int(_LAUNDERING["max_cycles"]),
        max_paths=int(_LAUNDERING["max_paths"]),
        funnel_threshold=float(_LAUNDERING["funnel_threshold"]),
    )
    injections = {s: float(graph.out_amount(s)) for s in _SOURCES}
    dirty = graph.propagate_dirty(injections)
    total = max(sum(dirty.values()), 1e-9)

    layers = _layers()
    node_pos: dict[str, tuple[float, float]] = {}
    columns: dict[int, int] = {}
    for node in graph.nodes():
        col = columns.get(layers[node[:1]], 0)
        pos_x = float(layers[node[:1]])
        pos_y = float(col) - (len([n for n in graph.nodes() if layers[n[:1]] == layers[node[:1]]]) / 2.0)
        node_pos[node] = (pos_x, pos_y)
        columns[layers[node[:1]]] = col + 1

    fig, ax = plt.subplots(figsize=(9, 6))
    for edge in graph.edges():
        x0, y0 = node_pos[edge.source]
        x1, y1 = node_pos[edge.target]
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="->", color="#8a8a8a", lw=0.6, shrinkA=4, shrinkB=4),
        )
    for node in graph.nodes():
        x, y = node_pos[node]
        frac = dirty.get(node, 0.0) / total
        colour = plt.get_cmap("RdYlGn")(1.0 - min(frac * 8.0, 1.0))  # red = dirty
        ax.scatter(x, y, s=340, color=colour, edgecolors="black", linewidths=0.6, zorder=3)
        ax.text(x, y, node, ha="center", va="center", fontsize=7, zorder=4)
    ax.set_title("Sanchez money-laundering graph — node colour = dirty-flow share (ROGUE)")
    ax.set_xlim(-0.5, 3.5)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(
        ["placement\n(cash)", "layering\n(shells)", "fronts\n(seafood/currency)", "integration\n(banks/legit)"]
    )
    ax.set_yticks([])
    ax.set_xlabel("laundering stage")
    ax.set_ylabel("")
    fig.tight_layout()
    path = outdir / "laundering_network.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_rogue_escalation(outdir: Path) -> Path:
    """Render the optimal rogue-00 policy: alert, exposure and blowback hazard v step."""
    report = solve_optimal_policy(canonical_rogue_params()["model"])
    steps = []
    for entry in report.escalation:
        steps.append(
            {
                "step": int(entry["step"]),
                "alert": float(entry["alert"]),
                "alert_after": float(entry["alert_after"]),
                "exposure": float(entry["exposure"]),
                "blowback": float(entry["blowback"]),
            }
        )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    x = [s["step"] for s in steps]
    # Both alert series: the level each step is entered with (what its hazard
    # is priced on) and the level its own action leaves behind. Plotting only
    # the former draws a flat zero line for the canonical optimal policy and
    # hides the terminal overt escalation entirely.
    axes[0].plot(x, [s["alert"] for s in steps], marker="o", color="#c0392b", label="alert entering step")
    axes[0].plot(
        x,
        [s["alert_after"] for s in steps],
        marker="x",
        ls="--",
        color="#e74c3c",
        label="alert after action",
    )
    axes[0].plot(x, [s["exposure"] for s in steps], marker="s", color="#8e44ad", label="cumulative exposure")
    axes[0].set_title("ROGUE escalation under the optimal policy")
    axes[0].set_xlabel("mission step")
    axes[0].set_ylabel("level / exposure")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(x, [s["blowback"] for s in steps], marker="^", color="#e67e22")
    axes[1].axhline(report.peak_blowback, color="#7f8c8d", ls="--", lw=0.9)
    axes[1].set_title("blowback hazard: P(retaliation)")
    axes[1].set_xlabel("mission step")
    axes[1].set_ylabel("P(blowback)")
    axes[1].set_ylim(0.0, 1.02)
    axes[1].grid(alpha=0.3)

    fig.suptitle(
        f"Rogue-00 optimal policy — expected value {report.optimal_value:.3f}, "
        f"first action {report.first_action} (Licence to Kill)"
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = outdir / "rogue_escalation.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


#: Canonical vessel figure so the mission's third domain is visualised too.
def plot_vessel_forensic_scan(outdir: Path) -> Path:
    """Render the Wavekrest-class forensic profile and its flagged anomalies."""
    vessel = forensic_report(_VESSEL["profile"], observed=_VESSEL["observed"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["hull volume", "gross tonnage", "fuel (t)", "displacement"]
    values = [
        vessel.hull_volume,
        vessel.gross_tonnage,
        vessel.fuel_mass_tonnes,
        vessel.predicted_displacement,
    ]
    ax.bar(labels, values, color=["#2c3e50", "#16a085", "#2980b9", "#c0392b"])
    ax.set_title(
        f"Wavekrest-class forensic profile — {len(vessel.anomalies)} anomaly(s), "
        f"score {vessel.anomaly_score:.1f} (ROGUE)"
    )
    ax.set_ylabel("magnitude")
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    path = outdir / "vessel_forensics.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_operations_logistics(outdir: Path, params: dict[str, Any] | None = None) -> Path:
    """Render the operations network with the risk-optimal route highlighted.

    ``params`` defaults to :func:`canonical_logistics_params`; it is
    injectable so the unreachable-destination guard below is reachable from a
    test rather than being a branch that can never fire.
    """
    params = canonical_logistics_params() if params is None else params
    network = OperationNetwork(params["legs"])
    optimal = shortest_path(network, str(params["origin"]), str(params["destination"]), weight="risk")
    # The baseline is the *direct leg*, not the distance-minimal path. They
    # coincide on the canonical network, which is precisely why computing the
    # latter and calling it the former went unnoticed; see
    # ``operations_logistics.direct_leg``.
    direct = direct_leg(network, str(params["origin"]), str(params["destination"]))
    # Explicit raise rather than `assert`: assertions are stripped under -O,
    # which would turn an unreachable destination into an AttributeError deep
    # inside the plotting code instead of a named failure here.
    if optimal is None or direct is None:
        raise ValueError(f"{params['destination']!r} is unreachable from {params['origin']!r} in the canonical network")

    # Deterministic hub layout (left → right by operational stage).
    positions = {"IC": (0.0, 0.0), "BOG": (0.8, -1.2), "HK": (2.2, 0.6), "FL": (3.4, 0.0)}
    optimal_edges = {(leg.origin, leg.destination) for leg in optimal.legs}
    direct_edges = {(direct.origin, direct.destination)}

    fig, ax = plt.subplots(figsize=(9, 5.4))
    for leg in network.legs():
        x0, y0 = positions[leg.origin]
        x1, y1 = positions[leg.destination]
        on_optimal = (leg.origin, leg.destination) in optimal_edges
        on_direct = (leg.origin, leg.destination) in direct_edges
        colour = "#c0392b" if on_optimal else ("#f5b041" if on_direct else "#95a5a6")
        weight = 2.4 if on_optimal else 1.2
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="-|>", color=colour, lw=weight, shrinkA=6, shrinkB=6),
        )
        midx, midy = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(
            midx + 0.06,
            midy + 0.12,
            f"${leg.cost / 1000:.0f}k, r={leg.risk:.2f}",
            fontsize=7,
            color="#34495e",
        )
    for node, (x, y) in positions.items():
        ax.scatter(x, y, s=520, color="#2c3e50", edgecolors="white", linewidths=1.4, zorder=3)
        ax.text(x, y, node, ha="center", va="center", color="white", fontsize=10, fontweight="bold", zorder=4)
    ax.set_title(
        f"ROGUE operations network — risk-optimal route {' → '.join(optimal.path)} "
        f"(cum. risk {optimal.cumulative_risk:.3f} vs direct leg {direct.risk:.3f})"
    )
    ax.set_xlim(-0.6, 4.0)
    ax.set_ylim(-2.0, 1.6)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("operational progression (Isthmus City → Florida)")
    fig.tight_layout()
    path = outdir / "operations_logistics.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def generate_figures(outdir: Path) -> dict[str, Path]:
    """Generate every ROGUE figure; return ``name → path`` in stable order."""
    outdir = Path(outdir)
    return {
        "laundering_network": plot_laundering_network(outdir),
        "rogue_escalation": plot_rogue_escalation(outdir),
        "vessel_forensic_scan": plot_vessel_forensic_scan(outdir),
        "operations_logistics": plot_operations_logistics(outdir),
    }
