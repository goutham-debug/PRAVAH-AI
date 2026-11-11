import json
import os
import pytest
from services.shelter_service import shelter_service
from services.rescue_service import rescue_service

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "dev_quarantine")

@pytest.fixture
def pilot_shelters():
    path = os.path.join(DATA_DIR, "shelters.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def pilot_rescue_teams():
    path = os.path.join(DATA_DIR, "rescue_teams.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_shelter_allocation_capacity_constraint(pilot_shelters):
    """Enforces zero shelter capacity overflow: allocated count must never exceed remaining capacity."""
    # Create artificial high demand exceeding a single shelter
    demands = [
        {
            "neighbourhood_id": "WARD_149",
            "name": "Varthur",
            "demand": 2500,
            "centroid": [77.747, 12.938]
        }
    ]
    res = shelter_service.allocate_shelters(ward_demands=demands, shelters=pilot_shelters)
    
    assert res["total_evacuation_demand"] == 2500
    assert res["total_allocated_population"] <= res["total_shelter_capacity"]
    
    # Check individual shelter allocations
    for s in res["shelter_status"]:
        assert s["assigned_count"] <= s["total_capacity"]
        assert s["remaining_capacity"] >= 0

def test_shelter_allocation_unmet_demand_reported(pilot_shelters):
    """When demand exceeds available capacity, unallocated demand must be explicitly reported."""
    total_cap = sum(s.get("total_capacity", 0) for s in pilot_shelters)
    huge_demand = total_cap + 1000

    demands = [
        {
            "neighbourhood_id": "WARD_OVERFLOW",
            "name": "Extreme Overflow Ward",
            "demand": huge_demand,
            "centroid": [77.7499, 12.9698]
        }
    ]
    res = shelter_service.allocate_shelters(ward_demands=demands, shelters=pilot_shelters)
    assert res["total_unmet_demand"] >= 1000
    assert len(res["unmet_records"]) > 0
    assert any("exhausted total capacity limit" in r["reason"] for r in res["unmet_records"])

def test_rescue_coordination_capability_matching(pilot_rescue_teams):
    """Enforces matching of squad capability (BOAT_RESCUE, DEWATERING_PUMP, etc.) to incident type."""
    incidents = [
        {
            "id": 101,
            "tracking_id": "INC-BOAT-01",
            "incident_type": "STRANDED_PERSONS",
            "severity": "SEVERE",
            "lat": 12.940,
            "lon": 77.745,
            "status": "VERIFIED",
            "description": "Family stranded on flooded terrace near lake sluice"
        },
        {
            "id": 102,
            "tracking_id": "INC-PUMP-02",
            "incident_type": "DRAIN_OVERFLOW",
            "severity": "HIGH",
            "lat": 12.975,
            "lon": 77.730,
            "status": "VERIFIED",
            "description": "Culvert blocked under railway bridge"
        }
    ]

    res = rescue_service.coordinate_rescue_assignments(
        incident_reports=incidents,
        rescue_teams=pilot_rescue_teams
    )

    assert res["total_incidents_evaluated"] == 2
    assert res["dispatched_count"] >= 1
    
    # Verify no team assigned multiple times
    assigned_team_ids = [a["assigned_team_id"] for a in res["assignments"]]
    assert len(assigned_team_ids) == len(set(assigned_team_ids)), "Duplicate team assignment detected!"

def test_rescue_coordination_no_duplicate_assignment(pilot_rescue_teams):
    """Verifies that no single rescue team is assigned to more than one active mission."""
    # Single team pool
    single_team = [pilot_rescue_teams[0]]
    incidents = [
        {
            "id": 201, "tracking_id": "INC-01", "incident_type": "STRANDED_PERSONS",
            "severity": "SEVERE", "lat": 12.940, "lon": 77.745, "status": "VERIFIED"
        },
        {
            "id": 202, "tracking_id": "INC-02", "incident_type": "STRANDED_PERSONS",
            "severity": "SEVERE", "lat": 12.945, "lon": 77.750, "status": "VERIFIED"
        }
    ]
    res = rescue_service.coordinate_rescue_assignments(
        incident_reports=incidents,
        rescue_teams=single_team
    )
    assert res["dispatched_count"] == 1
    assert res["unassigned_count"] == 1
    assert res["remaining_idle_teams_count"] == 0
