import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))

from services.flood_engine import flood_engine

def test_stage2_formula_and_weights():
    # Verify weights sum exactly to 1.00
    meta = flood_engine.get_methodology_metadata()
    weights = meta['weights']
    total_w = sum(w['weight'] for w in weights.values())
    assert abs(total_w - 1.00) < 1e-6
    assert weights['P']['weight'] == 0.35
    assert weights['E']['weight'] == 0.20
    assert weights['H']['weight'] == 0.25
    assert weights['D']['weight'] == 0.20

def test_stage2_normalization_functions():
    # Rainfall normalisation
    assert flood_engine.normalize_rainfall(0) == 0.0
    assert flood_engine.normalize_rainfall(195.0) == 100.0
    assert flood_engine.normalize_rainfall(390.0) == 100.0 # Clamped

    # Elevation vulnerability: 850m = 100.0 (valley floor), 895m = 0.0 (high ground)
    assert flood_engine.normalize_elevation_vulnerability(850.0) == 100.0
    assert flood_engine.normalize_elevation_vulnerability(895.0) == 0.0
    assert flood_engine.normalize_elevation_vulnerability(872.5) == 50.0
    assert flood_engine.normalize_elevation_vulnerability(840.0) == 100.0 # Clamped below min
    assert flood_engine.normalize_elevation_vulnerability(910.0) == 0.0 # Clamped above max
    assert flood_engine.normalize_elevation_vulnerability(None) is None

    # Hazard & Drainage
    assert flood_engine.normalize_hazard(75.5) == 75.5
    assert flood_engine.normalize_hazard(150.0) == 100.0 # Clamped
    assert flood_engine.normalize_drainage(60.0) == 60.0
    assert flood_engine.normalize_drainage(-10.0) == 0.0

def test_stage2_missing_input_returns_not_assessed():
    # When any factor is missing (None), must return NOT_ASSESSED under strict data policy
    res1 = flood_engine.calculate_risk_score(None, 50, 50, 50)
    assert res1['classification'] == 'NOT_ASSESSED'
    assert res1['risk_score'] is None
    assert 'Rainfall Intensity (P)' in res1['missing_inputs']

    res2 = flood_engine.calculate_risk_score(50, None, 50, 50)
    assert res2['classification'] == 'NOT_ASSESSED'
    assert res2['risk_score'] is None
    assert 'Elevation Vulnerability (E)' in res2['missing_inputs']

    res3 = flood_engine.calculate_risk_score(50, 50, None, 50)
    assert res3['classification'] == 'NOT_ASSESSED'
    assert res3['risk_score'] is None

    res4 = flood_engine.calculate_risk_score(50, 50, 50, None)
    assert res4['classification'] == 'NOT_ASSESSED'
    assert res4['risk_score'] is None

def test_stage2_explainability_and_component_breakdown():
    # P=80, E=60, H=70, D=50
    # Expected: (0.35 * 80) + (0.20 * 60) + (0.25 * 70) + (0.20 * 50) = 28.0 + 12.0 + 17.5 + 10.0 = 67.5
    res = flood_engine.calculate_risk_score(80, 60, 70, 50)
    assert res['risk_score'] == 67.5
    assert res['classification'] == 'HIGH'
    
    components = res['components']
    assert components['P']['weighted_contribution'] == 28.0
    assert components['E']['weighted_contribution'] == 12.0
    assert components['H']['weighted_contribution'] == 17.5
    assert components['D']['weighted_contribution'] == 10.0

    # Sum of percentage contributions must equal ~100%
    pct_sum = (
        components['P']['pct_of_total'] +
        components['E']['pct_of_total'] +
        components['H']['pct_of_total'] +
        components['D']['pct_of_total']
    )
    assert abs(pct_sum - 100.0) <= 0.5

    # Primary driver must be Rainfall Intensity
    assert res['primary_driver']['name'] == 'Rainfall Intensity (P)'
    assert 'source' in components['P']
    assert 'limitations_notice' in res

def test_stage2_data_sources_and_provenance():
    assert 'P' in flood_engine.DATA_SOURCES
    assert 'E' in flood_engine.DATA_SOURCES
    assert 'H' in flood_engine.DATA_SOURCES
    assert 'D' in flood_engine.DATA_SOURCES
    assert flood_engine.DATA_SOURCES['P']['provider'].startswith('Open-Meteo')
    assert 'SRTM' in flood_engine.DATA_SOURCES['E']['provider']
