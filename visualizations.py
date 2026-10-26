"""Plotly visual grammar shared by all six scientific story views."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from routing_model import POSITIONS, NODES, path_edges

COLORS = {
    "background": "#0B1220", "panel": "#111C2D", "muted": "#7F93AC",
    "text": "#F1F5FC", "edge": "#64748B", "active": "#42DFC2",
    "source": "#7C9CFF", "target": "#FDBA74", "failed": "#FF6B84",
    "visited": "#79AAFF", "frontier": "#F1CC68", "grid": "#28384D",
}


def _layout(fig: go.Figure, title: str, height: int = 430) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.025, "font": {"size": 16, "color": COLORS["text"]}},
        height=height, margin={"l": 12, "r": 12, "t": 55, "b": 16},
        paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["panel"],
        font={"family": "Inter, Arial, sans-serif", "color": COLORS["text"]},
        showlegend=False, hovermode="closest",
        xaxis={"visible": False, "range": [-0.35, 3.35], "fixedrange": True},
        yaxis={"visible": False, "range": [-1.48, 1.48], "scaleanchor": "x", "scaleratio": 1, "fixedrange": True},
    )
    return fig


def network_figure(
    edges: list[dict[str, Any]],
    route: tuple[str, ...] | list[str] = (),
    source: str = "A",
    destination: str = "F",
    *,
    title: str = "Weighted network topology",
    settled: list[str] | None = None,
    frontier: list[str] | None = None,
    current: str | None = None,
    relaxed_edges: list[dict[str, Any]] | None = None,
    packet: tuple[float, float] | None = None,
    packet_label: str = "Packet",
    height: int = 430,
) -> go.Figure:
    fig = go.Figure()
    chosen = path_edges(route)
    relaxing = {"-".join(sorted((d["from"], d["to"]))) for d in (relaxed_edges or [])}
    # Draw both active and failed links, explicitly different from a high-cost link.
    for edge in edges:
        x0, y0 = POSITIONS[edge["source"]]
        x1, y1 = POSITIONS[edge["target"]]
        failed = edge["status"] != "up"
        is_route = edge["edge_id"] in chosen and not failed
        is_relaxed = edge["edge_id"] in relaxing and not failed
        color = (COLORS["failed"] if failed else COLORS["frontier"] if is_relaxed
                 else COLORS["active"] if is_route else COLORS["edge"])
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line={"color": color, "width": 6 if is_route else 4 if is_relaxed else 2,
                  "dash": "dash" if failed else "solid"},
            hoverinfo="skip", showlegend=False,
        ))
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        fig.add_trace(go.Scatter(
            x=[mid_x], y=[mid_y], mode="markers",
            marker={"size": 17, "color": "rgba(255,255,255,0.01)"},
            hovertemplate=(f"<b>Link {edge['edge_id']}</b><br>Routing cost: {edge['cost']:g} (unitless)"
                           f"<br>One-way latency: {edge['latency_ms']:g} ms"
                           f"<br>Bandwidth: {edge['bandwidth_mbps']:g} Mbps"
                           f"<br>Status: {edge['status']}<extra></extra>"),
            showlegend=False,
        ))
        # Shift labels away from nodes and other cost labels.
        shift_x = -0.11 if abs(x0 - x1) < 0.15 else 0
        shift_y = (0.15 if abs(y0 - y1) < 0.15 else 0.11 if y0 + y1 >= 0 else -0.11)
        fig.add_annotation(
            x=mid_x + shift_x, y=mid_y + shift_y,
            text=("DOWN" if failed else f"{edge['cost']:g}"), showarrow=False,
            bgcolor=COLORS["panel"], bordercolor=color, borderwidth=1,
            font={"size": 11, "color": color}, borderpad=3,
        )
    settled_set = set(settled or [])
    frontier_set = set(frontier or [])
    colors = []
    for n in NODES:
        colors.append(
            COLORS["source"] if n == source else COLORS["target"] if n == destination
            else COLORS["frontier"] if n in frontier_set else COLORS["visited"] if n in settled_set
            else "#A3B7D0"
        )
    fig.add_trace(go.Scatter(
        x=[POSITIONS[n][0] for n in NODES], y=[POSITIONS[n][1] for n in NODES],
        mode="markers+text", text=list(NODES), textposition="middle center",
        textfont={"color": "#071624", "size": 15, "family": "Arial Black, Arial"},
        marker={"size": [47 if n == current else 42 for n in NODES],
                "color": colors, "line": {"color": "#C5D4EC", "width": 2}},
        customdata=list(NODES), hovertemplate="Router %{customdata}<extra></extra>",
        showlegend=False,
    ))
    if packet is not None:
        fig.add_trace(go.Scatter(
            x=[packet[0]], y=[packet[1]], mode="markers+text",
            text=["●"], textposition="top center",
            marker={"size": 15, "color": "#FFFFFF", "line": {"color": COLORS["active"], "width": 4}},
            hovertemplate=f"{packet_label}<extra></extra>", name="Packet", showlegend=False,
        ))
    return _layout(fig, title, height=height)


def animation_figure(
    edges: list[dict[str, Any]],
    path: tuple[str, ...], source: str, destination: str,
    *, steps_per_hop: int = 12,
) -> go.Figure:
    """Packet movement is a visual teaching animation, not measured transit time.

    Travel position is interpolated for each hop and annotated with *illustrative*
    cumulative one-way link latencies; frame duration is presentation pacing.
    """
    fig = network_figure(
        edges, path, source, destination,
        title="Packet journey · scrub timeline or use playback controls below", height=460,
        packet=POSITIONS[path[0]], packet_label="Packet starts here",
    )
    packet_trace_index = len(fig.data) - 1
    frames = []
    labels = []
    lookup = {e["edge_id"]: e for e in edges}
    cumulative_ms = 0.0
    if len(path) == 1:
        frames.append(go.Frame(
            name="frame-0", data=[go.Scatter(x=[POSITIONS[path[0]][0]], y=[POSITIONS[path[0]][1]],
                                               mode="markers+text", text=["●"], textposition="top center",
                                               marker={"size": 15, "color": "#FFFFFF",
                                                       "line": {"color": COLORS["active"], "width": 4}})],
            traces=[packet_trace_index],
        ))
        labels.append("Source = destination · 0 hops")
    else:
        idx = 0
        for hop, (u, v) in enumerate(zip(path, path[1:]), start=1):
            eid = "-".join(sorted((u, v)))
            link_latency = lookup[eid]["latency_ms"]
            x0, y0 = POSITIONS[u]
            x1, y1 = POSITIONS[v]
            for substep in range(steps_per_hop + 1):
                if hop > 1 and substep == 0:
                    continue
                frac = substep / steps_per_hop
                x, y = x0 + frac * (x1 - x0), y0 + frac * (y1 - y0)
                t = cumulative_ms + frac * link_latency
                label = f"Hop {hop}/{len(path)-1}: {u} → {v} · modeled elapsed {t:g} ms"
                frames.append(go.Frame(
                    name=f"frame-{idx}",
                    data=[go.Scatter(
                        x=[x], y=[y], mode="markers+text", text=["●"],
                        textposition="top center",
                        marker={"size": 15, "color": "#FFFFFF",
                                "line": {"color": COLORS["active"], "width": 4}},
                        hovertemplate=label + "<extra></extra>",
                    )],
                    traces=[packet_trace_index],
                ))
                labels.append(label)
                idx += 1
            cumulative_ms += link_latency
    fig.frames = frames
    animation_opts = {"frame": {"duration": 110, "redraw": False},
                      "transition": {"duration": 0}, "mode": "immediate", "fromcurrent": True}
    replay_opts = {**animation_opts, "fromcurrent": False}
    slider_steps = [
        {"label": str(round(i * 100 / max(len(frames)-1, 1))) + "%",
         "method": "animate", "args": [[f.name], {"frame": {"duration": 0, "redraw": False},
                                           "mode": "immediate", "transition": {"duration": 0}}]}
        for i, f in enumerate(frames)
        if i == 0 or i == len(frames)-1 or (i % max(1, steps_per_hop // 2) == 0)
    ]
    # Give playback buttons their own row well BELOW the slider and within the
    # plot's bottom margin. Disabling Plotly's active-button styling avoids a
    # washed-out Play button that previously looked disabled.
    fig.update_layout(
        height=620,
        margin={"l": 10, "r": 10, "t": 65, "b": 205},
        updatemenus=[{
            "type": "buttons", "direction": "left", "showactive": False,
            "x": 0.02, "y": -0.36, "xanchor": "left", "yanchor": "top",
            "pad": {"t": 7, "r": 9, "b": 7, "l": 9},
            "buttons": [
                {"label": "▶ Play / Resume", "method": "animate", "args": [None, animation_opts]},
                {"label": "Ⅱ Pause", "method": "animate",
                 "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                   "mode": "immediate", "transition": {"duration": 0}}]},
                {"label": "↺ Replay", "method": "animate", "args": [None, replay_opts]},
            ],
            "font": {"color": "#FFFFFF", "size": 15},
            "bgcolor": "#1D3450", "bordercolor": "#7895B5", "borderwidth": 1,
        }],
        sliders=[{
            "active": 0, "steps": slider_steps, "x": 0.03, "len": 0.94,
            "y": -0.035, "yanchor": "top", "pad": {"t": 17, "b": 3},
            "currentvalue": {"prefix": "Packet progress: ",
                             "font": {"color": COLORS["text"], "size": 13}},
            "tickcolor": COLORS["muted"],
            "font": {"color": "#B8C8DC", "size": 11},
        }],
    )
    return fig


def candidate_bar(rows: list[dict[str, Any]], current_path: str) -> go.Figure:
    fig = go.Figure()
    if rows:
        colors = [COLORS["active"] if r["path"] == current_path else COLORS["visited"] for r in rows]
        fig.add_trace(go.Bar(
            x=[r["total_cost"] for r in rows], y=[r["path"] for r in rows],
            orientation="h", marker_color=colors,
            text=[f"{r['total_cost']:g}" for r in rows], textposition="outside",
            hovertemplate="%{y}<br>Cost: %{x:g} (unitless)<extra></extra>",
        ))
        fig.update_yaxes(autorange="reversed", visible=True, tickfont={"size": 11})
        fig.update_xaxes(visible=True, showgrid=True, gridcolor=COLORS["grid"],
                         title="Sum of routing costs (unitless)", rangemode="tozero")
    else:
        fig.add_annotation(text="No source-to-destination route remains", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
    fig.update_layout(
        title="Candidate route costs · least cost highlighted",
        height=405, paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["panel"],
        font={"color": COLORS["text"], "family": "Arial"},
        margin={"l": 15, "r": 60, "t": 58, "b": 52},
        showlegend=False,
    )
    return fig


def scenario_bars(records: list[dict[str, Any]], metric: str) -> go.Figure:
    labels = {"total_cost": "Total routing cost (unitless)",
              "hops": "Hop count (hops)", "total_latency_ms": "Summed one-way link latency (ms)"}
    valid = [r for r in records if r.get("reachable")]
    fig = go.Figure()
    if valid:
        fig.add_trace(go.Bar(
            x=[r["scenario"] for r in valid], y=[r[metric] for r in valid],
            marker_color=[COLORS["active"] if r["scenario"] == "Baseline" else COLORS["visited"] for r in valid],
            text=[f"{r[metric]:g}" for r in valid], textposition="outside",
            hovertemplate="%{x}<br>%{y:g}<extra></extra>",
        ))
    else:
        fig.add_annotation(text="All selected scenarios are unreachable", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
    fig.update_layout(
        title="Scenario outcomes · unreachable scenarios excluded from numeric bars",
        height=415, paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["panel"],
        font={"color": COLORS["text"], "family": "Arial"},
        xaxis={"title": "Scenario", "showgrid": False},
        yaxis={"title": labels[metric], "gridcolor": COLORS["grid"], "rangemode": "tozero"},
        margin={"l": 55, "r": 20, "t": 63, "b": 70}, showlegend=False,
    )
    return fig