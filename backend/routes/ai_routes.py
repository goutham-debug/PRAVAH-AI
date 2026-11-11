from flask import Blueprint, request, jsonify
from services.ai_service import ai_assistant_service

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/query', methods=['POST'])
def query_ai():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"success": False, "error": "Question parameter is required."}), 400

    assessment_id = data.get('assessment_id')
    rainfall_scenario = data.get('rainfall_scenario', 'HEAVY')
    closed_road_ids = data.get('closed_road_ids', [])

    try:
        response = ai_assistant_service.answer_query(
            question=question,
            assessment_id=assessment_id,
            rainfall_scenario=rainfall_scenario,
            closed_road_ids=closed_road_ids
        )
        return jsonify({"success": True, **response})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to synthesize response: {str(e)}"
        }), 500
