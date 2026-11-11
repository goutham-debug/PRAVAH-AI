"""Data Operations API tests (need the full backend deps: pip install -r backend/requirements.txt).
Provider HTTP is patched; no real network calls."""
from unittest import mock

from conftest import auth


class R:
    def __init__(self, status=200, body=b''):
        self.status_code, self.content = status, body


def test_dataops_requires_authentication(client):
    for path in ('/api/dataops/overview', '/api/dataops/datasets', '/api/dataops/runs', '/api/dataops/events'):
        assert client.get(path).status_code == 401, path
    assert client.post('/api/dataops/sources/imd/refresh').status_code == 401


def test_dataops_role_policy(client, make_user):
    _, _, analyst = make_user('READ_ONLY_ANALYST')
    _, _, officer = make_user('DISASTER_OFFICER')
    _, _, manager = make_user('DATA_MANAGER')
    assert client.get('/api/dataops/overview', headers=auth(analyst)).status_code == 403
    assert client.get('/api/dataops/overview', headers=auth(officer)).status_code == 200
    assert client.post('/api/dataops/sources/imd/refresh', headers=auth(officer)).status_code == 403
    assert client.post('/api/dataops/sources/imd/refresh', headers=auth(manager)).status_code in (202, 409)


def test_overview_reports_real_state(client, admin_token):
    d = client.get('/api/dataops/overview', headers=auth(admin_token)).get_json()
    assert d['api']['status'] == 'UP' and d['database']['status'] == 'UP'
    keys = {s['key'] for s in d['sources']}
    assert keys == {'open_meteo', 'osm_roads', 'imd', 'ksndmc', 'cwc', 'gba', 'bhuvan'}
    imd = next(s for s in d['sources'] if s['key'] == 'imd')
    assert imd['configured'] is False and 'IMD_URL' in imd['missing_credentials']
    assert imd['classification'] in ('NOT_ASSESSED', 'UNAVAILABLE')


def test_unknown_source_404(client, admin_token):
    assert client.post('/api/dataops/sources/nope/refresh', headers=auth(admin_token)).status_code == 404


def test_not_configured_refresh_logs_real_run_and_claims_nothing(client, admin_token):
    import time
    with mock.patch('requests.get') as g:
        rv = client.post('/api/dataops/sources/ksndmc/refresh', headers=auth(admin_token))
        assert rv.status_code in (202, 409)
        for _ in range(50):
            runs = client.get('/api/dataops/runs?source=ksndmc', headers=auth(admin_token)).get_json()['runs']
            if runs and runs[0]['status'] != 'RUNNING':
                break
            time.sleep(0.1)
    assert runs[0]['status'] == 'NOT_CONFIGURED'
    g.assert_not_called()
    ev = client.get('/api/dataops/events', headers=auth(admin_token)).get_json()['events']
    assert any('missing KSNDMC_URL' in e['message'] for e in ev)
    ov = client.get('/api/dataops/overview', headers=auth(admin_token)).get_json()
    k = next(s for s in ov['sources'] if s['key'] == 'ksndmc')
    assert k['last_success_at'] is None and k['classification'] == 'UNAVAILABLE'


def test_weather_failure_is_unavailable_and_registered(client, admin_token):
    import requests
    from services.weather_service import weather_service
    weather_service._cache = None
    with mock.patch('requests.get', side_effect=requests.ConnectionError('offline')), \
            mock.patch('providers.http.time.sleep'):
        w = client.get('/api/weather', headers=auth(admin_token)).get_json()['weather']
    assert w['status'] == 'UNAVAILABLE' and 'temperature_c' not in w
    ov = client.get('/api/dataops/overview', headers=auth(admin_token)).get_json()
    om = next(s for s in ov['sources'] if s['key'] == 'open_meteo')
    assert om['last_status'] == 'FAILED' and om['last_success_at'] is None


def test_health_endpoint_stays_minimal(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200 and set(rv.get_json()) == {'status', 'product'}
