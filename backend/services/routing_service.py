"""
PRAVAH AI — Stage 4: Intelligent Routing Engine

Pathfinding Algorithms:
- Dijkstra's Algorithm (shortest weighted cost path)
- A* Algorithm (admissible Haversine distance heuristic)

Cost Calculation Methodology:
    edge_cost = length_km * (1.0 + flood_risk_penalty)
Where:
    - Low Risk: penalty = 0.0 (multiplier = 1.0)
    - Moderate Risk: penalty = 0.25 (multiplier = 1.25)
    - High Risk: penalty = 0.75 (multiplier = 1.75)
    - Severe Risk: penalty = 2.0 (multiplier = 3.0)

Constraints & Policies:
- Coordinate snapping with 3.0 km threshold.
- One-way traffic restrictions strictly enforced on DiGraph.
- Confirmed closed roads completely excluded.
- Alternative route generation via primary path edge penalization (4.0x multiplier).
- Estimated travel time based on 25 km/h urban flood transit crawl speed.
- Strict real-data policy: No unverified live traffic claimed; no route claimed safe without verified ground conditions.
"""

from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
from services.geo_service import haversine_distance_km
from services.graph_service import graph_service

class RoutingService:
    EMERGENCY_TRANSIT_SPEED_KMH = 25.0 # Realistic urban transit speed during monsoon/waterlogging
    MAX_SNAP_DISTANCE_KM = 3.0

    def calculate_route(
        self,
        start_lat: float,
        start_lon: float,
        dest_lat: float,
        dest_lon: float,
        closed_road_ids: Optional[List[str]] = None,
        algorithm: str = "dijkstra",
        calculate_alternative: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates optimal evacuation and safe transit routes avoiding confirmed road closures.
        """
        algorithm = algorithm.lower()
        if algorithm not in ["dijkstra", "astar"]:
            algorithm = "dijkstra"

        # 1. Coordinate snapping with validation
        start_node, start_snap_dist, start_node_data = graph_service.snap_to_nearest_node(
            start_lat, start_lon, max_dist_km=self.MAX_SNAP_DISTANCE_KM
        )
        dest_node, dest_snap_dist, dest_node_data = graph_service.snap_to_nearest_node(
            dest_lat, dest_lon, max_dist_km=self.MAX_SNAP_DISTANCE_KM
        )

        if not start_node:
            return {
                "success": False,
                "error": (
                    f"Origin location ({round(start_lat, 4)}, {round(start_lon, 4)}) is "
                    f"{round(start_snap_dist, 2)} km from nearest road network node, "
                    f"exceeding the maximum allowed snap threshold ({self.MAX_SNAP_DISTANCE_KM} km)."
                ),
                "snap_distance_km": round(start_snap_dist, 2),
                "max_threshold_km": self.MAX_SNAP_DISTANCE_KM
            }

        if not dest_node:
            return {
                "success": False,
                "error": (
                    f"Destination location ({round(dest_lat, 4)}, {round(dest_lon, 4)}) is "
                    f"{round(dest_snap_dist, 2)} km from nearest road network node, "
                    f"exceeding the maximum allowed snap threshold ({self.MAX_SNAP_DISTANCE_KM} km)."
                ),
                "snap_distance_km": round(dest_snap_dist, 2),
                "max_threshold_km": self.MAX_SNAP_DISTANCE_KM
            }

        # 2. Get scenario graph with confirmed closures removed
        G = graph_service.get_scenario_graph(closed_road_ids)

        # Same origin and destination node check
        if start_node == dest_node:
            total_dist = round(start_snap_dist + dest_snap_dist, 2)
            time_mins = round((total_dist / self.EMERGENCY_TRANSIT_SPEED_KMH) * 60.0, 1)
            return {
                "success": True,
                "primary_route": {
                    "total_distance_km": total_dist,
                    "travel_time_mins": time_mins,
                    "node_sequence": [start_node],
                    "road_names": ["Direct Local Access"],
                    "coordinates": [
                        [start_lon, start_lat],
                        [start_node_data['lon'], start_node_data['lat']],
                        [dest_lon, dest_lat]
                    ],
                    "turn_by_turn": [
                        f"Origin and destination snap to the same junction ({start_node_data.get('name')}). "
                        "Proceed directly on foot or local access lane."
                    ],
                    "route_explanation": "Origin and destination are within immediate walking proximity of the same network node."
                },
                "alternative_route": None,
                "closures_avoided_count": len(closed_road_ids or []),
                "algorithm_used": algorithm.upper(),
                "traffic_notice": "Estimates based on static geometric network distance. Live traffic API not active."
            }

        # 3. Pathfinding (Dijkstra or A*)
        try:
            if algorithm == "astar":
                # Admissible heuristic: Haversine distance in km
                def astar_heuristic(u, v):
                    u_d = G.nodes[u]
                    v_d = G.nodes[v]
                    return haversine_distance_km(u_d['lat'], u_d['lon'], v_d['lat'], v_d['lon'])

                path_nodes = nx.astar_path(G, start_node, dest_node, heuristic=astar_heuristic, weight='weight')
            else:
                path_nodes = nx.dijkstra_path(G, start_node, dest_node, weight='weight')
        except nx.NetworkXNoPath:
            # Area isolation detection
            ug = G.to_undirected()
            return {
                "success": False,
                "error": (
                    f"No connected route found between '{start_node_data.get('name')}' and '{dest_node_data.get('name')}'. "
                    "All connecting corridors are currently blocked by confirmed closures or flood disruption. "
                    "The area is topologically isolated."
                ),
                "is_isolated": True,
                "start_node": start_node_data,
                "dest_node": dest_node_data,
                "active_closures": closed_road_ids or []
            }

        primary_route = self._build_route_details(
            G, path_nodes, start_lat, start_lon, dest_lat, dest_lon, is_alt=False
        )

        # 4. Alternative route generation (penalize primary path edges)
        alt_route = None
        if calculate_alternative:
            G_alt = G.copy()
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i+1]
                if G_alt.has_edge(u, v):
                    G_alt[u][v]['weight'] = G_alt[u][v].get('weight', 1.0) * 4.0

            try:
                alt_nodes = nx.dijkstra_path(G_alt, start_node, dest_node, weight='weight')
                if alt_nodes != path_nodes:
                    alt_route = self._build_route_details(
                        G, alt_nodes, start_lat, start_lon, dest_lat, dest_lon, is_alt=True
                    )
            except Exception:
                alt_route = None

        return {
            "success": True,
            "algorithm_used": algorithm.upper(),
            "cost_function": "cost = length_km * (1.0 + flood_risk_penalty)",
            "start_node": start_node_data,
            "dest_node": dest_node_data,
            "primary_route": primary_route,
            "alternative_route": alt_route,
            "closures_avoided_count": len(closed_road_ids or []),
            "closed_roads_active": closed_road_ids or [],
            "safety_notice": (
                "Route calculated based on network distance, one-way restrictions, and base flood risk weights. "
                "Conditions may change rapidly during heavy monsoon showers. Proceed with caution at low-lying underpasses."
            ),
            "traffic_notice": (
                "Transit time calculated at 25 km/h emergency transit crawl speed. "
                "Does NOT reflect live traffic congestion (no live traffic API active)."
            )
        }

    def _build_route_details(
        self,
        G: nx.DiGraph,
        node_ids: List[str],
        start_lat: float,
        start_lon: float,
        dest_lat: float,
        dest_lon: float,
        is_alt: bool = False
    ) -> Dict[str, Any]:
        coords = [[start_lon, start_lat]]
        road_names = []
        total_dist_km = 0.0
        total_time_mins = 0.0
        turn_by_turn = []
        high_risk_segments = []

        start_node_name = G.nodes[node_ids[0]].get('name', 'Origin Junction')
        turn_by_turn.append(f"Depart origin. Proceed to nearest intersection: {start_node_name}.")

        for i in range(len(node_ids)):
            curr = node_ids[i]
            c_data = G.nodes[curr]
            coords.append([c_data['lon'], c_data['lat']])

            if i < len(node_ids) - 1:
                nxt = node_ids[i+1]
                n_data = G.nodes[nxt]
                edge_data = G.get_edge_data(curr, nxt) or {}

                road_name = edge_data.get('name', f"Link to {n_data.get('name')}")
                dist = edge_data.get('length_km', 1.0)
                speed = edge_data.get('speed_limit_kmh', 30)
                # Estimate travel time based on speed limit or emergency speed
                effective_speed = min(speed, self.EMERGENCY_TRANSIT_SPEED_KMH)
                t_mins = round((dist / max(10, effective_speed)) * 60.0, 1)
                flood_risk = edge_data.get('base_flood_risk', 'Low')

                total_dist_km += dist
                total_time_mins += t_mins
                if road_name not in road_names:
                    road_names.append(road_name)

                if flood_risk in ['High', 'Severe']:
                    high_risk_segments.append(road_name)

                turn_by_turn.append(
                    f"Follow {road_name} for {round(dist, 1)} km ({round(t_mins, 1)} mins) towards {n_data.get('name')} "
                    f"[{flood_risk} flood hazard zone]."
                )

        coords.append([dest_lon, dest_lat])
        dest_node_name = G.nodes[node_ids[-1]].get('name', 'Destination Junction')
        turn_by_turn.append(f"Arrive safely at destination ({dest_node_name}).")

        # Route explanation
        risk_summary = (
            f"Passes through {len(high_risk_segments)} high-hazard segment(s): {', '.join(high_risk_segments)}."
            if high_risk_segments
            else "Traverses relatively elevated, low-risk roadways."
        )
        explanation = (
            f"{'Alternative' if is_alt else 'Primary'} route covering {round(total_dist_km, 2)} km across "
            f"{len(node_ids)} intersections via {len(road_names)} road corridor(s). {risk_summary}"
        )

        return {
            "is_alternative": is_alt,
            "total_distance_km": round(total_dist_km, 2),
            "travel_time_mins": round(total_time_mins, 1),
            "node_count": len(node_ids),
            "node_sequence": node_ids,
            "road_names": road_names,
            "high_risk_segments": high_risk_segments,
            "coordinates": coords,
            "turn_by_turn": turn_by_turn,
            "route_explanation": explanation
        }

# Singleton instance
routing_service = RoutingService()
