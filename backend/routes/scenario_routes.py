from flask import Blueprint, request, jsonify
from services.scenario_service import scenario_service
from services.graph_service import graph_service

scenario_bp = Blueprint('scenarios', __name__)

@scenario_bp.route('/simulate', methods=['POST'])
def run_simulation():
    data = request.get_json() or {}
    rainfall_scenario = data.get('rainfall_scenario', 'HEAVY')
    disruptions = data.get('active_disruptions', [])
    name = data.get('scenario_name', 'Interactive Authority Simulation')

    result = scenario_service.run_simulation(
        rainfall_scenario=rainfall_scenario,
        closed_road_ids=disruptions,
        scenario_name=name
    )
    return jsonify({
        "success": True,
        "scenario": result
    })

@scenario_bp.route('/compare', methods=['POST'])
def compare():
    data = request.get_json(silent=True) or {}
    closed = data.get('closed_road_ids') or []
    if not isinstance(closed, list) or not closed:
        return jsonify({"success": False, "error": "Select at least one road closure to compare."}), 400
    known = {r['id'] for r in graph_service.get_all_roads()}
    unknown = [c for c in closed + (data.get('restored_road_ids') or []) if c not in known]
    if unknown:
        return jsonify({"success": False, "error": f"Unknown road ids: {unknown}"}), 400
    comparison = scenario_service.compare_scenarios(
        data.get('rainfall_scenario', 'HEAVY'), closed, data.get('restored_road_ids') or [])
    return jsonify({"success": True, **comparison})


@scenario_bp.route('/candidate-disruptions', methods=['GET'])
def get_candidate_disruptions():
    all_roads = graph_service.get_all_roads()
    candidate_roads = []
    for r in all_roads:
        candidate_roads.append({
            "id": r['id'],
            "name": r['name'],
            "source": r['source'],
            "target": r['target'],
            "length_km": r['length_km'],
            "base_flood_risk": r['base_flood_risk'],
            "elevation_risk_score": r.get('elevation_risk_score', 50),
            "is_critical": r.get('is_critical', False)
        })
    return jsonify({
        "success": True,
        "candidate_roads": candidate_roads
    })
