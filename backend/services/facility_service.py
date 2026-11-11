"""
PRAVAH AI — Stage 3: Critical Healthcare Facility Accessibility & Dependency Engine

Analyzes network accessibility from all monitored administrative wards to:
- Level-1 / Level-2 Tertiary Trauma Hospitals (Vydehi, Sakra)
- Regional General Hospitals & Clinics
- Emergency First Responder Stations (Fire, Police)

Features:
- Dijkstra network transit times and distances
- Critical facility dependency analysis (identifying roads whose loss cuts off hospital access)
- Ward trauma care isolation warnings
- Detailed explainability per facility and ward
"""

from typing import Dict, Any, List, Optional
import networkx as nx
from services.graph_service import graph_service

class FacilityService:
    def __init__(self):
        pass

    def evaluate_accessibility(
        self,
        facilities: List[Dict[str, Any]],
        neighbourhoods: List[Dict[str, Any]],
        closed_road_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates network accessibility from every neighbourhood centroid to every facility.
        Detects unreachable facilities, wards losing trauma care, and critical access roads.
        """
        G = graph_service.get_scenario_graph(closed_road_ids)
        closed_set = set(closed_road_ids or [])

        facility_status = []
        neighbourhood_access = {}

        # Initialize neighbourhood tracking
        for nb in neighbourhoods:
            neighbourhood_access[nb['id']] = {
                "neighbourhood_id": nb['id'],
                "name": nb['name'],
                "accessible_hospitals": 0,
                "accessible_trauma_centres": 0,
                "accessible_fire_stations": 0,
                "accessible_police_stations": 0,
                "nearest_hospital_mins": None,
                "nearest_hospital_name": None,
                "nearest_hospital_dist_km": None,
                "nearest_trauma_mins": None,
                "nearest_trauma_name": None,
                "is_completely_isolated": True
            }

        total_facilities = len(facilities)
        reachable_count = 0
        unreachable_count = 0

        # Track facility-dependent road links
        road_facility_dependencies: Dict[str, List[str]] = {}

        for fac in facilities:
            target_node = fac.get('nearest_node_id')
            fac_type = fac.get('type')
            is_trauma = fac.get('subtype') == 'TERTIARY_TRAUMA'

            reachable_from_wards = []
            min_travel_mins = float('inf')
            closest_ward_name = None

            for nb in neighbourhoods:
                centroid = nb.get('centroid', [77.7499, 12.9698])
                nb_node, _, _ = graph_service.snap_to_nearest_node(centroid[1], centroid[0])

                if not nb_node or not target_node:
                    continue

                if nx.has_path(G, nb_node, target_node):
                    try:
                        travel_dist = nx.dijkstra_path_length(G, nb_node, target_node, weight='weight')
                        path_nodes = nx.dijkstra_path(G, nb_node, target_node, weight='weight')

                        # Track edges traversed on this access route
                        for i in range(len(path_nodes) - 1):
                            u, v = path_nodes[i], path_nodes[i+1]
                            edge_info = G.get_edge_data(u, v) or {}
                            rid = edge_info.get('id')
                            if rid:
                                if rid not in road_facility_dependencies:
                                    road_facility_dependencies[rid] = []
                                fac_label = f"{fac.get('name')} (from {nb.get('name')})"
                                if fac_label not in road_facility_dependencies[rid]:
                                    road_facility_dependencies[rid].append(fac_label)

                        # Flood emergency transit speed: ~25 km/h
                        travel_mins = round((travel_dist / 25.0) * 60, 1)
                        reachable_from_wards.append({
                            "ward_id": nb['id'],
                            "ward_name": nb['name'],
                            "travel_dist_km": round(travel_dist, 2),
                            "travel_mins": travel_mins
                        })

                        # Update neighbourhood record
                        nb_record = neighbourhood_access[nb['id']]
                        nb_record["is_completely_isolated"] = False

                        if fac_type == 'HOSPITAL':
                            nb_record["accessible_hospitals"] += 1
                            if is_trauma:
                                nb_record["accessible_trauma_centres"] += 1
                                if nb_record["nearest_trauma_mins"] is None or travel_mins < nb_record["nearest_trauma_mins"]:
                                    nb_record["nearest_trauma_mins"] = travel_mins
                                    nb_record["nearest_trauma_name"] = fac.get('name')

                            if nb_record["nearest_hospital_mins"] is None or travel_mins < nb_record["nearest_hospital_mins"]:
                                nb_record["nearest_hospital_mins"] = travel_mins
                                nb_record["nearest_hospital_dist_km"] = round(travel_dist, 2)
                                nb_record["nearest_hospital_name"] = fac.get('name')
                        elif fac_type == 'FIRE_STATION':
                            nb_record["accessible_fire_stations"] += 1
                        elif fac_type == 'POLICE_STATION':
                            nb_record["accessible_police_stations"] += 1

                        if travel_mins < min_travel_mins:
                            min_travel_mins = travel_mins
                            closest_ward_name = nb['name']
                    except Exception:
                        pass

            is_accessible = len(reachable_from_wards) > 0
            if is_accessible:
                reachable_count += 1
            else:
                unreachable_count += 1

            facility_status.append({
                "facility_id": fac.get('id'),
                "name": fac.get('name'),
                "type": fac.get('type'),
                "subtype": fac.get('subtype'),
                "lat": fac.get('lat'),
                "lon": fac.get('lon'),
                "nearest_node_id": target_node,
                "is_network_accessible": is_accessible,
                "connected_wards_count": len(reachable_from_wards),
                "total_wards_count": len(neighbourhoods),
                "min_travel_time_mins": min_travel_mins if min_travel_mins != float('inf') else None,
                "closest_accessible_ward": closest_ward_name,
                "operational_status": fac.get('operational_status', 'OPERATIONAL'),
                "has_emergency_ward": fac.get('has_emergency_ward', False),
                "capacity_beds": fac.get('capacity_beds', 0),
                "phone": fac.get('phone'),
                "address": fac.get('address')
            })

        # Identify wards with zero trauma center access
        wards_at_risk = []
        for wid, data in neighbourhood_access.items():
            if data["accessible_trauma_centres"] == 0:
                wards_at_risk.append({
                    "neighbourhood_id": wid,
                    "name": data["name"],
                    "reason": "Lost road network connectivity to all Level-1/2 Tertiary Trauma Centres (Vydehi & Sakra)."
                })

        # Compile critical dependency road links
        critical_access_roads = []
        for rid, fac_list in road_facility_dependencies.items():
            if len(fac_list) >= 2: # Road carries access for 2 or more facility-ward connections
                critical_access_roads.append({
                    "road_id": rid,
                    "dependent_facility_routes_count": len(fac_list),
                    "dependent_routes": fac_list[:5],
                    "criticality_explanation": f"Arterial serves as emergency access conduit for {len(fac_list)} critical facility transit routes."
                })

        critical_access_roads.sort(key=lambda x: x['dependent_facility_routes_count'], reverse=True)

        return {
            "total_facilities": total_facilities,
            "reachable_facilities": reachable_count,
            "unreachable_facilities": unreachable_count,
            "overall_accessibility_pct": round((reachable_count / max(1, total_facilities)) * 100, 1),
            "facility_status": facility_status,
            "neighbourhood_access_matrix": list(neighbourhood_access.values()),
            "wards_with_zero_trauma_access": wards_at_risk,
            "critical_facility_dependency_roads": critical_access_roads,
            "active_disruptions": list(closed_set)
        }

# Singleton instance
facility_service = FacilityService()
