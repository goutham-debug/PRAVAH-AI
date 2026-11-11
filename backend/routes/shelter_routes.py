from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import Shelter, Neighbourhood
from services.shelter_service import shelter_service

shelter_bp = Blueprint('shelters', __name__)

@shelter_bp.route('', methods=['GET'])
def list_shelters():
    session = SessionLocal()
    try:
        shelters = session.query(Shelter).all()
        return jsonify({
            "success": True,
            "total_count": len(shelters),
            "shelters": [s.to_dict() for s in shelters]
        })
    finally:
        session.close()

@shelter_bp.route('/allocate', methods=['POST'])
def allocate_shelters():
    data = request.get_json() or {}
    disruptions = data.get('active_disruptions', [])
    demands = data.get('ward_demands', [])

    session = SessionLocal()
    try:
        db_shelters = session.query(Shelter).all()
        shelters = [s.to_dict() for s in db_shelters]

        if not demands:
            # Generate demand from severe wards if not supplied
            db_nbs = session.query(Neighbourhood).all()
            for nb in db_nbs:
                if nb.hazard_factor >= 60.0:
                    demands.append({
                        "neighbourhood_id": nb.id,
                        "name": nb.name,
                        "demand": int(nb.population * 0.04), # 4% evacuation demand
                        "centroid": [nb.centroid_lon, nb.centroid_lat]
                    })

        allocation_result = shelter_service.allocate_shelters(
            ward_demands=demands,
            shelters=shelters,
            closed_road_ids=disruptions
        )
        return jsonify({"success": True, **allocation_result})
    finally:
        session.close()
