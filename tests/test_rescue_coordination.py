import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.rescue_service import rescue_service

def test_rescue_coordination_matching():
    incidents = [
        {"id": 1, "tracking_id": "T1", "incident_type": "WATERLOGGING", "severity": "SEVERE", "lat": 12.9520, "lon": 77.7410, "status": "VERIFIED"},
        {"id": 2, "tracking_id": "T2", "incident_type": "ROAD_BLOCK", "severity": "MODERATE", "lat": 12.9840, "lon": 77.7510, "status": "VERIFIED"}
    ]
    teams = [
        {"id": "TEAM_BOAT", "name": "Boat Squad", "type": "BOAT_RESCUE", "status": "AVAILABLE", "base_lat": 12.9980, "base_lon": 77.7600, "nearest_node_id": "N_KADUGODI_TREE"},
        {"id": "TEAM_PUMP", "name": "Pump Squad", "type": "DEWATERING_PUMP", "status": "AVAILABLE", "base_lat": 12.9880, "base_lon": 77.6890, "nearest_node_id": "N_MAHADEVAPURA_FLYOVER"}
    ]

    result = rescue_service.coordinate_rescue_assignments(incidents, teams, closed_road_ids=[])
    assert result['dispatched_count'] >= 1
    # Check no duplicate team assignments
    assigned_ids = [a['assigned_team_id'] for a in result['assignments']]
    assert len(assigned_ids) == len(set(assigned_ids))
