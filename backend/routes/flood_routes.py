from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import Neighbourhood
from services.flood_engine import flood_engine

flood_bp = Blueprint('flood', __name__)

@flood_bp.route('/assess', methods=['POST'])
def assess_flood_risk():
    """
    Executes explainable flood susceptibility screening across monitored wards.
    Formula: R = 0.35P + 0.20E + 0.25H + 0.20D
    """
    data = request.get_json(silent=True) or {}
    rainfall_scenario = data.get('rainfall_scenario', 'HEAVY')
    observed_rainfall_mm = data.get('rainfall_mm')
    disruptions = data.get('active_disruptions', [])

    if observed_rainfall_mm is not None:
        try:
            observed_rainfall_mm = float(observed_rainfall_mm)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "rainfall_mm must be a numeric value."}), 400

    session = SessionLocal()
    try:
        db_nbs = session.query(Neighbourhood).all()
        nbs = [n.to_dict() for n in db_nbs]
        results = flood_engine.assess_neighbourhoods(
            neighbourhoods=nbs,
            rainfall_scenario=rainfall_scenario,
            active_disruptions=disruptions,
            observed_rainfall_mm=observed_rainfall_mm
        )
        return jsonify({
            "success": True,
            "rainfall_scenario": rainfall_scenario,
            "observed_rainfall_mm": observed_rainfall_mm,
            "assumptions": flood_engine.RAINFALL_PRESETS.get(rainfall_scenario, {}),
            "neighbourhoods_assessed_count": len(results),
            "formula": "R = 0.35P + 0.20E + 0.25H + 0.20D",
            "data_sources": flood_engine.DATA_SOURCES,
            "results": results
        })
    finally:
        session.close()

@flood_bp.route('/formula', methods=['GET'])
def get_formula_metadata():
    """Returns methodology documentation, weights justification, and limitations."""
    return jsonify({
        "success": True,
        **flood_engine.get_methodology_metadata()
    })
