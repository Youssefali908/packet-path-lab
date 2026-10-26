import math
import networkx as nx
import pandas as pd
import pytest

from routing_model import (
    baseline_edges, build_graph, candidate_routes, compute_route, dijkstra_states,
    prepare_edge_table, preset_edges, set_cost, set_status, verify_route, NODES,
)


def test_verified_baseline_example():
    route = compute_route(baseline_edges(), "A", "F")
    assert route.path == ("A", "C", "E", "F")
    assert route.total_cost == 12  # A-C (2) + C-E (3) + E-F (7)
    assert route.hops == 3
    assert route.total_latency_ms == 3 + 4 + 6
    assert verify_route(baseline_edges(), "A", "F")["passed"]


def test_increase_one_cost_triggers_recomputation():
    route = compute_route(set_cost(baseline_edges(), "E-F", 20), "A", "F")
    assert route.path == ("A", "C", "E", "D", "F")
    assert route.total_cost == 20


def test_failure_reroutes_without_fake_high_cost():
    edges = set_status(baseline_edges(), "E-F", "down")
    assert not build_graph(edges).has_edge("E", "F")
    route = compute_route(edges, "A", "F")
    assert route.path == ("A", "C", "E", "D", "F")
    assert route.total_cost == 20


def test_disconnected_network_boundary_case():
    route = compute_route(preset_edges("A disconnected"), "A", "F")
    assert route.reachable is False
    assert route.path == ()
    assert route.total_cost is None
    assert verify_route(preset_edges("A disconnected"), "A", "F")["passed"]


def test_equal_source_and_destination_boundary_case():
    route = compute_route(baseline_edges(), "C", "C")
    assert route.path == ("C",)
    assert route.total_cost == 0
    assert route.hops == 0
    assert route.total_latency_ms == 0


def test_trace_step_states_match_route():
    states = dijkstra_states(build_graph(baseline_edges()), "A", "F")
    assert states[0]["current"] is None
    assert states[0]["distances"]["A"] == 0
    assert states[-1]["distances"]["F"] == 12
    assert states[-1]["current"] == "F"
    assert all(len(s["settled"]) == s["step"] for s in states)


def test_all_pairs_against_independent_networkx():
    for scenario in ("Baseline", "High E–F cost", "E–F link failure", "A disconnected"):
        edges = preset_edges(scenario)
        for s in NODES:
            for d in NODES:
                assert verify_route(edges, s, d)["passed"], (scenario, s, d)


def test_cost_zero_allowed_and_negative_rejected():
    edges = set_cost(baseline_edges(), "E-F", 0)
    assert verify_route(edges, "A", "F")["passed"]
    with pytest.raises(ValueError, match="nonnegative"):
        set_cost(edges, "E-F", -1)


def test_missing_field_rejected_not_silently_imputed():
    df = pd.DataFrame(baseline_edges()).drop(columns=["cost"])
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_edge_table(df)


def test_missing_numeric_cell_rejected():
    df = pd.DataFrame(baseline_edges())
    df.loc[0, "cost"] = float("nan")
    with pytest.raises(ValueError, match="Missing/invalid"):
        prepare_edge_table(df)


def test_candidate_routes_are_sorted():
    paths = candidate_routes(baseline_edges(), "A", "F")
    assert paths[0]["total_cost"] == 12
    assert all(paths[i]["total_cost"] <= paths[i+1]["total_cost"]
               for i in range(len(paths)-1))