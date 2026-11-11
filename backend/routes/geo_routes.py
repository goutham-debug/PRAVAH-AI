from flask import Blueprint, jsonify
from services.geo_service import geo_service
from database import SessionLocal
from models import Neighbourhood, Facility

geo_bp = Blueprint('geo', __name__)

@geo_bp.route('/neighbourhoods/geojson', methods=['GET'])
def get_neighbourhoods_geojson():
    return jsonify(geo_service.get_neighbourhoods_geojson())

@geo_bp.route('/neighbourhoods', methods=['GET'])
def list_neighbourhoods():
    session = SessionLocal()
    try:
        nbs = session.query(Neighbourhood).all()
        return jsonify({
            "success": True,
            "total_count": len(nbs),
            "neighbourhoods": [n.to_dict() for n in nbs]
        })
    finally:
        session.close()

@geo_bp.route('/facilities', methods=['GET'])
def list_facilities():
    session = SessionLocal()
    try:
        facs = session.query(Facility).all()
        return jsonify({
            "success": True,
            "total_count": len(facs),
            "facilities": [f.to_dict() for f in facs]
        })
    finally:
        session.close()

@geo_bp.route('/boundaries/analysis', methods=['GET'])
def analyze_boundaries():
    """
    GeoPandas geometric analysis: polygon area (sq km), perimeter, and validation.
    """
    results = geo_service.analyze_neighbourhood_boundaries()
    return jsonify({
        "success": True,
        "ward_count": len(results),
        "boundaries": results
    })

@geo_bp.route('/water-bodies/proximity', methods=['GET'])
def analyze_water_proximity():
    """
    Shapely spatial buffer and intersection analysis with lake catchment zones.
    """
    analysis = geo_service.analyze_water_body_proximity(buffer_meters=350.0)
    return jsonify({
        "success": True,
        **analysis
    })
