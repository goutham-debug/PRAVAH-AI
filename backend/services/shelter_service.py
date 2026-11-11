from typing import Dict, Any, List, Optional
import networkx as nx
from services.graph_service import graph_service

class ShelterService:
    def __init__(self):
        pass

    def allocate_shelters(
        self,
        ward_demands: List[Dict[str, Any]], # [{"neighbourhood_id": "...", "name": "...", "demand": 450, "centroid": [lon, lat]}]
        shelters: List[Dict[str, Any]],
        closed_road_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Solves capacity-constrained shelter allocation using min-cost flow graph or optimal greedy matching.
        Hard constraint: No shelter ever exceeds its remaining capacity!
        """
        G_road = graph_service.get_scenario_graph(closed_road_ids)
        
        # Track shelter remaining capacity
        shelter_state = {}
        for s in shelters:
            avail = max(0, s.get('total_capacity', 500) - s.get('current_occupancy', 0))
            shelter_state[s['id']] = {
                "id": s['id'],
                "name": s['name'],
                "nearest_node_id": s.get('nearest_node_id'),
                "total_capacity": s.get('total_capacity', 500),
                "remaining_capacity": avail,
                "assigned_count": 0,
                "assignments": []
            }

        assignments = []
        unmet_demand_records = []
        total_evacuation_demand = 0
        total_allocated = 0
        total_unreachable = 0
        total_unmet = 0

        # Build transportation cost matrix between each ward demand and each shelter
        for req in ward_demands:
            ward_id = req['neighbourhood_id']
            ward_name = req['name']
            demand = int(req.get('demand', 0))
            centroid = req.get('centroid', [77.7499, 12.9698])
            
            total_evacuation_demand += demand
            if demand <= 0:
                continue

            ward_node, _, _ = graph_service.snap_to_nearest_node(centroid[1], centroid[0])
            
            # Find candidate shelters reachable from this ward
            candidate_shelters = []
            for s_id, s_data in shelter_state.items():
                target_node = s_data['nearest_node_id']
                if ward_node and target_node and nx.has_path(G_road, ward_node, target_node):
                    try:
                        dist_km = nx.dijkstra_path_length(G_road, ward_node, target_node, weight='weight')
                        candidate_shelters.append({
                            "shelter_id": s_id,
                            "shelter_name": s_data['name'],
                            "distance_km": round(dist_km, 2),
                            "travel_mins": round((dist_km / 30.0) * 60, 1),
                            "available_cap": s_data['remaining_capacity']
                        })
                    except Exception:
                        pass

            # Sort shelters by shortest distance/travel cost
            candidate_shelters.sort(key=lambda x: x['distance_km'])

            remaining_demand_to_place = demand
            
            if not candidate_shelters:
                total_unreachable += demand
                unmet_demand_records.append({
                    "neighbourhood_id": ward_id,
                    "name": ward_name,
                    "unmet_count": demand,
                    "reason": "Completely disconnected by road disruptions. No operational shelter reachable."
                })
                continue

            for cand in candidate_shelters:
                s_id = cand['shelter_id']
                s_obj = shelter_state[s_id]
                avail = s_obj['remaining_capacity']
                
                if avail <= 0:
                    continue
                    
                alloc_amount = min(remaining_demand_to_place, avail)
                
                s_obj['remaining_capacity'] -= alloc_amount
                s_obj['assigned_count'] += alloc_amount
                remaining_demand_to_place -= alloc_amount
                total_allocated += alloc_amount
                
                assignment_entry = {
                    "neighbourhood_id": ward_id,
                    "neighbourhood_name": ward_name,
                    "shelter_id": s_id,
                    "shelter_name": s_obj['name'],
                    "allocated_population": alloc_amount,
                    "travel_distance_km": cand['distance_km'],
                    "travel_time_mins": cand['travel_mins']
                }
                assignments.append(assignment_entry)
                s_obj['assignments'].append(assignment_entry)
                
                if remaining_demand_to_place <= 0:
                    break

            if remaining_demand_to_place > 0:
                total_unmet += remaining_demand_to_place
                unmet_demand_records.append({
                    "neighbourhood_id": ward_id,
                    "name": ward_name,
                    "unmet_count": remaining_demand_to_place,
                    "reason": "Reachable regional shelters exhausted total capacity limit."
                })

        # Calculate overall shelter capacity summary
        total_capacity_available = sum(s.get('total_capacity', 0) for s in shelters)
        remaining_system_capacity = sum(s_data['remaining_capacity'] for s_data in shelter_state.values())

        return {
            "total_evacuation_demand": total_evacuation_demand,
            "total_allocated_population": total_allocated,
            "total_unmet_demand": total_unmet,
            "total_unreachable_demand": total_unreachable,
            "allocation_fulfillment_pct": round((total_allocated / max(1, total_evacuation_demand)) * 100, 1),
            "total_shelter_capacity": total_capacity_available,
            "remaining_shelter_capacity": remaining_system_capacity,
            "shelter_utilization_pct": round(((total_capacity_available - remaining_system_capacity) / max(1, total_capacity_available)) * 100, 1),
            "assignments": assignments,
            "shelter_status": list(shelter_state.values()),
            "unmet_records": unmet_demand_records,
            "active_disruptions": closed_road_ids or []
        }

# Singleton instance
shelter_service = ShelterService()
