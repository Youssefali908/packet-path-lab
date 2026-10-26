"""Figure serialization smoke tests (no browser or Streamlit needed)."""

from routing_model import baseline_edges, compute_route, preset_edges, candidate_routes
from visualizations import network_figure, animation_figure, candidate_bar, scenario_bars


def test_all_six_charts_serialize():
    edges = baseline_edges()
    route = compute_route(edges, "A", "F")
    figures = [
        network_figure(edges, route.path, "A", "F"),
        animation_figure(edges, route.path, "A", "F"),
        candidate_bar(candidate_routes(edges, "A", "F"), route.path_label),
        network_figure(edges, route.path, "A", "F", settled=["A"], frontier=["C"]),
        network_figure(preset_edges("E–F link failure"), ("A", "C", "E", "D", "F"), "A", "F"),
        scenario_bars([compute_route(preset_edges(s), "A", "F").as_record(s)
                       for s in ("Baseline", "E–F link failure", "A disconnected")], "total_cost"),
    ]
    assert all("data" in fig.to_json() and len(fig.data) > 0 for fig in figures)
    assert len(figures[1].frames) > 12  # actually animated, not decorative static plot


def test_no_route_or_one_node_packet_figures_render():
    edges = preset_edges("A disconnected")
    no_path = compute_route(edges, "A", "F")
    assert not no_path.reachable
    assert "data" in network_figure(edges, (), "A", "F").to_json()
    same = compute_route(edges, "A", "A")
    assert len(animation_figure(edges, same.path, "A", "A").frames) == 1
    assert "data" in candidate_bar([], "No route available").to_json()


def test_packet_playback_buttons_do_not_overlap_timeline():
    """Protect against the original crowded/washed-out Play button layout."""
    edges = baseline_edges()
    route = compute_route(edges, "A", "F")
    fig = animation_figure(edges, route.path, "A", "F")
    controls = fig.layout.updatemenus[0]
    timeline = fig.layout.sliders[0]
    assert fig.layout.margin.b >= 170
    assert controls.y < timeline.y - 0.25  # separate lower control row
    assert controls.showactive is False  # active state must not fade the Play text
    assert controls.font.size >= 14
    assert [button.label for button in controls.buttons] == [
        "▶ Play / Resume", "Ⅱ Pause", "↺ Replay"
    ]
    assert controls.buttons[0].args[1]["fromcurrent"] is True
    assert controls.buttons[2].args[1]["fromcurrent"] is False