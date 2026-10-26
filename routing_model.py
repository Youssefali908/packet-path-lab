"""Deterministic OSPF-inspired weighted-graph educational simulation.

Routing COST is a dimensionless nonnegative weight. Contextual link latency (ms)
and bandwidth (Mbps) do not affect routing unless costs are changed explicitly.
This is not an implementation of live OSPF or packet forwarding.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from copy import deepcopy
from pathlib import Path
import math
from typing import Any, Mapping

import networkx as nx
import pandas as pd

NODES = tuple("ABCDEF")
BASELINE_FILE = Path(__file__).resolve().parent / "data" / "network_edges.csv"
REQUIRED_COLUMNS = (
    "edge_id", "source", "target", "cost", "latency_ms", "bandwidth_mbps", "status", "scenario"
)
POSITIONS = {
    "A": (0.0, 0.0), "B": (1.0, 1.0), "C": (1.0, -1.0),
    "D": (2.0, 1.0), "E": (2.0, -1.0), "F": (3.0, 0.0),
}


@dataclass(frozen=True)
class RouteSummary:
    source: str
    destination: str
    path: tuple[str, ...]
    reachable: bool
    total_cost: float | None
    hops: int | None
    total_latency_ms: float | None
    bottleneck_bandwidth_mbps: float | None

    @property
    def path_label(self) -> str:
        return " → ".join(self.path) if self.reachable else "No route available"

    def as_record(self, scenario: str = "current") -> dict[str, Any]:
        row = asdict(self)
        row["path"] = self.path_label
        row["scenario"] = scenario
        return row


def _real(value: Any, field: str) -> float:
    """Reject missing, non-finite, non-numeric or negative observations."""
    if isinstance(value, bool) or pd.isna(value):
        raise ValueError(f"Missing/invalid {field}: {value!r}")
    try:
        val = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Non-numeric {field}: {value!r}") from exc
    if not math.isfinite(val) or val < 0:
        raise ValueError(f"{field} must be finite and nonnegative: {value!r}")
    return val


def prepare_edge_table(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Validate the explicit edge schema, normalize values and return records."""
    missing = sorted(set(REQUIRED_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    result = []
    used_ids = set()
    for index, record in enumerate(frame.loc[:, REQUIRED_COLUMNS].to_dict("records"), start=1):
        u, v = str(record["source"]).strip().upper(), str(record["target"]).strip().upper()
        if u not in NODES or v not in NODES or u == v:
            raise ValueError(f"Row {index}: invalid edge endpoints {u!r}, {v!r}")
        expected = "-".join(sorted((u, v)))
        if str(record["edge_id"]).strip().upper() != expected:
            raise ValueError(f"Row {index}: edge_id must be {expected}")
        if expected in used_ids:
            raise ValueError(f"Duplicate undirected edge {expected}")
        used_ids.add(expected)
        status = str(record["status"]).lower().strip()
        if status not in ("up", "down"):
            raise ValueError(f"Row {index}: status must be up or down")
        result.append({
            "edge_id": expected, "source": u, "target": v,
            "cost": _real(record["cost"], f"cost on {expected}"),
            "latency_ms": _real(record["latency_ms"], f"latency_ms on {expected}"),
            "bandwidth_mbps": _real(record["bandwidth_mbps"], f"bandwidth_mbps on {expected}"),
            "status": status, "scenario": str(record["scenario"]),
        })
    return result


def baseline_edges() -> list[dict[str, Any]]:
    return prepare_edge_table(pd.read_csv(BASELINE_FILE))


def clone_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return deepcopy(edges)


def set_cost(edges: list[dict[str, Any]], edge_id: str, cost: float) -> list[dict[str, Any]]:
    new_edges = clone_edges(edges)
    cost = _real(cost, "routing cost")
    for edge in new_edges:
        if edge["edge_id"] == edge_id:
            edge["cost"] = cost
            return new_edges
    raise KeyError(edge_id)


def set_status(edges: list[dict[str, Any]], edge_id: str, status: str) -> list[dict[str, Any]]:
    if status not in {"up", "down"}:
        raise ValueError("Status must be up or down")
    new_edges = clone_edges(edges)
    for edge in new_edges:
        if edge["edge_id"] == edge_id:
            edge["status"] = status
            return new_edges
    raise KeyError(edge_id)


def preset_edges(name: str) -> list[dict[str, Any]]:
    edges = baseline_edges()
    if name == "Baseline":
        return edges
    if name == "High E–F cost":
        return set_cost(edges, "E-F", 20)
    if name == "E–F link failure":
        return set_status(edges, "E-F", "down")
    if name == "A disconnected":
        return set_status(set_status(edges, "A-B", "down"), "A-C", "down")
    raise ValueError(f"Unknown preset: {name}")


def build_graph(edges: list[dict[str, Any]]) -> nx.Graph:
    """Construct active topology. Down edges are ABSENT, not given high cost."""
    graph = nx.Graph()
    graph.add_nodes_from(NODES)
    for edge in edges:
        for f in ("cost", "latency_ms", "bandwidth_mbps"):
            _real(edge.get(f), f)
        if edge["status"] == "up":
            graph.add_edge(edge["source"], edge["target"],
                           cost=float(edge["cost"]),
                           latency_ms=float(edge["latency_ms"]),
                           bandwidth_mbps=float(edge["bandwidth_mbps"]),
                           edge_id=edge["edge_id"])
    return graph


def dijkstra_states(graph: nx.Graph, source: str, destination: str) -> list[dict[str, Any]]:
    """Teaching-oriented deterministic Dijkstra state log.

    Minimum distance first; equal-distance paths choose lexicographically smaller
    full node sequences. Every state is a snapshot AFTER settling/relaxing one
    node; an initial state precedes all settlements.
    """
    if source not in graph or destination not in graph:
        raise ValueError("Source/destination is not part of the graph")
    distance = {node: float("inf") for node in sorted(graph.nodes)}
    parent: dict[str, str | None] = {node: None for node in sorted(graph.nodes)}
    signatures: dict[str, tuple[str, ...] | None] = {node: None for node in sorted(graph.nodes)}
    distance[source] = 0.0
    signatures[source] = (source,)
    settled: list[str] = []
    states = [{
        "step": 0, "current": None, "settled": [], "frontier": [source],
        "relaxed_edges": [], "distances": dict(distance), "predecessors": dict(parent),
        "description": f"Initialize: distance({source}) = 0; all others = ∞.",
    }]
    while True:
        viable = [n for n in distance if n not in settled and math.isfinite(distance[n])]
        if not viable:
            break
        current = min(viable, key=lambda n: (distance[n], signatures[n]))
        settled.append(current)
        updates = []
        for neighbor in sorted(graph.neighbors(current)):
            if neighbor in settled:
                continue
            proposal = distance[current] + graph[current][neighbor]["cost"]
            candidate = signatures[current] + (neighbor,)
            if proposal < distance[neighbor] or (proposal == distance[neighbor] and (
                signatures[neighbor] is None or candidate < signatures[neighbor]
            )):
                distance[neighbor] = proposal
                parent[neighbor] = current
                signatures[neighbor] = candidate
                updates.append({"from": current, "to": neighbor, "new_distance": proposal})
        frontier = sorted(
            (n for n in distance if n not in settled and math.isfinite(distance[n])),
            key=lambda n: (distance[n], signatures[n]),
        )
        states.append({
            "step": len(states), "current": current, "settled": list(settled),
            "frontier": frontier, "relaxed_edges": updates,
            "distances": dict(distance), "predecessors": dict(parent),
            "description": f"Settle {current} (cost {distance[current]:g}); "
                           + ("relax " + ", ".join(f"{x['to']} to {x['new_distance']:g}" for x in updates)
                              if updates else "no distance updates"),
        })
        if current == destination:
            break
    return states


def compute_route(edges: list[dict[str, Any]], source: str, destination: str) -> RouteSummary:
    graph = build_graph(edges)
    states = dijkstra_states(graph, source, destination)
    last = states[-1]
    total = last["distances"][destination]
    if not math.isfinite(total):
        return RouteSummary(source, destination, (), False, None, None, None, None)
    path = [destination]
    while path[-1] != source:
        prev = last["predecessors"].get(path[-1])
        if prev is None:
            raise RuntimeError("Inconsistent Dijkstra predecessor table")
        path.append(prev)
    path.reverse()
    total_latency = sum(graph[u][v]["latency_ms"] for u, v in zip(path, path[1:]))
    bandwidth = min((graph[u][v]["bandwidth_mbps"] for u, v in zip(path, path[1:])), default=None)
    return RouteSummary(source, destination, tuple(path), True, float(total),
                        len(path) - 1, float(total_latency), bandwidth)


def verify_route(edges: list[dict[str, Any]], source: str, destination: str) -> dict[str, Any]:
    """Cross-check logged Dijkstra cost vs NetworkX and sum of edge costs."""
    graph = build_graph(edges)
    result = compute_route(edges, source, destination)
    try:
        expected = float(nx.dijkstra_path_length(graph, source, destination, weight="cost"))
        independent_reachable = True
    except nx.NetworkXNoPath:
        expected = None
        independent_reachable = False
    edge_sum = (sum(graph[u][v]["cost"] for u, v in zip(result.path, result.path[1:]))
                if result.reachable else None)
    passed = result.reachable == independent_reachable
    if passed and independent_reachable:
        passed = math.isclose(result.total_cost, expected) and math.isclose(edge_sum, expected)
    return {
        "passed": bool(passed), "source": source, "destination": destination,
        "logged_cost": result.total_cost, "recomputed_edge_sum": edge_sum,
        "networkx_cost": expected, "reachable": result.reachable,
        "path": result.path_label,
    }


def path_edges(path: tuple[str, ...] | list[str]) -> set[str]:
    return {"-".join(sorted((u, v))) for u, v in zip(path, path[1:])}


def candidate_routes(edges: list[dict[str, Any]], source: str, destination: str, n: int = 5) -> list[dict[str, Any]]:
    graph = build_graph(edges)
    if source == destination:
        return [{"path": source, "total_cost": 0.0, "hops": 0}]
    if not nx.has_path(graph, source, destination):
        return []
    from itertools import islice
    options = list(islice(nx.shortest_simple_paths(graph, source, destination, weight="cost"), n))
    rows = [
        {"path": " → ".join(path),
         "total_cost": sum(graph[u][v]["cost"] for u, v in zip(path, path[1:])),
         "hops": len(path) - 1}
        for path in options
    ]
    return sorted(rows, key=lambda x: (x["total_cost"], x["path"]))


def edge_frame(edges: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(edges, columns=REQUIRED_COLUMNS)


def trace_frame(states: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for st in states:
        for node in NODES:
            dist = st["distances"][node]
            rows.append({
                "step": st["step"], "current": st["current"], "node": node,
                "distance": dist if math.isfinite(dist) else None,
                "predecessor": st["predecessors"][node],
                "settled": node in st["settled"],
                "in_frontier": node in st["frontier"],
            })
    return pd.DataFrame(rows)