"""
PRAVAH AI — Stage 3: Geographic Road Network & Graph Analysis Service

Technologies:
- NetworkX (DiGraph, connected components, articulation points, bridges, edge betweenness)
- GeoPandas & Shapely (CRS handling, spatial intersections, point snapping)

Features:
- Directed graph representation: intersections as nodes, road segments as edges.
- Node attributes: ID, name, lat, lon, elevation, neighbourhood_id.
- Edge attributes: ID, name, length_km, speed_limit_kmh, travel_time_mins, one_way, base_flood_risk, elevation_risk_score, is_critical.
- Graph analytics:
    * Strongly / Weakly / Undirected connected components
    * Articulation points (critical junction cut-vertices)
    * Bridge-edge analysis (cut-edges whose loss splits the graph)
    * Edge betweenness centrality & critical link ranking with explanations
    * Road closure impact simulation
    * Coordinate snapping with distance threshold validation
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import networkx as nx
from services.geo_service import haversine_distance_km

class GraphService:
    def __init__(self, roads_data_path: Optional[Path] = None):
        if roads_data_path is None:
            from config import Config
            # Development road graph is quarantined (UNVERIFIED). Without the explicit flag the graph is empty.
            roads_data_path = Path(__file__).resolve().parent.parent / 'data' / 'dev_quarantine' / 'whitefield_roads.json'
            if not Config.LOAD_PILOT_DATASET:
                roads_data_path = Path('/nonexistent/pravah-no-road-data')
        self.roads_data_path = roads_data_path
        self.nodes_data: List[Dict[str, Any]] = []
        self.edges_data: List[Dict[str, Any]] = []
        self.baseline_graph: nx.DiGraph = nx.DiGraph()
        self._load_network()

    def _load_network(self):
        if not self.roads_data_path.exists():
            return

        with open(self.roads_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.nodes_data = data.get('nodes', [])
            self.edges_data = data.get('edges', [])

        self.baseline_graph = nx.DiGraph()

        # Add nodes
        for node in self.nodes_data:
            self.baseline_graph.add_node(
                node['id'],
                id=node['id'],
                name=node.get('name'),
                lat=node.get('lat'),
                lon=node.get('lon'),
                elevation=node.get('elevation', 880),
                neighbourhood_id=node.get('neighbourhood_id')
            )

        # Add edges (directed or bidirectional based on one_way)
        for edge in self.edges_data:
            length_km = edge.get('length_km', 1.0)
            speed_kmh = edge.get('speed_limit_kmh', 40)
            time_mins = round((length_km / max(10, speed_kmh)) * 60, 2)
            flood_risk = edge.get('base_flood_risk', 'Low')
            one_way = edge.get('one_way', False)

            # Weight incorporates flood risk penalty so routing favors higher ground
            risk_penalty = 0.0
            if flood_risk == 'Moderate':
                risk_penalty = 0.25
            elif flood_risk == 'High':
                risk_penalty = 0.75
            elif flood_risk == 'Severe':
                risk_penalty = 2.0

            weight = round(length_km * (1.0 + risk_penalty), 3)

            attrs = {
                'id': edge['id'],
                'name': edge.get('name'),
                'length_km': length_km,
                'speed_limit_kmh': speed_kmh,
                'travel_time_mins': time_mins,
                'weight': weight,
                'base_flood_risk': flood_risk,
                'elevation_risk_score': edge.get('elevation_risk_score', 30),
                'is_critical': edge.get('is_critical', False),
                'one_way': one_way,
                'is_closed': False
            }

            # Forward edge
            self.baseline_graph.add_edge(edge['source'], edge['target'], **attrs)

            # If not one-way, add reverse edge
            if not one_way:
                self.baseline_graph.add_edge(edge['target'], edge['source'], **attrs)

    def get_baseline_graph(self) -> nx.DiGraph:
        """Returns an unmutated clone of the baseline graph."""
        return self.baseline_graph.copy()

    def get_scenario_graph(self, closed_road_ids: Optional[List[str]] = None) -> nx.DiGraph:
        """
        Creates an independent clone of the baseline graph and applies road closures.
        Never mutates the baseline graph!
        """
        G = self.baseline_graph.copy()
        if not closed_road_ids:
            return G

        closed_set = set(closed_road_ids)
        edges_to_remove = []
        for u, v, data in G.edges(data=True):
            if data.get('id') in closed_set:
                edges_to_remove.append((u, v))

        for u, v in edges_to_remove:
            G.remove_edge(u, v)

        return G

    def snap_to_nearest_node(
        self, lat: float, lon: float, max_dist_km: float = 3.0
    ) -> Tuple[Optional[str], float, Optional[Dict[str, Any]]]:
        """
        Snaps a coordinate to the closest road network intersection node.
        Returns: (node_id, distance_km, node_attributes)
        """
        closest_id = None
        min_dist = float('inf')
        closest_data = None

        for node_id, data in self.baseline_graph.nodes(data=True):
            node_lat = data.get('lat')
            node_lon = data.get('lon')
            if node_lat is not None and node_lon is not None:
                dist = haversine_distance_km(lat, lon, node_lat, node_lon)
                if dist < min_dist:
                    min_dist = dist
                    closest_id = node_id
                    closest_data = data

        if min_dist > max_dist_km:
            return None, min_dist, closest_data

        return closest_id, min_dist, closest_data

    def analyze_connectivity(self, G: Optional[nx.DiGraph] = None) -> Dict[str, Any]:
        """
        Comprehensive graph connectivity analysis:
        - Strongly and weakly connected components
        - Undirected connected components
        - Articulation points (critical nodes)
        - Bridge edges (critical links)
        - Isolated nodes and neighbourhoods
        - Network integrity percentage
        """
        if G is None:
            G = self.baseline_graph

        UG = G.to_undirected()
        components = list(nx.connected_components(UG))
        total_nodes = self.baseline_graph.number_of_nodes()
        total_edges = self.baseline_graph.number_of_edges()
        active_nodes = G.number_of_nodes()
        active_edges = G.number_of_edges()

        # Sort components by size descending
        components_sorted = sorted(components, key=len, reverse=True)
        primary_component = components_sorted[0] if components_sorted else set()

        # Isolated nodes & neighbourhoods
        isolated_nodes = []
        isolated_neighbourhoods = set()
        for node_id in self.baseline_graph.nodes():
            if node_id not in primary_component:
                node_info = self.baseline_graph.nodes[node_id]
                isolated_nodes.append({
                    "id": node_id,
                    "name": node_info.get("name"),
                    "neighbourhood_id": node_info.get("neighbourhood_id"),
                    "lat": node_info.get("lat"),
                    "lon": node_info.get("lon")
                })
                if node_info.get("neighbourhood_id"):
                    isolated_neighbourhoods.add(node_info.get("neighbourhood_id"))

        # Articulation points (cut-vertices)
        raw_articulation_points = list(nx.articulation_points(UG)) if UG.number_of_nodes() > 2 else []
        articulation_points = []
        for ap in raw_articulation_points:
            node_data = self.baseline_graph.nodes.get(ap, {})
            articulation_points.append({
                "node_id": ap,
                "name": node_data.get("name"),
                "neighbourhood_id": node_data.get("neighbourhood_id"),
                "lat": node_data.get("lat"),
                "lon": node_data.get("lon")
            })

        # Bridges (cut-edges)
        raw_bridges = list(nx.bridges(UG)) if UG.number_of_edges() > 0 else []
        bridges = []
        for u, v in raw_bridges:
            edge_data = UG.get_edge_data(u, v) or {}
            u_data = self.baseline_graph.nodes.get(u, {})
            v_data = self.baseline_graph.nodes.get(v, {})
            bridges.append({
                "road_id": edge_data.get('id'),
                "name": edge_data.get('name'),
                "source": u,
                "target": v,
                "source_name": u_data.get('name'),
                "target_name": v_data.get('name'),
                "length_km": edge_data.get('length_km'),
                "base_flood_risk": edge_data.get('base_flood_risk')
            })

        # Strongly connected components (in directed view)
        scc = list(nx.strongly_connected_components(G))

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "active_nodes": active_nodes,
            "active_edges": active_edges,
            "edges_disrupted": total_edges - active_edges,
            "num_connected_components": len(components),
            "num_strongly_connected_components": len(scc),
            "primary_component_size": len(primary_component),
            "isolated_node_count": len(isolated_nodes),
            "isolated_nodes": isolated_nodes,
            "isolated_neighbourhood_ids": list(isolated_neighbourhoods),
            "network_integrity_pct": round((len(primary_component) / max(1, total_nodes)) * 100, 1),
            "articulation_point_count": len(articulation_points),
            "articulation_points": articulation_points,
            "bridge_count": len(bridges),
            "bridges": bridges
        }

    def identify_critical_road_links(self, G: Optional[nx.DiGraph] = None) -> List[Dict[str, Any]]:
        """
        Ranks and explains critical road links based on:
        1. Topological bridge status (severing splits the network into components).
        2. Edge betweenness centrality (percentage of all shortest paths passing through this corridor).
        3. Elevation and base flood susceptibility.
        4. Operational access criticality (connecting hospitals / emergency hubs).
        """
        if G is None:
            G = self.baseline_graph

        UG = G.to_undirected()
        bridge_edges_set = set()
        for u, v in nx.bridges(UG):
            bridge_edges_set.add((u, v))
            bridge_edges_set.add((v, u))

        # Edge betweenness centrality
        try:
            betweenness = nx.edge_betweenness_centrality(G, weight='weight')
        except Exception:
            betweenness = {}

        ranked_links = []
        for edge in self.edges_data:
            road_id = edge['id']
            src, tgt = edge['source'], edge['target']
            is_bridge = (src, tgt) in bridge_edges_set or (tgt, src) in bridge_edges_set
            ebc = max(betweenness.get((src, tgt), 0.0), betweenness.get((tgt, src), 0.0))
            elev_risk = edge.get('elevation_risk_score', 30)
            is_flagged_critical = edge.get('is_critical', False)

            # Criticality score: 0 - 100
            score = (
                (40.0 if is_bridge else 0.0) +
                (min(30.0, ebc * 120.0)) +
                (elev_risk * 0.20) +
                (10.0 if is_flagged_critical else 0.0)
            )
            score = round(min(100.0, score), 1)

            # Build explainability rationale
            reasons = []
            if is_bridge:
                reasons.append("Topological bridge link: loss immediately isolates adjacent ward components.")
            if ebc > 0.15:
                reasons.append(f"Major transit corridor carrying {round(ebc * 100, 1)}% of network shortest paths.")
            if elev_risk >= 75:
                reasons.append(f"Low-lying terrain depression risk (elevation score {elev_risk}/100), prone to flash flooding.")
            if is_flagged_critical:
                reasons.append("Designated municipal arterial connecting regional emergency facilities.")

            if not reasons:
                reasons.append("Secondary link road with redundant local bypasses.")

            ranked_links.append({
                "road_id": road_id,
                "name": edge.get('name'),
                "source": src,
                "target": tgt,
                "source_name": self.baseline_graph.nodes.get(src, {}).get('name'),
                "target_name": self.baseline_graph.nodes.get(tgt, {}).get('name'),
                "length_km": edge.get('length_km'),
                "speed_limit_kmh": edge.get('speed_limit_kmh'),
                "base_flood_risk": edge.get('base_flood_risk'),
                "elevation_risk_score": elev_risk,
                "is_bridge": is_bridge,
                "betweenness_centrality": round(ebc, 4),
                "criticality_score": score,
                "why_critical": " ".join(reasons)
            })

        # Sort descending by criticality score
        ranked_links.sort(key=lambda x: x['criticality_score'], reverse=True)
        return ranked_links

    def evaluate_road_closure_impact(self, closed_road_ids: List[str]) -> Dict[str, Any]:
        """
        Calculates direct impact of simulated or observed road closures on graph reachability.
        """
        closed_set = set(closed_road_ids or [])
        G_scen = self.get_scenario_graph(closed_road_ids)
        conn = self.analyze_connectivity(G_scen)

        # Detail closed edges
        closed_details = []
        for edge in self.edges_data:
            if edge['id'] in closed_set:
                closed_details.append({
                    "road_id": edge['id'],
                    "name": edge.get('name'),
                    "source": edge.get('source'),
                    "target": edge.get('target'),
                    "length_km": edge.get('length_km'),
                    "base_flood_risk": edge.get('base_flood_risk')
                })

        return {
            "closed_roads_count": len(closed_set),
            "closed_roads": closed_details,
            "connectivity": conn,
            "network_status": (
                "CRITICAL_SPLIT" if conn['num_connected_components'] > 1
                else "DEGRADED" if len(closed_set) > 0
                else "NORMAL"
            )
        }

    def get_all_roads(self) -> List[Dict[str, Any]]:
        return self.edges_data

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        return self.nodes_data

# Singleton instance
graph_service = GraphService()
