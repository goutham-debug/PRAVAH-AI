from flask import Blueprint, jsonify, request
from services.graph_service import graph_service
from services.routing_service import routing_service

road_bp = Blueprint('roads', __name__)

@road_bp.route('/topology', methods=['GET'])
def get_road_topology():
    """Returns complete directed graph topology with nodes and edges."""
    nodes = graph_service.get_all_nodes()
    edges = graph_service.get_all_roads()
    return jsonify({
        "success": True,
        "zone": "Whitefield-Mahadevapura, Bengaluru",
        "verification_status": "UNVERIFIED",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges
    })

@road_bp.route('/critical-links', methods=['GET'])
def get_critical_links():
    """
    Identifies and ranks critical road links using:
    - Bridge analysis
    - Edge betweenness centrality
    - Topographic depression hazard
    """
    critical_links = graph_service.identify_critical_road_links()
    return jsonify({
        "success": True,
        "critical_link_count": len(critical_links),
        "critical_links": critical_links
    })

@road_bp.route('/network-analysis', methods=['GET'])
def get_network_analysis():
    """
    Computes graph connectivity metrics:
    - Connected components
    - Articulation points (critical junctions)
    - Bridge edges (critical corridors)
    - Network integrity percentage
    """
    conn = graph_service.analyze_connectivity()
    return jsonify({
        "success": True,
        "connectivity": conn
    })

@road_bp.route('/closure-impact', methods=['POST'])
def evaluate_closure_impact():
    """
    Simulates the topological impact of specific road closures on network connectivity.
    """
    data = request.get_json(silent=True) or {}
    closed_roads = data.get('closed_roads', [])
    if not isinstance(closed_roads, list):
        return jsonify({"success": False, "error": "closed_roads must be a list of road IDs."}), 400

    impact = graph_service.evaluate_road_closure_impact(closed_roads)
    return jsonify({
        "success": True,
        **impact
    })

@road_bp.route('/route', methods=['POST'])
def plan_route():
    """
    Plans shortest transit / evacuation route using Dijkstra or A*.
    Excludes confirmed closed roads and respects one-way restrictions.
    """
    data = request.get_json(silent=True) or {}
    try:
        start_lat = float(data['start_lat'])
        start_lon = float(data['start_lon'])
        dest_lat = float(data['dest_lat'])
        dest_lon = float(data['dest_lon'])
    except (KeyError, TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "start_lat, start_lon, dest_lat and dest_lon are required numeric coordinates."
        }), 400

    closed = data.get('avoid_roads') or []
    if not isinstance(closed, list):
        return jsonify({"success": False, "error": "avoid_roads must be a list."}), 400

    algorithm = data.get('algorithm', 'dijkstra').lower()
    if algorithm not in ['dijkstra', 'astar']:
        algorithm = 'dijkstra'

    return jsonify(routing_service.calculate_route(
        start_lat=start_lat,
        start_lon=start_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        closed_road_ids=closed,
        algorithm=algorithm,
        calculate_alternative=True
    ))
