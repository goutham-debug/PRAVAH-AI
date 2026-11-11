import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.graph_service import graph_service
from services.geo_service import geo_service
from services.facility_service import facility_service

def test_stage3_directed_graph_properties():
    G = graph_service.get_baseline_graph()
    assert G.number_of_nodes() >= 10
    assert G.number_of_edges() >= 20 # Directed edges (forward + backward for 2-way)
    
    # Check node attributes
    for n, data in G.nodes(data=True):
        assert 'name' in data
        assert 'lat' in data
        assert 'lon' in data
        assert 'elevation' in data
        assert 800 <= data['elevation'] <= 950

    # Check edge attributes
    for u, v, data in G.edges(data=True):
        assert 'id' in data
        assert 'length_km' in data
        assert data['length_km'] > 0
        assert 'weight' in data
        assert 'base_flood_risk' in data

def test_stage3_connected_components_and_integrity():
    conn = graph_service.analyze_connectivity()
    assert conn['num_connected_components'] == 1 # Baseline is fully connected
    assert conn['network_integrity_pct'] == 100.0
    assert conn['isolated_node_count'] == 0

def test_stage3_articulation_points_and_bridges():
    conn = graph_service.analyze_connectivity()
    # In an urban arterial graph with bridges and dead ends, articulation points and bridges exist
    assert 'articulation_points' in conn
    assert 'bridges' in conn
    assert conn['articulation_point_count'] > 0
    assert conn['bridge_count'] > 0

    # Verify bridge structure
    first_bridge = conn['bridges'][0]
    assert 'road_id' in first_bridge
    assert 'source' in first_bridge
    assert 'target' in first_bridge

def test_stage3_critical_road_links_ranking_and_explanation():
    critical_links = graph_service.identify_critical_road_links()
    assert len(critical_links) > 0
    
    # Top link must have high criticality score
    top_link = critical_links[0]
    assert 'criticality_score' in top_link
    assert 'why_critical' in top_link
    assert len(top_link['why_critical']) > 10
    assert 'betweenness_centrality' in top_link
    assert top_link['criticality_score'] >= critical_links[-1]['criticality_score']

def test_stage3_road_closure_impact_simulation():
    # Sever the Varthur-Whitefield State Highway and Kadubeesanahalli underpass
    closed_roads = ["ROAD_WHITEFIELD_VARTHUR_KODI", "ROAD_MARATHAHALLI_KADUBEESANAHALLI"]
    impact = graph_service.evaluate_road_closure_impact(closed_roads)
    assert impact['closed_roads_count'] == 2
    assert 'connectivity' in impact
    assert impact['connectivity']['active_edges'] < graph_service.baseline_graph.number_of_edges()

def test_stage3_geopandas_neighbourhood_boundaries():
    boundaries = geo_service.analyze_neighbourhood_boundaries()
    assert len(boundaries) >= 4
    for b in boundaries:
        assert b['is_valid_geometry'] is True
        assert b['area_sqkm_calculated'] > 0
        assert len(b['centroid']) == 2
        # Centroid coordinates within Bengaluru bounds
        assert 12.8 <= b['centroid'][1] <= 13.2
        assert 77.5 <= b['centroid'][0] <= 77.9

def test_stage3_shapely_water_body_proximity_buffer():
    # Test 350m buffer intersection with road network
    proximity = geo_service.analyze_water_body_proximity(buffer_meters=350.0)
    assert proximity['monitored_water_bodies'] == 2 # Bellandur & Varthur
    assert proximity['exposed_roads_count'] > 0
    
    # Check that low-lying lake roads (e.g. Varthur or Bellandur) intersect the buffer
    exposed_ids = [r['road_id'] for r in proximity['exposed_roads']]
    assert any('VARTHUR' in rid or 'BELLANDUR' in rid or 'KADUBEESANAHALLI' in rid for rid in exposed_ids)

def test_stage3_hospital_accessibility_and_dependency():
    import json
    data_dir = Path(__file__).resolve().parent.parent / 'backend' / 'data' / 'dev_quarantine'
    with open(data_dir / 'facilities.json', 'r', encoding='utf-8') as f:
        facs = json.load(f)
    with open(data_dir / 'whitefield_neighbourhoods.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
        nbs = [feat['properties'] for feat in geo['features']]

    # Baseline evaluation: all or most facilities should be reachable
    baseline = facility_service.evaluate_accessibility(facs, nbs, closed_road_ids=[])
    assert baseline['reachable_facilities'] > 0
    assert baseline['overall_accessibility_pct'] > 50.0

    # Closure of key link disconnecting Sakra or Vydehi
    closed_eval = facility_service.evaluate_accessibility(
        facs, nbs, 
        closed_road_ids=["ROAD_KADUBEESANAHALLI_DEVARABEESANAHALLI", "ROAD_DEVARABEESANAHALLI_BELLANDUR"]
    )
    assert 'critical_facility_dependency_roads' in closed_eval
