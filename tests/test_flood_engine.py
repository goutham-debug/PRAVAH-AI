import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.flood_engine import flood_engine

def test_flood_risk_formula_bounds():
    # Min bounds
    res_min = flood_engine.calculate_risk_score(0, 0, 0, 0)
    assert res_min['risk_score'] == 0.0
    assert res_min['classification'] == 'LOW'

    # Max bounds
    res_max = flood_engine.calculate_risk_score(100, 100, 100, 100)
    assert res_max['risk_score'] == 100.0
    assert res_max['classification'] == 'SEVERE'

def test_flood_risk_weighted_index_math():
    # R = 0.35 * P + 0.20 * E + 0.25 * H + 0.20 * D
    # P=65, E=50, H=80, D=70
    # Expected R = (0.35*65) + (0.20*50) + (0.25*80) + (0.20*70) = 22.75 + 10.0 + 20.0 + 14.0 = 66.75 -> 66.8
    res = flood_engine.calculate_risk_score(65, 50, 80, 70)
    assert abs(res['risk_score'] - 66.8) <= 0.1
    assert res['classification'] == 'HIGH'
    assert 'components' in res
    assert res['components']['P']['weighted_contribution'] == 22.75

def test_flood_engine_assess_neighbourhoods():
    sample_wards = [
        {"id": "NB_VARTHUR", "name": "Varthur", "hazard_factor": 85, "drainage_factor": 80, "population": 36000},
        {"id": "NB_KADUGODI", "name": "Kadugodi", "hazard_factor": 30, "drainage_factor": 25, "population": 38000}
    ]
    results = flood_engine.assess_neighbourhoods(sample_wards, rainfall_scenario="HEAVY")
    assert len(results) == 2
    # Varthur should have higher risk than Kadugodi
    assert results[0]['neighbourhood_id'] == 'NB_VARTHUR'
    assert results[0]['risk_score'] > results[1]['risk_score']
