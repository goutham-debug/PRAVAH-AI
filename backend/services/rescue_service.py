from typing import Dict, Any, List, Optional
import networkx as nx
from services.graph_service import graph_service

class RescueService:
    def __init__(self):
        pass

    def coordinate_rescue_assignments(
        self,
        incident_reports: List[Dict[str, Any]],
        rescue_teams: List[Dict[str, Any]],
        closed_road_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Coordinates and assigns available emergency rescue teams to open incidents.
        Prioritizes:
        1. Severity (SEVERE > HIGH > MODERATE > LOW)
        2. Incident capability match (e.g. STRANDED_PERSONS / WATERLOGGING -> BOAT_RESCUE, DRAIN_OVERFLOW -> DEWATERING_PUMP, Medical -> MEDICAL_EVAC)
        3. Reachability on current road network and shortest response distance.
        Enforces NO DUPLICATE team assignment.
        """
        G = graph_service.get_scenario_graph(closed_road_ids)

        # Severity weights
        severity_rank = {
            "SEVERE": 4,
            "HIGH": 3,
            "MODERATE": 2,
            "LOW": 1
        }

        # Filter actionable incidents
        actionable_incidents = [
            inc for inc in incident_reports 
            if inc.get('status') in ['PENDING_VERIFICATION', 'VERIFIED']
        ]
        
        # Sort by severity descending
        actionable_incidents.sort(
            key=lambda x: severity_rank.get(x.get('severity', 'MODERATE'), 1), 
            reverse=True
        )

        # Available teams pool
        available_teams = [
            dict(team) for team in rescue_teams 
            if team.get('status') == 'AVAILABLE'
        ]
        
        assigned_team_ids = set()
        matched_assignments = []
        unassigned_incidents = []

        for incident in actionable_incidents:
            inc_id = incident.get('id')
            inc_type = incident.get('incident_type')
            inc_sev = incident.get('severity')
            inc_lat = incident.get('lat')
            inc_lon = incident.get('lon')

            inc_node, _, _ = graph_service.snap_to_nearest_node(inc_lat, inc_lon)
            
            best_team = None
            min_response_time_mins = float('inf')
            best_distance_km = 0.0

            # Find best candidate team
            for team in available_teams:
                t_id = team.get('id')
                if t_id in assigned_team_ids:
                    continue

                t_node = team.get('nearest_node_id')
                t_type = team.get('type')

                # Capability match scoring
                has_match = False
                if inc_type in ['STRANDED_PERSONS', 'WATERLOGGING'] and t_type == 'BOAT_RESCUE':
                    has_match = True
                elif inc_type in ['DRAIN_OVERFLOW', 'ROAD_BLOCK'] and t_type == 'DEWATERING_PUMP':
                    has_match = True
                elif inc_type in ['STRANDED_PERSONS'] and t_type == 'MEDICAL_EVAC':
                    has_match = True
                elif t_type == 'SEARCH_AND_RESCUE':
                    has_match = True # Universal fallback

                # Check road connectivity from team base to incident
                is_reachable = False
                dist_km = 0.0
                
                if inc_node and t_node and nx.has_path(G, t_node, inc_node):
                    try:
                        dist_km = nx.dijkstra_path_length(G, t_node, inc_node, weight='weight')
                        is_reachable = True
                    except Exception:
                        is_reachable = False
                elif t_type == 'BOAT_RESCUE':
                    # Aquatic boat units can deploy through flooded waterlogged zones if road is cut!
                    dist_km = 3.5 # Flat deployment distance
                    is_reachable = True

                if is_reachable:
                    # Speed: 35 km/h for emergency response
                    response_mins = round((dist_km / 35.0) * 60, 1)
                    
                    # Preference bonus if exact capability match
                    score = response_mins - (15.0 if has_match else 0.0)
                    
                    if score < min_response_time_mins:
                        min_response_time_mins = score
                        best_distance_km = round(dist_km, 2)
                        best_team = team

            if best_team:
                assigned_team_ids.add(best_team['id'])
                assignment = {
                    "incident_id": inc_id,
                    "tracking_id": incident.get('tracking_id'),
                    "incident_type": inc_type,
                    "severity": inc_sev,
                    "location_description": incident.get('description'),
                    "citizen_name": incident.get('citizen_name'),
                    "assigned_team_id": best_team['id'],
                    "assigned_team_name": best_team['name'],
                    "team_type": best_team['type'],
                    "contact_commander": best_team.get('contact_commander'),
                    "phone": best_team.get('phone'),
                    "estimated_arrival_mins": max(8.0, round(best_distance_km / 35.0 * 60, 1)),
                    "response_distance_km": best_distance_km,
                    "status": "DISPATCHED"
                }
                matched_assignments.append(assignment)
            else:
                unassigned_incidents.append({
                    "incident_id": inc_id,
                    "tracking_id": incident.get('tracking_id'),
                    "incident_type": inc_type,
                    "severity": inc_sev,
                    "description": incident.get('description'),
                    "reason": "All matching rescue teams currently dispatched or location completely unreachable by land."
                })

        return {
            "total_incidents_evaluated": len(actionable_incidents),
            "dispatched_count": len(matched_assignments),
            "unassigned_count": len(unassigned_incidents),
            "coverage_rate_pct": round((len(matched_assignments) / max(1, len(actionable_incidents))) * 100, 1),
            "assignments": matched_assignments,
            "unassigned_incidents": unassigned_incidents,
            "available_rescue_teams_count": len(rescue_teams),
            "remaining_idle_teams_count": len(rescue_teams) - len(assigned_team_ids),
            "notice": "Assignment recommendations only. Dispatch requires officer confirmation."
        }

# Singleton instance
rescue_service = RescueService()
