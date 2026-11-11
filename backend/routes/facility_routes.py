from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import Facility, Neighbourhood
from services.facility_service import facility_service

facility_bp = Blueprint('facilities', __name__)

@facility_bp.route('/accessibility', methods=['POST'])
def get_accessibility():
    data = request.get_json() or {}
    disruptions = data.get('active_disruptions', [])

    session = SessionLocal()
    try:
        db_facs = session.query(Facility).all()
        db_nbs = session.query(Neighbourhood).all()
        
        facs = [f.to_dict() for f in db_facs]
        nbs = [n.to_dict() for n in db_nbs]

        result = facility_service.evaluate_accessibility(
            facilities=facs,
            neighbourhoods=nbs,
            closed_road_ids=disruptions
        )
        return jsonify({"success": True, **result})
    finally:
        session.close()
