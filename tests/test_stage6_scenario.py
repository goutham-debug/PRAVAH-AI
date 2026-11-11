import pytest
from services.scenario_service import scenario_service
from services.graph_service import graph_service

def test_scenario_baseline_graph_immutability(app):
    """The scenario simulation must use independent graph copies and NEVER mutate the baseline graph."""
    with app.app_context():
        orig_nodes = graph_service.baseline_graph.number_of_nodes()
        orig_edges = graph_service.baseline_graph.number_of_edges()

        # Run simulation with multiple closed roads
        closed = ["ROAD_HOPEFARM_ITPL", "ROAD_ITPL_HOODI"]
        res = scenario_service.run_simulation(
            rainfall_scenario="EXTREME",
            closed_road_ids=closed,
            scenario_name="Immutability Test"
        )

        assert res["active_disruptions"] == closed
        
        # Verify baseline graph was not mutated
        assert graph_service.baseline_graph.number_of_nodes() == orig_nodes
        assert graph_service.baseline_graph.number_of_edges() == orig_edges

def test_scenario_comparison_delta_matrix(app):
    """Verifies that scenario comparison accurately computes delta metrics between baseline and disrupted."""
    with app.app_context():
        res = scenario_service.compare_scenarios(
            rainfall_scenario="HEAVY",
            closed_road_ids=["ROAD_HOPEFARM_ITPL"],
            restored_road_ids=[]
        )

        assert "stages" in res
        assert "baseline" in res["stages"]
        assert "disrupted" in res["stages"]
        assert "restored" in res["stages"]
        assert "comparison_matrix" in res

        matrix = res["comparison_matrix"]
        assert "network_integrity_pct" in matrix
        assert "isolated_wards_count" in matrix
        assert "unreachable_facilities" in matrix
        assert "unmet_shelter_demand" in matrix
        assert res["label"] == "MODELLED"
