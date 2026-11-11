from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import RescueTeam, IncidentReport
from services.rescue_service import rescue_service

rescue_bp = Blueprint('rescue', __name__)

@rescue_bp.route('/teams', methods=['GET'])
def list_teams():
    session = SessionLocal()
    try:
        teams = session.query(RescueTeam).all()
        return jsonify({
            "success": True,
            "total_count": len(teams),
            "teams": [t.to_dict() for t in teams]
        })
    finally:
        session.close()

@rescue_bp.route('/coordinate', methods=['POST'])
def coordinate_rescue():
    data = request.get_json() or {}
    disruptions = data.get('active_disruptions', [])

    session = SessionLocal()
    try:
        db_teams = session.query(RescueTeam).all()
        db_incidents = session.query(IncidentReport).all()

        teams = [t.to_dict() for t in db_teams]
        incidents = [i.to_dict() for i in db_incidents]

        coord_result = rescue_service.coordinate_rescue_assignments(
            incident_reports=incidents,
            rescue_teams=teams,
            closed_road_ids=disruptions
        )
        return jsonify({"success": True, **coord_result})
    finally:
        session.close()

@rescue_bp.route('/teams/<team_id>/status', methods=['POST'])
def update_team_status(team_id: str):
    data = request.get_json() or {}
    new_status = data.get('status', 'AVAILABLE') # 'AVAILABLE', 'DISPATCHED', 'MAINTENANCE'

    session = SessionLocal()
    try:
        team = session.query(RescueTeam).filter(RescueTeam.id == team_id).first()
        if not team:
            return jsonify({"success": False, "error": "Team not found."}), 404

        team.status = new_status
        if new_status == 'AVAILABLE':
            team.current_assigned_incident_id = None
        session.commit()
        return jsonify({"success": True, "team": team.to_dict()})
    finally:
        session.close()
