import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.graph_service import graph_service
from services.routing_service import routing_service

def test_graph_initialization():
    nodes = graph_service.get_all_nodes()
    roads = graph_service.get_all_roads()
    assert len(nodes) >= 10
    assert len(roads) >= 15
    G = graph_service.get_baseline_graph()
    assert G.number_of_nodes() == len(nodes)

def test_snap_to_nearest_node():
    # Coordinates of Hope Farm Junction (12.9840, 77.7510)
    node_id, dist, data = graph_service.snap_to_nearest_node(12.9840, 77.7510)
    assert node_id == "N_HOPE_FARM"
    assert dist < 0.1

def test_routing_closure_avoidance():
    # Route from Hope Farm to ITPL Gate
    # Baseline: direct road ROAD_HOPEFARM_ITPL exists
    res_open = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510, # Hope Farm
        dest_lat=12.9856, dest_lon=77.7314,   # ITPL
        closed_road_ids=[]
    )
    assert res_open['success'] is True
    assert "N_ITPL_GATE" in res_open['primary_route']['node_sequence']

    # Now close ROAD_HOPEFARM_ITPL
    res_closed = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510,
        dest_lat=12.9856, dest_lon=77.7314,
        closed_road_ids=["ROAD_HOPEFARM_ITPL"]
    )
    assert res_closed['success'] is True
    # Should still find a detour route or alternative link
    assert "ROAD_HOPEFARM_ITPL" not in res_closed['primary_route']['road_names']
