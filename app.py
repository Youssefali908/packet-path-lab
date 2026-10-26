"""CPS 5745 - How Do Packets Find a Path Through a Network?

Run: streamlit run app.py
A six-view dynamic scientific story based on the approved routing proposal.
"""

from __future__ import annotations

import io
import json
import math

import pandas as pd
import streamlit as st

from routing_model import (
    NODES, baseline_edges, build_graph, candidate_routes, clone_edges,
    compute_route, dijkstra_states, edge_frame, preset_edges,
    set_cost, set_status, trace_frame, verify_route,
)
from visualizations import (
    COLORS, animation_figure, candidate_bar, network_figure, scenario_bars,
)

st.set_page_config(
    page_title="Packet Path Lab | Dynamic Scientific Storytelling",
    page_icon="🌐", layout="wide", initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', Arial, sans-serif; }
    .stApp { background: #0B1220; color: #F1F5FC; }
    [data-testid="stSidebar"] { background: #101A2B; border-right: 1px solid #22344B; }
    [data-testid="stMetric"] { background: #152238; padding: 15px 18px; border: 1px solid #2B3F58; border-radius: 13px; }
    [data-testid="stMetricLabel"] { color: #A6BAD2; }
    [data-testid="stMetricValue"] { color: #F1F5FC; font-family: 'Space Grotesk', Arial, sans-serif; }
    /* Keep the hero clear of the Streamlit toolbar at the top of the page. */
    [data-testid="stMainBlockContainer"], .block-container {
        padding-top: 3.75rem !important;
        padding-bottom: 4rem;
        max-width: 1450px;
    }
    h1,h2,h3 { font-family: 'Space Grotesk', Arial, sans-serif; letter-spacing: -.025em; }
    h1 { line-height: 1.14; }
    .story-hero {
        padding: 23px 28px 26px;
        margin: 0 0 23px;
        border: 1px solid #29415A;
        border-radius: 18px;
        background: linear-gradient(115deg, #15263A 0%, #111B2F 67%, #132335 100%);
        box-shadow: 0 12px 32px rgba(0, 0, 0, .13);
    }
    .story-hero .story-label {
        display: block;
        margin: 0 0 13px;
        padding: 0;
        color: #42DFC2;
        font: 700 12px/1.5 'DM Sans', Arial, sans-serif;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .story-hero h1 {
        margin: 0 0 14px !important;
        padding: 0;
        color: #F1F5FC;
        font: 700 clamp(28px, 2.8vw, 43px)/1.16 'Space Grotesk', Arial, sans-serif;
        letter-spacing: -.035em;
        overflow-wrap: anywhere;
    }
    .story-hero p {
        margin: 0;
        color: #BDCCE0;
        font: 400 clamp(14px, 1.2vw, 16px)/1.65 'DM Sans', Arial, sans-serif;
        max-width: 1000px;
    }
    @media (max-width: 800px) {
        [data-testid="stMainBlockContainer"], .block-container { padding-top: 3.2rem !important; }
        .story-hero { padding: 19px 18px; }
    }
    [data-baseweb="tab"] { font-weight: 650; }
    [data-testid="stAlert"] { border-radius: 12px; }
    .eyebrow { color: #42DFC2; font-weight: 700; letter-spacing: .16em; font-size: 12px; margin-bottom: 4px; }
    .description { color: #A9BAD0; font-size: 16px; max-width: 900px; margin-bottom: 16px; }
    .smallnote { color: #8BA1BB; font-size: 12px; }
    .legend { background:#132136; border:1px solid #263B55; padding:9px 14px; border-radius:9px; font-size:13px; }
    hr { border-color: #22344B; }
</style>
""", unsafe_allow_html=True)


# Session-state values are shared across EVERY visualization.
if "edges" not in st.session_state:
    st.session_state.edges = baseline_edges()
if "source" not in st.session_state:
    st.session_state.source = "A"
if "destination" not in st.session_state:
    st.session_state.destination = "F"
if "algorithm_step" not in st.session_state:
    st.session_state.algorithm_step = 0
if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}
if "cost_selected_edge" not in st.session_state:
    st.session_state.cost_selected_edge = "E-F"
if "cost_value" not in st.session_state:
    st.session_state.cost_value = 7.0
if "failure_selected_edge" not in st.session_state:
    st.session_state.failure_selected_edge = "E-F"
if "preset_to_load" not in st.session_state:
    st.session_state.preset_to_load = "Baseline"
if "snapshot_name" not in st.session_state:
    st.session_state.snapshot_name = "My experiment"


def refresh_cost_control() -> None:
    chosen = st.session_state.cost_selected_edge
    target = next(e for e in st.session_state.edges if e["edge_id"] == chosen)
    st.session_state.cost_value = float(target["cost"])


def reset_step() -> None:
    st.session_state.algorithm_step = 0


def apply_cost() -> None:
    st.session_state.edges = set_cost(
        st.session_state.edges, st.session_state.cost_selected_edge, st.session_state.cost_value
    )
    reset_step()


def load_preset(preset: str) -> None:
    st.session_state.edges = preset_edges(preset)
    refresh_cost_control()
    reset_step()


def restore_link_cost() -> None:
    edge_id = st.session_state.cost_selected_edge
    baseline = next(e for e in baseline_edges() if e["edge_id"] == edge_id)
    st.session_state.edges = set_cost(st.session_state.edges, edge_id, baseline["cost"])
    st.session_state.cost_value = float(baseline["cost"])
    reset_step()


def reset_network() -> None:
    st.session_state.edges = baseline_edges()
    st.session_state.source = "A"
    st.session_state.destination = "F"
    st.session_state.preset_to_load = "Baseline"
    st.session_state.cost_selected_edge = "E-F"
    st.session_state.failure_selected_edge = "E-F"
    st.session_state.cost_value = 7.0
    reset_step()


def toggle_failure_link() -> None:
    """Run before widgets render, so resetting the Dijkstra slider is legal.

    Streamlit invokes on_click callbacks at the start of the new rerun.
    Writing to algorithm_step inline in View 5 would fail because View 4
    has already instantiated the slider bound to that session-state key.
    """
    edge_id = st.session_state.failure_selected_edge
    current = next(e for e in st.session_state.edges if e["edge_id"] == edge_id)
    new_status = "down" if current["status"] == "up" else "up"
    st.session_state.edges = set_status(st.session_state.edges, edge_id, new_status)
    reset_step()


with st.sidebar:
    st.markdown("### ◉ Packet Path Lab")
    st.caption("A deterministic, OSPF-inspired teaching simulation")
    st.divider()
    st.markdown("#### Route endpoints")
    st.selectbox("Source router", NODES, key="source", on_change=reset_step)
    st.selectbox("Destination router", NODES, key="destination", on_change=reset_step)
    st.markdown("#### Load scenario")
    st.selectbox("Starting scenario", [
        "Baseline", "High E–F cost", "E–F link failure", "A disconnected",
    ], key="preset_to_load")
    st.button("Load chosen scenario", use_container_width=True,
              on_click=load_preset, args=(st.session_state.preset_to_load,))
    st.button("↺ Reset network & endpoints", use_container_width=True,
              on_click=reset_network)
    st.divider()
    st.markdown("#### Save your experiment")
    st.text_input("Snapshot label", key="snapshot_name", max_chars=38)
    if st.button("Save current scenario", use_container_width=True):
        label = st.session_state.snapshot_name.strip()
        if not label:
            st.warning("Enter a scenario name first.")
        elif label in {"Baseline", "High E–F cost", "E–F link failure", "A disconnected", "Current experiment"}:
            st.warning("Choose a different label; this name is reserved.")
        else:
            st.session_state.saved_scenarios[label] = clone_edges(st.session_state.edges)
            st.success(f"Saved ‘{label}’ for View 6.")
    if st.session_state.saved_scenarios:
        st.caption(f"{len(st.session_state.saved_scenarios)} snapshot(s) saved in this browser session")
        if st.button("Clear saved snapshots", use_container_width=True):
            st.session_state.saved_scenarios = {}
            st.rerun()
    st.divider()
    st.caption("Scope: six synthetic routers · no live packet captures · no real-time OSPF")

edges = st.session_state.edges
source = st.session_state.source
destination = st.session_state.destination
route = compute_route(edges, source, destination)
graph = build_graph(edges)

# Single self-contained header avoids tiny clipped lines and inconsistent title spacing.
st.markdown(
    '<section class="story-hero" aria-label="Project introduction">'
    '<span class="story-label">CPS 5745 · Dynamic Scientific Storytelling</span>'
    '<h1>How Do Packets Find a Path Through a Network?</h1>'
    '<p>Explore how <strong>weighted link costs</strong>, routing algorithms, and failed links '
    'change the path selected between routers. Six connected experiments share the same model and route state.</p>'
    '</section>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns([2.2, 1, 1, 1.2])
m1.metric("SELECTED ROUTE", route.path_label)
m2.metric("ROUTING COST", f"{route.total_cost:g}" if route.reachable else "N/A")
m3.metric("HOPS", route.hops if route.reachable else "N/A")
m4.metric("LINK LATENCY SUM", f"{route.total_latency_ms:g} ms" if route.reachable else "N/A")
st.markdown(
    '<div class="smallnote">Routing cost is dimensionless and drives route selection. Latency (ms) and bandwidth '
    '(Mbps) are illustrative context attributes, <strong>not</strong> inputs to the routing algorithm.</div>',
    unsafe_allow_html=True,
)
st.divider()

tabs = st.tabs([
    "01 · Network map", "02 · Packet journey", "03 · Cost explorer",
    "04 · Dijkstra", "05 · Link failure", "06 · Comparison", "Data & verification",
])


# VIEW 1 ----------------------------------------------------------------------
with tabs[0]:
    st.subheader("01 — Network Overview: Where Can a Packet Go?")
    st.write("Each router is a node; each available link carries a **dimensionless routing cost**. "
             "The teal path minimizes the **sum of costs**, not geometric distance on the screen.")
    left, right = st.columns([2.2, 1])
    with left:
        st.plotly_chart(network_figure(edges, route.path, source, destination,
                                       title="Network map · hover over edge midpoints to inspect exact values"),
                        use_container_width=True, key="network_v1")
    with right:
        st.markdown("**Read the diagram**")
        st.markdown(
            '<div class="legend">🔵 Blue = source router<br>🟠 Orange = destination router<br>'
            '🟢 Teal = least-cost path<br>🔴 Dashed red = failed link<br>'
            'Numbers = edge routing cost (unitless)</div>', unsafe_allow_html=True,
        )
        st.write("**Try it:** Change the source/destination in the sidebar. Every view recalculates.")
        st.write(f"**Current result:** {route.path_label}")
        if route.reachable and route.hops:
            path_ids = ["-".join(sorted((u,v))) for u,v in zip(route.path, route.path[1:])]
            route_costs = [next(e["cost"] for e in edges if e["edge_id"] == eid) for eid in path_ids]
            st.code(" + ".join(f"{c:g}" for c in route_costs) + f" = {route.total_cost:g}", language="text")
        elif route.reachable:
            st.info("Source equals destination: no link traversal; cost 0.")
        else:
            st.error("No route available: the active topology disconnects this pair.")
    with st.expander("Inspect all link records (hover also supported)"):
        st.dataframe(edge_frame(edges).drop(columns=["scenario"]),
                     hide_index=True, use_container_width=True)


# VIEW 2 ----------------------------------------------------------------------
with tabs[1]:
    st.subheader("02 — Packet Journey: What Happens Hop by Hop?")
    st.write("This view turns the chosen path into an **ordered sequence of forwarding hops**. "
             "Use the timeline to inspect a position; **Play / Resume**, **Pause**, and **Replay** "
             "are clearly separated below the timeline.")
    if not route.reachable:
        st.warning("No packet journey is possible because the destination is disconnected. "
                   "Restore an active link or choose different endpoints.")
        st.plotly_chart(network_figure(edges, (), source, destination,
                                       title="Unreachable: no valid packet path"),
                        use_container_width=True, key="unreachable_v2")
    else:
        st.plotly_chart(animation_figure(edges, route.path, source, destination),
                        use_container_width=True, key="packet_animation_v2")
        st.caption("Motion is illustrative and paced for viewing. Displayed modeled elapsed milliseconds are "
                   "the sum of the synthetic one-way link latencies; animation wall-clock timing is NOT network latency.")
        hop_rows = []
        cumulative = 0.0
        for idx, (u, v) in enumerate(zip(route.path, route.path[1:]), start=1):
            eid = "-".join(sorted((u, v)))
            link = next(e for e in edges if e["edge_id"] == eid)
            cumulative += link["latency_ms"]
            hop_rows.append({"Hop": idx, "From": u, "To": v, "Link": eid,
                             "Routing cost (unitless)": link["cost"],
                             "One-way latency (ms)": link["latency_ms"],
                             "Cumulative illustrative latency (ms)": cumulative})
        st.markdown("**Hop-by-hop inspection**")
        if hop_rows:
            st.dataframe(pd.DataFrame(hop_rows), hide_index=True, use_container_width=True)
        else:
            st.info("Zero-hop route: source and destination are the same router.")


# VIEW 3 ----------------------------------------------------------------------
with tabs[2]:
    st.subheader("03 — Link-Cost Explorer: Why Does the Route Change?")
    st.write("Edit **one link's routing cost** and see how the least-cost route and its alternatives change. "
             "The routing algorithm uses the sum of the link costs, not their latencies or screen lengths.")
    control_col, expl_col = st.columns([1, 1.7])
    with control_col:
        st.selectbox("Link to edit", [e["edge_id"] for e in edges],
                     key="cost_selected_edge", on_change=refresh_cost_control)
        st.slider("Routing cost (unitless)", min_value=0.0, max_value=40.0, step=1.0,
                  key="cost_value", on_change=apply_cost)
        chosen = next(e for e in st.session_state.edges if e["edge_id"] == st.session_state.cost_selected_edge)
        st.caption(f"Current {chosen['edge_id']} latency: {chosen['latency_ms']:g} ms · "
                   f"bandwidth: {chosen['bandwidth_mbps']:g} Mbps · status: {chosen['status']}")
        st.button("Restore just this link's baseline cost", key="restore_single_cost",
                  on_click=restore_link_cost)
        st.info("**Guided experiment:** Select E–F, start at cost 7, then raise it to 20. "
                "For A → F, the chosen path switches from A → C → E → F (12) to "
                "A → C → E → D → F (20).")
    with expl_col:
        st.plotly_chart(candidate_bar(candidate_routes(edges, source, destination), route.path_label),
                        use_container_width=True, key="route_cost_bars_v3")
    st.plotly_chart(network_figure(edges, route.path, source, destination,
                                   title="The same network after cost changes", height=370),
                    use_container_width=True, key="cost_network_v3")


# VIEW 4 ----------------------------------------------------------------------
with tabs[3]:
    st.subheader("04 — Dijkstra Step-Through: How Is the Path Computed?")
    st.write("The shortest path is discovered iteratively. At each step the algorithm settles the node with "
             "the smallest tentative distance, then relaxes its outgoing links.")
    states = dijkstra_states(graph, source, destination)
    st.session_state.algorithm_step = min(st.session_state.algorithm_step, len(states) - 1)
    prev, nextbtn, position = st.columns([1, 1, 5])
    with prev:
        if st.button("← Previous", disabled=st.session_state.algorithm_step == 0):
            st.session_state.algorithm_step -= 1
            st.rerun()
    with nextbtn:
        if st.button("Next →", disabled=st.session_state.algorithm_step == len(states) - 1):
            st.session_state.algorithm_step += 1
            st.rerun()
    with position:
        if len(states) <= 1:
            st.caption("No reachable node can be settled; only initialization is available.")
        else:
            st.slider("Algorithm state", 0, len(states) - 1, key="algorithm_step")
    state = states[st.session_state.algorithm_step]
    st.info(f"**Step {state['step']} of {len(states)-1}:** {state['description']}")
    diagram, distances = st.columns([1.6, 1])
    with diagram:
        st.plotly_chart(network_figure(
            edges, route.path if state["current"] == destination else (), source, destination,
            title="Gold = tentative frontier · blue = settled · highlighted edge = just relaxed",
            settled=state["settled"], frontier=state["frontier"],
            current=state["current"], relaxed_edges=state["relaxed_edges"],
            height=435,
        ), use_container_width=True, key="dijkstra_graph_v4")
    with distances:
        st.markdown("**Algorithm-state table**")
        distance_rows = []
        for node in NODES:
            dist = state["distances"][node]
            status = "Settled" if node in state["settled"] else "Frontier" if node in state["frontier"] else "Unreached"
            distance_rows.append({"Router": node,
                                  "Tentative cost": f"{dist:g}" if math.isfinite(dist) else "∞",
                                  "Predecessor": state["predecessors"][node] or "—",
                                  "State": status})
        st.dataframe(pd.DataFrame(distance_rows), hide_index=True, use_container_width=True)
        if state["relaxed_edges"]:
            st.markdown("**Relaxations at this step**")
            st.dataframe(pd.DataFrame(state["relaxed_edges"]), hide_index=True,
                         use_container_width=True)
        else:
            st.caption("No edge distances changed at this step.")
    st.caption("Tie rule: equal-cost routes use lexicographically ordered router sequences. "
               "Zero/nonnegative costs are supported; negative costs are rejected.")
    with st.expander("View complete algorithm-state data"):
        st.dataframe(trace_frame(states), hide_index=True, use_container_width=True)
        st.download_button("Download this algorithm trace (CSV)",
                           data=trace_frame(states).to_csv(index=False).encode("utf-8"),
                           file_name="dijkstra_trace.csv", mime="text/csv")


# VIEW 5 ----------------------------------------------------------------------
with tabs[4]:
    st.subheader("05 — Failure and Rerouting: What If a Link Goes Down?")
    st.write("Disable an actual edge—not by giving it an artificially huge cost. "
             "A failed link disappears from the graph used for route selection.")
    action, result_col = st.columns([1, 1.5])
    with action:
        st.selectbox("Select a physical link", [e["edge_id"] for e in edges],
                     key="failure_selected_edge")
        edge_choice = next(e for e in edges if e["edge_id"] == st.session_state.failure_selected_edge)
        st.write(f"**Current link status:** `{edge_choice['status'].upper()}`")
        st.button("Disable link" if edge_choice["status"] == "up" else "Restore link",
                  use_container_width=True, type="primary", on_click=toggle_failure_link)
        down = [e["edge_id"] for e in edges if e["status"] == "down"]
        st.write("**Failed links:** " + (", ".join(down) if down else "None"))
        st.caption("To demonstrate the disconnected boundary case, load “A disconnected” "
                   "from the sidebar (A–B and A–C both down).")
    with result_col:
        if route.reachable:
            st.success(f"Current route: {route.path_label} | cost {route.total_cost:g} | {route.hops} hops")
        else:
            st.error("No route available. Routing cost is undefined—not zero and not infinite.")
        baseline_now = compute_route(baseline_edges(), source, destination)
        if baseline_now.reachable and route.reachable:
            diff = route.total_cost - baseline_now.total_cost
            st.metric("Cost change vs. baseline", f"{diff:+g} (unitless)")
        elif not route.reachable:
            st.metric("Reachability", "Disconnected")
    st.plotly_chart(network_figure(edges, route.path, source, destination,
                                   title="Failure state · unavailable edges are red and dashed"),
                    use_container_width=True, key="failure_network_v5")
    st.caption("For A → F, removing E–F causes A → C → E → D → F with cost 20. "
               "Removing both A–B and A–C isolates A; the application reports no route.")


# VIEW 6 ----------------------------------------------------------------------
with tabs[5]:
    st.subheader("06 — Scenario Comparison: What Did We Learn?")
    st.write("Compare unchanged, cost-modified, and failed-link scenarios using the "
             "**same selected source and destination**. Saved experiments appear here too.")
    compare_edges = {
        "Baseline": preset_edges("Baseline"),
        "High E–F cost": preset_edges("High E–F cost"),
        "E–F link failure": preset_edges("E–F link failure"),
        "A disconnected": preset_edges("A disconnected"),
        "Current experiment": clone_edges(edges),
        **st.session_state.saved_scenarios,
    }
    chosen_scenarios = st.multiselect(
        "Scenarios to compare", options=list(compare_edges),
        default=["Baseline", "High E–F cost", "E–F link failure", "Current experiment"],
        key="comparison_selection",
    )
    metric = st.selectbox(
        "Measurement", ["total_cost", "hops", "total_latency_ms"],
        format_func={"total_cost": "Routing cost (unitless)", "hops": "Hops",
                     "total_latency_ms": "Summed one-way latency (ms)"}.get,
        key="comparison_metric",
    )
    scenario_rows = []
    for scenario in chosen_scenarios:
        rec = compute_route(compare_edges[scenario], source, destination)
        scenario_rows.append(rec.as_record(scenario))
    if not chosen_scenarios:
        st.warning("Select at least one scenario for comparison.")
    else:
        st.plotly_chart(scenario_bars(scenario_rows, metric),
                        use_container_width=True, key="scenario_compare_v6")
        st.markdown("**Exact scenario metrics**")
        displayed = pd.DataFrame(scenario_rows)[[
            "scenario", "path", "reachable", "total_cost", "hops", "total_latency_ms",
            "bottleneck_bandwidth_mbps",
        ]].rename(columns={
            "scenario": "Scenario", "path": "Selected route", "reachable": "Reachable",
            "total_cost": "Cost (unitless)", "hops": "Hops", "total_latency_ms": "Latency sum (ms)",
            "bottleneck_bandwidth_mbps": "Bottleneck (Mbps)",
        })
        st.dataframe(displayed, hide_index=True, use_container_width=True)
        st.download_button("Download comparison (CSV)", data=displayed.to_csv(index=False).encode("utf-8"),
                           file_name="scenario_comparison.csv", mime="text/csv")
    st.markdown("**Interpretation and limitations**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Costs govern the route**")
        st.caption("A geometrically shorter drawn line is not necessarily the route with the minimum sum of weights.")
    with c2:
        st.markdown("**Rerouting needs connectivity**")
        st.caption("If a path remains, Dijkstra can find a replacement; if none remains, reachability is false.")
    with c3:
        st.markdown("**This is an educational simulation**")
        st.caption("No live OSPF, queues, policy routing, packet loss, congestion, or actual Internet measurements.")


# BACKSTAGE: explicitly demonstrate data-to-visual transformation and checks.
with tabs[6]:
    st.subheader("Model, Data Workflow & Independent Verification")
    st.write("Data source: **synthetic network topology** specified for this class project. "
             "All costs and contextual link metrics are illustrative rather than captured from real equipment.")
    st.markdown("#### 1. Source and schema")
    st.dataframe(edge_frame(edges), hide_index=True, use_container_width=True)
    st.download_button("Download current edge records (CSV)",
                       data=edge_frame(edges).to_csv(index=False).encode("utf-8"),
                       file_name="current_network_edges.csv", mime="text/csv")
    st.markdown("""
| Field | Meaning | Unit / allowed values |
|---|---|---|
| `source`, `target` | Link endpoints | router label A–F |
| `cost` | Weight in shortest-path optimization | dimensionless, nonnegative |
| `latency_ms` | Illustrative one-way link latency | milliseconds |
| `bandwidth_mbps` | Illustrative link capacity | Mbps |
| `status` | Whether the link exists in available graph | `up` / `down` |
| `scenario` | Origin label of the edge record | text |
| Dijkstra `distance` | Tentative source-to-node weighted distance | dimensionless |
| Dijkstra `predecessor` | Previous node in selected lowest-cost route | router label / null |
| Dijkstra `settled` | Finalized distance state | Boolean |
""")
    st.markdown("#### 2. Preparation-to-visual transformation")
    st.code("""raw_edges = pandas.read_csv('data/network_edges.csv')
validated_records = prepare_edge_table(raw_edges)        # reject invalid/missing values
active_graph = build_graph(validated_records)          # exclude failed edges
states = dijkstra_states(active_graph, source, target) # keep each relaxation step
route = compute_route(validated_records, source, target)
# Then: graph layers → packet frames → candidate paths → algorithm trace → comparison
""", language="python")
    st.latex(r"C(P)=\sum_{e\in P} c_e\qquad P^{*}=\arg\min_{P\in\mathcal{P}(s,d)} C(P)")
    st.markdown("#### 3. Current numerical cross-check")
    comparison = verify_route(edges, source, destination)
    st.success("PASS: computed path, summed edge weights, and NetworkX agree."
               if comparison["passed"] else "WARNING: Verification failed")
    st.json(comparison)
    st.markdown("#### 4. Required fixed test cases")
    baseline = compute_route(baseline_edges(), "A", "F")
    failed = compute_route(preset_edges("E–F link failure"), "A", "F")
    disconnected = compute_route(preset_edges("A disconnected"), "A", "F")
    same = compute_route(baseline_edges(), "C", "C")
    check_rows = [
        {"Test": "Baseline A → F", "Expected": "A-C-E-F, cost 12",
         "Actual": f"{baseline.path_label}, cost {baseline.total_cost:g}",
         "Pass": baseline.path == ("A","C","E","F") and baseline.total_cost == 12},
        {"Test": "E–F down: reroute A → F", "Expected": "A-C-E-D-F, cost 20",
         "Actual": f"{failed.path_label}, cost {failed.total_cost:g}",
         "Pass": failed.path == ("A","C","E","D","F") and failed.total_cost == 20},
        {"Test": "Disconnected A → F", "Expected": "No route available",
         "Actual": disconnected.path_label, "Pass": not disconnected.reachable},
        {"Test": "Same source/destination C → C", "Expected": "Cost 0, hops 0",
         "Actual": f"Cost {same.total_cost:g}, hops {same.hops}",
         "Pass": same.total_cost == 0 and same.hops == 0},
    ]
    st.dataframe(pd.DataFrame(check_rows), hide_index=True, use_container_width=True)
    st.markdown("**Missing values:** Imported schema records with missing endpoints or numeric parameters "
                "are rejected—not silently filled. No percentages or median aggregation are used.")
    st.markdown("#### 5. Sources & scientific scope")
    st.markdown("""
- E. W. Dijkstra (1959), *A note on two problems in connexion with graphs*. DOI: [10.1007/BF01386390](https://doi.org/10.1007/BF01386390).
- J. Moy (1998), [RFC 2328: OSPF Version 2](https://www.rfc-editor.org/rfc/rfc2328.html).
- [NetworkX shortest-path documentation](https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html) — independent check.
- H. Wu and C.-C. Chiang (2004), *A network teaching tool for visualizing and analyzing routing protocols*, cited in the approved proposal.

**Design rationale:** Dynamic 2D is intentional: the studied variable is network connectivity / cost, not physical 3D position. "Fast" animation is for pedagogy only. Ties resolve by the lexicographically smallest complete path. Failed links are removed rather than made artificially costly.

**AI-use disclosure:** ChatGPT assisted with translating the approved storyboard into Python code, Plotly views, narrative copy, tests, and documentation. Results are checked by `pytest` and by an independent NetworkX calculation; the presenter should run the app, inspect every view, verify each claim, and disclose any revisions before submitting.
""")

st.divider()
st.caption("Youssef Ali · Kean University · CPS 5745 · Based on the approved October 2026 network-routing proposal")