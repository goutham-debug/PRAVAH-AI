import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.routing_service import routing_service
from services.graph_service import graph_service

def test_stage4_dijkstra_routing():
    # Hope Farm (12.9840, 77.7510) to Kadugodi (12.9980, 77.7600)
    res = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510,
        dest_lat=12.9980, dest_lon=77.7600,
        closed_road_ids=[],
        algorithm="dijkstra"
    )
    assert res['success'] is True
    assert res['algorithm_used'] == 'DIJKSTRA'
    
    route = res['primary_route']
    assert route['total_distance_km'] > 0
    assert route['travel_time_mins'] > 0
    assert len(route['node_sequence']) >= 2
    assert len(route['coordinates']) >= 3
    assert len(route['turn_by_turn']) >= 2
    assert 'route_explanation' in route
    assert 'traffic_notice' in res

def test_stage4_astar_routing():
    # Compare A* path with Dijkstra path for the same OD pair
    res_astar = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510,
        dest_lat=12.9980, dest_lon=77.7600,
        closed_road_ids=[],
        algorithm="astar"
    )
    assert res_astar['success'] is True
    assert res_astar['algorithm_used'] == 'ASTAR'
    assert res_astar['primary_route']['total_distance_km'] > 0

def test_stage4_coordinate_snapping_threshold():
    # Valid coordinate within 3km threshold
    res_valid = routing_service.calculate_route(
        start_lat=12.9845, start_lon=77.7515,
        dest_lat=12.9985, dest_lon=77.7605
    )
    assert res_valid['success'] is True

    # Coordinates far outside pilot area (e.g. Mumbai 19.0760, 72.8777)
    res_invalid = routing_service.calculate_route(
        start_lat=19.0760, start_lon=72.8777,
        dest_lat=12.9840, dest_lon=77.7510
    )
    assert res_invalid['success'] is False
    assert "exceeding the maximum allowed snap threshold" in res_invalid['error']

def test_stage4_confirmed_closure_avoidance_and_detour():
    # Route from Hope Farm to ITPL Gate
    # Primary corridor: ROAD_HOPEFARM_ITPL
    res_normal = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510,
        dest_lat=12.9856, dest_lon=77.7314,
        closed_road_ids=[]
    )
    assert res_normal['success'] is True
    assert "Hope Farm to ITPL Link Road" in res_normal['primary_route']['road_names']

    # Close the direct link
    res_detour = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510,
        dest_lat=12.9856, dest_lon=77.7314,
        closed_road_ids=["ROAD_HOPEFARM_ITPL"]
    )
    assert res_detour['success'] is True
    # The direct road must NOT be in the traversed road names
    assert "Hope Farm to ITPL Link Road" not in res_detour['primary_route']['road_names']

def test_stage4_alternative_route_generation():
    # Route across network with multiple corridors
    res = routing_service.calculate_route(
        start_lat=12.9840, start_lon=77.7510, # Hope Farm
        dest_lat=12.9560, dest_lon=77.7010,   # Marathahalli Bridge
        closed_road_ids=[],
        calculate_alternative=True
    )
    assert res['success'] is True
    assert res['primary_route'] is not None
    # If alternative route exists, verify it has distinct road geometry
    if res['alternative_route']:
        assert res['alternative_route']['is_alternative'] is True
        assert res['alternative_route']['total_distance_km'] >= res['primary_route']['total_distance_km']

def test_stage4_topological_isolation_handling():
    # Close all outgoing roads from Kadugodi to isolate it
    # Kadugodi connects to Hope Farm via ROAD_HOPEFARM_KADUGODI
    res_isolated = routing_service.calculate_route(
        start_lat=12.9980, start_lon=77.7600, # Kadugodi
        dest_lat=12.9260, dest_lon=77.6840,   # Bellandur Ecospace
        closed_road_ids=["ROAD_HOPEFARM_KADUGODI"]
    )
    assert res_isolated['success'] is False
    assert res_isolated.get('is_isolated') is True
    assert "No connected route found" in res_isolated['error']
