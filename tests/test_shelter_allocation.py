import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.shelter_service import shelter_service

def test_shelter_capacity_hard_constraint():
    shelters = [
        {"id": "S1", "name": "Shelter A", "nearest_node_id": "N_WHITEFIELD_POST", "total_capacity": 100, "current_occupancy": 0},
        {"id": "S2", "name": "Shelter B", "nearest_node_id": "N_HOODI_JN", "total_capacity": 50, "current_occupancy": 0}
    ]
    ward_demands = [
        {"neighbourhood_id": "W1", "name": "Ward 1", "demand": 120, "centroid": [77.7490, 12.9690]} # near Shelter A
    ]
    
    result = shelter_service.allocate_shelters(ward_demands, shelters, closed_road_ids=[])
    
    # Total capacity of S1 is 100. Demand is 120.
    # S1 MUST NOT exceed 100!
    allocated_to_s1 = sum(a['allocated_population'] for a in result['assignments'] if a['shelter_id'] == 'S1')
    assert allocated_to_s1 <= 100
    
    # Remaining 20 can go to S2 or become unmet
    total_alloc = result['total_allocated_population']
    assert total_alloc <= 150 # total capacity of S1 + S2
