import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.scenario_service import scenario_service
from services.graph_service import graph_service


def _sample_roads(n=3):
    return [r['id'] for r in graph_service.get_all_roads()][:n]


def test_scenario_comparison():
    closed = _sample_roads(3)
    res = scenario_service.compare_scenarios('HEAVY', closed, closed[:1])
    assert "stages" in res
    assert "baseline" in res["stages"]
    assert "disrupted" in res["stages"]
    assert "restored" in res["stages"]
    
    baseline = res["stages"]["baseline"]
    disrupted = res["stages"]["disrupted"]
    restored = res["stages"]["restored"]
    
    # Baseline has 100% network integrity and 0 disruptions
    assert baseline["connectivity"]["edges_disrupted"] == 0
    assert len(disrupted["active_disruptions"]) == 3 and res["label"] == "MODELLED"
    
    # Restored scenario has higher integrity than disrupted scenario
    assert restored["connectivity"]["network_integrity_pct"] >= disrupted["connectivity"]["network_integrity_pct"]
    
    # Check comparison matrix
    matrix = res["comparison_matrix"]
    assert "network_integrity_pct" in matrix
    assert matrix["network_integrity_pct"]["improvement_over_disrupted"] >= 0
