from flask import Blueprint, jsonify
from sqlalchemy import func

from config import Config
from database import SessionLocal
from models import Neighbourhood, Facility, Shelter, RescueTeam
from services.graph_service import graph_service

system_bp = Blueprint('system', __name__)


@system_bp.route('/status', methods=['GET'])
def status():
    """Read-only data availability summary for the operator header. Counts come from the database."""
    session = SessionLocal()
    try:
        counts = {
            "neighbourhoods": session.query(func.count(Neighbourhood.id)).scalar(),
            "facilities": session.query(func.count(Facility.id)).scalar(),
            "shelters": session.query(func.count(Shelter.id)).scalar(),
            "response_teams": session.query(func.count(RescueTeam.id)).scalar(),
        }
        unverified = (
            session.query(func.count(Neighbourhood.id)).filter(Neighbourhood.verification_status != 'VERIFIED').scalar()
            + session.query(func.count(Facility.id)).filter(Facility.verification_status != 'VERIFIED').scalar()
        )
    finally:
        session.close()
    return jsonify({
        "success": True,
        "zone": Config.PILOT_ZONE,
        "counts": counts,
        "road_network": {
            "nodes": graph_service.baseline_graph.number_of_nodes(),
            "edges": graph_service.baseline_graph.number_of_edges(),
            "status": "UNVERIFIED" if graph_service.baseline_graph.number_of_nodes() else "UNAVAILABLE",
        },
        "unverified_records": unverified,
        "dataset_status": "UNVERIFIED" if (unverified or graph_service.baseline_graph.number_of_nodes()) else "UNAVAILABLE",
    })
