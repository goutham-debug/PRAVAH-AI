import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from database import SessionLocal
from models import IncidentReport, RescueTeam
from services.geo_service import geo_service
from services.graph_service import graph_service

incident_bp = Blueprint('incidents', __name__)

@incident_bp.route('', methods=['GET'])
def list_incidents():
    status = request.args.get('status')
    session = SessionLocal()
    try:
        query = session.query(IncidentReport)
        if status:
            query = query.filter(IncidentReport.status == status)
        incidents = query.order_by(IncidentReport.created_at.desc()).all()
        return jsonify({
            "success": True,
            "total_count": len(incidents),
            "incidents": [i.to_dict() for i in incidents]
        })
    finally:
        session.close()

@incident_bp.route('/<int:incident_id>', methods=['GET'])
def get_incident(incident_id: int):
    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        if not inc:
            return jsonify({"success": False, "error": "Incident report not found."}), 404
        return jsonify({"success": True, "incident": inc.to_dict()})
    finally:
        session.close()

@incident_bp.route('/track/<tracking_id>', methods=['GET'])
def track_incident(tracking_id: str):
    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter(IncidentReport.tracking_id == tracking_id).first()
        if not inc:
            return jsonify({"success": False, "error": "Invalid tracking ID."}), 404
        return jsonify({"success": True, "incident": inc.to_dict()})
    finally:
        session.close()

@incident_bp.route('', methods=['POST'])
def submit_incident():
    data = request.get_json() or {}
    citizen_name = data.get('citizen_name', '').strip()
    phone = data.get('phone', '').strip()
    description = data.get('description', '').strip()
    incident_type = data.get('incident_type', 'WATERLOGGING')
    severity = data.get('severity', 'MODERATE')
    photo_url = data.get('photo_url')
    
    try:
        lat = float(data['lat'])
        lon = float(data['lon'])
    except (KeyError, TypeError, ValueError):
        return jsonify({"success": False, "error": "A valid latitude and longitude are required."}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"success": False, "error": "Coordinates are out of range."}), 400

    if not citizen_name or not phone or not description:
        return jsonify({"success": False, "error": "Citizen name, phone, and detailed description are required."}), 400

    # Geo associate
    nb_info = geo_service.find_neighbourhood_for_point(lat, lon)
    neighbourhood_id = nb_info.get('id') if nb_info else None
    
    # Snap to nearest road intersection
    node_id, _, _ = graph_service.snap_to_nearest_node(lat, lon)

    # Generate unique verifiable tracking ID
    tracking_id = f"PRV-BLR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    session = SessionLocal()
    try:
        new_report = IncidentReport(
            tracking_id=tracking_id,
            user_id=g.current_user.id,
            citizen_name=citizen_name,
            phone=phone,
            lat=lat,
            lon=lon,
            neighbourhood_id=neighbourhood_id,
            nearest_node_id=node_id,
            incident_type=incident_type,
            severity=severity,
            description=description,
            photo_url=photo_url,
            status="PENDING_VERIFICATION", # Notice: Not automatically confirmed emergency!
            authority_notes="Awaiting geospatial confirmation by BBMP field desk.",
            created_at=datetime.utcnow()
        )
        session.add(new_report)
        session.commit()

        return jsonify({
            "success": True,
            "message": "Incident reported successfully. Track status using your reference ID.",
            "tracking_id": tracking_id,
            "incident": new_report.to_dict()
        }), 201
    finally:
        session.close()

@incident_bp.route('/<int:incident_id>/verify', methods=['POST'])
def verify_incident(incident_id: int):
    """Authority verification workflow."""
    data = request.get_json() or {}
    new_status = data.get('status', 'VERIFIED')
    if new_status not in ('UNDER_REVIEW', 'VERIFIED', 'REJECTED', 'RESOLVED'):
        return jsonify({"success": False, "error": "Invalid status."}), 400
    notes = data.get('authority_notes', '')
    assigned_team_id = data.get('assigned_team_id')

    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
        if not inc:
            return jsonify({"success": False, "error": "Incident not found."}), 404

        inc.status = new_status
        if notes:
            inc.authority_notes = notes
        if assigned_team_id:
            inc.assigned_team_id = assigned_team_id
            # Update rescue team status
            team = session.query(RescueTeam).filter(RescueTeam.id == assigned_team_id).first()
            if team:
                team.status = "DISPATCHED"
                team.current_assigned_incident_id = str(inc.id)

        inc.updated_at = datetime.utcnow()
        session.commit()

        return jsonify({
            "success": True,
            "message": f"Incident {inc.tracking_id} updated to {new_status}.",
            "incident": inc.to_dict()
        })
    finally:
        session.close()
