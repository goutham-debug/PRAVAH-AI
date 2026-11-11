from flask import Blueprint, request, jsonify, Response
from services.scenario_service import scenario_service
from services.situation_report_service import situation_report_service

sitrep_bp = Blueprint('sitrep', __name__)

@sitrep_bp.route('/generate', methods=['POST'])
def generate_report():
    data = request.get_json() or {}
    rainfall = data.get('rainfall_scenario', 'HEAVY')
    disruptions = data.get('active_disruptions', [])

    scenario_res = scenario_service.run_simulation(
        rainfall_scenario=rainfall,
        closed_road_ids=disruptions,
        scenario_name="Ad-hoc Situation Assessment"
    )
    sitrep = situation_report_service.generate_sitrep(scenario_res)
    return jsonify({"success": True, "situation_report": sitrep})

@sitrep_bp.route('/export/markdown', methods=['POST'])
def export_markdown():
    data = request.get_json() or {}
    sitrep = data.get('situation_report', {})
    md_content = sitrep.get('markdown_content', '# PRAVAH AI Situation Report\nNo data supplied.')
    
    return Response(
        md_content,
        mimetype="text/markdown",
        headers={"Content-disposition": "attachment; filename=PRAVAH_AI_SITREP.md"}
    )
