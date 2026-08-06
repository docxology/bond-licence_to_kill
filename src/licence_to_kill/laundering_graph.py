"""Sanchez drug-cartel money-laundering graph — layering and integration detection.

The ROGUE mission's first domain: model the flow of cartel cash through the
layered network that *Licence to Kill*'s Franz Sanchez uses (placement through
street collectors → shell fronts → seafood/currency fronts → integration into
banks), and compute deterministic indicators of how much dirty value is being
obscured (layering) and diluted into legitimate flows (integration).

All algorithms are pure and deterministic (no RNG in the detectors); any
randomness lives only inside the generative :func:`build_sanchez_network`
factory, which is seeded and therefore reproducible.

Real algorithms implemented
---------------------------
- elementary-cycle detection by depth-limited DFS (Tarjan's depth-first
  framing) for money-returning layering loops;
- funnel / concentration analysis (many-in-to-few-out collectors and their
  reverse distributors) from per-node degree and volume imbalance;
- finite-path enumeration between dirty sources and integration sinks;
- conservative linear dirty-flow propagation (Markov re-distribution with
  sinks) → per-node dirty fraction, integration score, mixing entropy.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

__all__ = [
    "Edge",
    "LaunderingGraphError",
    "LaunderingReport",
    "Transaction",
    "TransactionGraph",
    "DEFAULT_FUNNEL_THRESHOLD",
    "LAYERING_WEIGHTS",
    "analyze_laundering",
    "build_sanchez_network",
    "canonical_laundering_params",
]

#: Default funnel degree-imbalance threshold (collector >= tau, distributor <= 1/tau).
DEFAULT_FUNNEL_THRESHOLD = 1.5

#: Composite layering-score blend weights: (cycle, depth, funnel). Heuristic
#: weights, not estimates — see the manuscript's Limitations section. Named
#: here so the manuscript can cite them as tokens instead of hand-authoring
#: three numbers that would drift the moment the blend is retuned.
LAYERING_WEIGHTS: tuple[float, float, float] = (0.4, 0.3, 0.3)

#: Default cap on source→sink path enumeration. Must sit strictly above the
#: canonical network's true path count so the reported `LAUNDERING_PATHS`
#: figure is the exact chain count, not a saturated cap. Raised from 200
#: (which the canonical network saturated) to 1000 as the C2 fix; if the
#: canonical graph is ever extended and its path count rises to this bound,
#: `tests/test_canonical_params.py` (which asserts the enumeration is
#: non-saturating) fails and forces a re-derivation.
DEFAULT_MAX_PATHS = 1000

#: Sink / integration sectors (terminal accounts where dirty value pools).
INTEGRATION_SECTORS = ("bank",)


class LaunderingGraphError(ValueError):
    """Raised for an invalid laundering-network input (bad transaction, etc.)."""


@dataclass(frozen=True)
class Transaction:
    """A single value transfer between two named entities."""

    source: str
    target: str
    amount: float
    sector: str = "generic"


@dataclass(frozen=True)
class Edge:
    """A stored directed edge: source, target, amount, sector."""

    source: str
    target: str
    amount: float
    sector: str


def _canonical_cycle(path: Sequence[str]) -> tuple[str, ...]:
    """Rotate a cycle so it starts at its lexicographically smallest node."""
    nodes = list(path)
    pivot = min(range(len(nodes)), key=lambda i: nodes[i])
    return tuple(nodes[pivot:] + nodes[:pivot])


class TransactionGraph:
    """A directed, weighted financial-flow graph.

    Nodes are entities (accounts, fronts, vessels, banks); a directed edge
    carries a positive ``amount`` of value from ``source`` to ``target``.
    Insertion order and sorted node iteration keep every structural output
    deterministic.
    """

    def __init__(self, transactions: Iterable[Transaction] = ()) -> None:
        self._edges: list[Edge] = []
        self._out: dict[str, list[Edge]] = {}
        self._in_: dict[str, list[Edge]] = {}
        for txn in transactions:
            self.add_transaction(txn)

    @classmethod
    def from_transactions(cls, transactions: Iterable[Transaction]) -> "TransactionGraph":
        return cls(transactions)

    def add_transaction(self, txn: Transaction) -> None:
        """Validate and append a transaction."""
        if not isinstance(txn, Transaction):
            raise LaunderingGraphError("expected a Transaction")
        if not (isinstance(txn.source, str) and txn.source.strip()):
            raise LaunderingGraphError("Transaction.source must be a non-empty string")
        if not (isinstance(txn.target, str) and txn.target.strip()):
            raise LaunderingGraphError("Transaction.target must be a non-empty string")
        if txn.source == txn.target:
            raise LaunderingGraphError("self-loop transactions are not laundering structure")
        if not (isinstance(txn.amount, (int, float)) and txn.amount > 0):
            raise LaunderingGraphError("Transaction.amount must be a positive number")
        for name in (txn.source, txn.target):
            self._out.setdefault(name, [])
            self._in_.setdefault(name, [])
        edge = Edge(txn.source, txn.target, float(txn.amount), txn.sector)
        self._edges.append(edge)
        self._out[txn.source].append(edge)
        self._in_[txn.target].append(edge)

    # -- accessors -------------------------------------------------------
    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._out))

    def edges(self) -> tuple[Edge, ...]:
        return tuple(self._edges)

    def has_node(self, node: str) -> bool:
        return node in self._out

    def out_edges(self, node: str) -> tuple[Edge, ...]:
        return tuple(self._out.get(node, ()))

    def in_edges(self, node: str) -> tuple[Edge, ...]:
        return tuple(self._in_.get(node, ()))

    def out_amount(self, node: str) -> float:
        return sum(edge.amount for edge in self._out.get(node, ()))

    def in_amount(self, node: str) -> float:
        return sum(edge.amount for edge in self._in_.get(node, ()))

    def __len__(self) -> int:
        return len(self._edges)

    # -- layering detectors ----------------------------------------------
    def find_cycles(self, max_depth: int = 8, max_cycles: int = 50) -> tuple[tuple[str, ...], ...]:
        """Elementary cycles via depth-limited DFS, canonically deduplicated."""
        if max_depth < 3:
            raise LaunderingGraphError("max_depth must be >= 3 to detect a cycle")
        found: set[tuple[str, ...]] = set()
        for start in self.nodes():
            stack: list[tuple[str, list[str]]] = [(start, [start])]
            while stack:
                node, path = stack.pop()
                for edge in self.out_edges(node):
                    if edge.target == start and len(path) >= 3:
                        found.add(_canonical_cycle(path))
                        if len(found) >= max_cycles:
                            return tuple(sorted(found))
                    if edge.target not in path and len(path) < max_depth:
                        stack.append((edge.target, path + [edge.target]))
        return tuple(sorted(found))

    def concentration(self, node: str) -> dict[str, float | str | int]:
        """Per-node degree and volume imbalance used for funnel detection."""
        in_edges = self.in_edges(node)
        out_edges = self.out_edges(node)
        unique_sources = len({e.source for e in in_edges})
        unique_targets = len({e.target for e in out_edges})
        in_vol = sum(e.amount for e in in_edges)
        out_vol = sum(e.amount for e in out_edges)
        funnel_ratio = (unique_sources + 1.0) / (unique_targets + 1.0)
        return {
            "node": node,
            "in_degree": len(in_edges),
            "unique_sources": unique_sources,
            "out_degree": len(out_edges),
            "unique_targets": unique_targets,
            "in_amount": in_vol,
            "out_amount": out_vol,
            "funnel_ratio": funnel_ratio,
        }

    def funnels(self, threshold: float = DEFAULT_FUNNEL_THRESHOLD) -> tuple[dict[str, float | str | int], ...]:
        """Flow nodes that genuinely concentrate (fan-in, ratio >= threshold) or
        distribute (fan-out, ratio <= 1/threshold).

        A node must show real fan-in or fan-out (>= 2 unique counterparts on
        the dense side) — a trivial linear pass-through is not a funnel.

        There is deliberately no isolated-node guard: a node only enters the
        graph via :meth:`add_transaction`, so every node has at least one
        incident edge, and a hypothetical isolated node would fail both the
        collector and the distributor test anyway (both require >= 2 unique
        counterparts). A guard here would be unreachable and could never
        change an outcome.
        """
        results = []
        for node in self.nodes():
            info = self.concentration(node)
            unique_sources = int(info["unique_sources"])
            unique_targets = int(info["unique_targets"])
            ratio = float(info["funnel_ratio"])
            is_collector = unique_sources >= 2 and ratio >= threshold
            is_distributor = unique_targets >= 2 and ratio <= 1.0 / threshold
            if is_collector or is_distributor:
                results.append(info)
        return tuple(results)

    def layering_paths(
        self,
        sources: Iterable[str],
        sinks: Iterable[str],
        max_depth: int = 8,
        max_paths: int = DEFAULT_MAX_PATHS,
    ) -> tuple[tuple[str, ...], ...]:
        """Enumerate finite source→sink value paths (the layering chains)."""
        source_set = set(sources)
        sink_set = set(sinks)
        found: list[tuple[str, ...]] = []
        for start in sorted(source_set):
            stack: list[list[str]] = [[start]]
            while stack and len(found) < max_paths:
                path = stack.pop()
                for edge in self.out_edges(path[-1]):
                    if edge.target in sink_set:
                        found.append(tuple(path + [edge.target]))
                    elif edge.target not in path and len(path) < max_depth:
                        stack.append(path + [edge.target])
        return tuple(dict.fromkeys(found))  # dedupe, preserve first-seen order

    # -- integration detectors -------------------------------------------
    def propagate_dirty(
        self,
        injections: Mapping[str, float],
        tolerance: float = 1e-9,
        max_iter: int = 2000,
    ) -> dict[str, float]:
        """Conservatively re-distribute dirty mass along edges until it pools at sinks.

        At each iteration the dirty value currently sitting at a node splits to
        its out-neighbours in proportion to edge weight; a node with no
        out-edges retains its mass (it is a sink). Iteration stops at
        convergence or ``max_iter`` (guards ill-posed pure circulations).
        """
        state = {n: float(injections.get(n, 0.0)) for n in self.nodes()}
        for _ in range(max_iter):
            nxt: defaultdict[str, float] = defaultdict(float)
            for node in self.nodes():
                total_out = self.out_amount(node)
                if total_out <= 0.0:
                    nxt[node] += state[node]
                else:
                    for edge in self.out_edges(node):
                        nxt[edge.target] += state[node] * (edge.amount / total_out)
            delta = max((abs(nxt[n] - state[n]) for n in state), default=0.0)
            state = {n: nxt[n] for n in self.nodes()}
            if delta < tolerance:
                break
        return state

    def integration_score(
        self,
        injections: Mapping[str, float],
        sinks: Iterable[str],
        tolerance: float = 1e-9,
        max_iter: int = 2000,
    ) -> tuple[float, dict[str, float]]:
        """Return ``(integration, dirty_frac_by_sink)`` in [0, 1].

        Integration = 1 - mean dirty fraction at the integration sinks: a high
        score means placed dirty value has been diluted by legitimate flows so
        it is no longer distinguishable.
        """
        state = self.propagate_dirty(injections, tolerance, max_iter)
        fractions: dict[str, float] = {}
        for sink in sinks:
            total_in = self.in_amount(sink)
            if self.has_node(sink) and total_in > 0:
                fractions[sink] = state.get(sink, 0.0) / total_in
        mean_fraction = sum(fractions.values()) / len(fractions) if fractions else 0.0
        integration = 1.0 - min(max(mean_fraction, 0.0), 1.0)
        return integration, fractions

    def mixing_entropy(
        self,
        injections: Mapping[str, float],
        sinks: Iterable[str],
        tolerance: float = 1e-9,
        max_iter: int = 2000,
    ) -> float:
        """Shannon entropy of the dirty-mass distribution across sinks."""
        state = self.propagate_dirty(injections, tolerance, max_iter)
        values = [state.get(s, 0.0) for s in sinks]
        total = sum(values)
        if total <= 0.0:
            return 0.0
        probs = [v / total for v in values if v > 0]
        return -sum(p * math.log(p) for p in probs)


@dataclass(frozen=True)
class LaunderingReport:
    """Deterministic restructuring of the laundering analysis for one graph."""

    num_nodes: int
    num_edges: int
    placement: float
    cycles: tuple[tuple[str, ...], ...]
    funnels: tuple[dict[str, float | str | int], ...]
    layering_paths: tuple[tuple[str, ...], ...]
    layering_score: float
    layering_components: dict[str, float]
    integration_score: float
    mixing_entropy: float
    dirty_fractions: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "placement": self.placement,
            "num_cycles": len(self.cycles),
            "cycles": [list(c) for c in self.cycles],
            "num_funnels": len(self.funnels),
            "funnels": list(self.funnels),
            "num_layering_paths": len(self.layering_paths),
            "layering_score": self.layering_score,
            "layering_components": dict(self.layering_components),
            "integration_score": self.integration_score,
            "mixing_entropy": self.mixing_entropy,
            "dirty_fractions": dict(self.dirty_fractions),
        }


def analyze_laundering(
    graph: TransactionGraph,
    sources: Iterable[str],
    sinks: Iterable[str],
    max_depth: int = 8,
    max_cycles: int = 50,
    max_paths: int = DEFAULT_MAX_PATHS,
    funnel_threshold: float = DEFAULT_FUNNEL_THRESHOLD,
) -> LaunderingReport:
    """Run the full layering + integration detection suite over ``graph``.

    ``sources`` are the dirty placement nodes and ``sinks`` the integration
    accounts. The composite layering score blends normalized cycle volume,
    mean layering-chain depth, and funnel imbalance, each in [0, 1].

    The four search bounds (``max_depth``, ``max_cycles``, ``max_paths``,
    ``funnel_threshold``) are threaded through to the detectors rather than
    left at their callee defaults, so :func:`canonical_laundering_params`
    genuinely controls the analysis instead of merely naming it.
    """
    cycles = graph.find_cycles(max_depth=max_depth, max_cycles=max_cycles)
    funnels = graph.funnels(threshold=funnel_threshold)
    sink_tuple = tuple(sinks)
    source_list = list(sources)

    paths = graph.layering_paths(source_list, sink_tuple, max_depth=max_depth, max_paths=max_paths)
    depth_stats = [len(p) - 1 for p in paths]
    mean_depth = sum(depth_stats) / len(depth_stats) if depth_stats else 0.0

    imbalance_vals = [abs(float(f["funnel_ratio"]) - 1.0) for f in funnels]
    mean_imbalance = sum(imbalance_vals) / len(imbalance_vals) if imbalance_vals else 0.0

    cycle_component = min(math.log1p(len(cycles)) / math.log1p(float(max_cycles)), 1.0)
    depth_component = min(mean_depth / max(float(max_depth), 1.0), 1.0)
    funnel_component = min(mean_imbalance / 2.0, 1.0)
    components = {
        "cycle_component": cycle_component,
        "depth_component": depth_component,
        "funnel_component": funnel_component,
    }
    w_cycle, w_depth, w_funnel = LAYERING_WEIGHTS
    layering_score = w_cycle * cycle_component + w_depth * depth_component + w_funnel * funnel_component

    placement = sum(float(graph.out_amount(s)) for s in sources)
    injections = {s: float(graph.out_amount(s)) for s in sources}
    integration, fractions = graph.integration_score(injections, sink_tuple)
    entropy = graph.mixing_entropy(injections, sink_tuple)

    return LaunderingReport(
        num_nodes=len(graph.nodes()),
        num_edges=len(graph.edges()),
        placement=placement,
        cycles=cycles,
        funnels=funnels,
        layering_paths=paths,
        layering_score=layering_score,
        layering_components=components,
        integration_score=integration,
        mixing_entropy=entropy,
        dirty_fractions=fractions,
    )


def build_sanchez_network(seed: int = 0) -> TransactionGraph:
    """Deterministically build the canonical Sanchez laundering network.

    Structure is fixed (cartel typology); edge amounts are drawn from a
    seeded RNG so the SAME seed always yields the SAME graph and therefore
    the SAME report — a live determinism proof.
    """
    rng = np.random.default_rng(seed)
    graph = TransactionGraph()

    cash_sources = [f"S{i}" for i in range(1, 4)]  # street collectors (placement)
    shells = [f"F{i}" for i in range(1, 7)]  # shell fronts (layering)
    seafood = [f"W{i}" for i in range(1, 4)]  # Wavekrest seafood fronts
    currency = [f"C{i}" for i in range(1, 4)]  # currency exchanges
    banks = [f"B{i}" for i in range(1, 5)]  # integration sinks
    legit = [f"L{i}" for i in range(1, 4)]  # legitimate exporters (mixer)

    def add(src: str, dst: str, sector: str) -> None:
        graph.add_transaction(Transaction(src, dst, float(rng.uniform(1.0, 20.0)), sector))

    # placement: cash → shells
    for s in cash_sources:
        for f in shells[:4]:
            add(s, f, "cash")
    # layering: shell → shell (a couple of money-returning loops)
    add(shells[0], shells[2], "shell")
    add(shells[2], shells[0], "shell")
    add(shells[1], shells[3], "shell")
    add(shells[3], shells[4], "shell")
    add(shells[4], shells[1], "shell")
    # layering onward: shells → seafood + currency
    for f in shells:
        for w in seafood:
            add(f, w, "seafood")
        for c in currency:
            add(f, c, "currency")
    # integration: seafood + currency → banks
    for w in seafood:
        for b in banks:
            add(w, b, "bank")
    for c in currency:
        for b in banks:
            add(c, b, "bank")
    # legitimate mixing flows into the same banks
    for exporter in legit:
        for b in banks:
            add(exporter, b, "legit")

    return graph


def canonical_laundering_params() -> dict[str, Any]:
    """Single source of truth for the canonical Sanchez-network analysis.

    Mirrors the ``mission.laundering`` block of ``manuscript/config.yaml``
    (bound by ``tests/test_canonical_params.py``) and is consumed by
    ``mission.py``, ``manuscript_variables.py``, and ``figures/plots.py`` so
    the three cannot drift apart.
    """
    return {
        "seed": 0,
        "sources": ("S1", "S2", "S3"),
        "sinks": ("B1", "B2", "B3", "B4"),
        "max_depth": 8,
        "max_cycles": 50,
        "max_paths": DEFAULT_MAX_PATHS,
        "funnel_threshold": DEFAULT_FUNNEL_THRESHOLD,
        "layering_weights": LAYERING_WEIGHTS,
    }
