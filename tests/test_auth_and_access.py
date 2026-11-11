from conftest import auth, _login


def test_health_is_public_and_minimal(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert set(rv.get_json()) == {"status", "product"}


def test_demo_endpoints_removed(client):
    assert client.post('/api/auth/demo-login', json={"role": "AUTHORITY"}).status_code in (401, 404)
    assert client.post('/api/auth/register', json={"email": "x@y.z", "password": "x"}).status_code in (401, 404, 405)


def test_all_data_endpoints_require_auth(client):
    for path in ['/api/geo/neighbourhoods', '/api/geo/facilities', '/api/roads/topology', '/api/shelters',
                 '/api/rescue/teams', '/api/incidents', '/api/weather', '/api/system/status',
                 '/api/flood/formula', '/api/scenarios/candidate-disruptions', '/api/admin/users']:
        assert client.get(path).status_code == 401, path
    assert client.post('/api/scenarios/simulate', json={}).status_code == 401


def test_login_rejects_bad_credentials_without_user_enumeration(client):
    a = _login(client, 'admin@example.test', 'wrong')
    b = _login(client, 'nobody@example.test', 'wrong')
    assert a.status_code == b.status_code == 401
    assert a.get_json()['error'] == b.get_json()['error']


def test_forged_and_expired_tokens_rejected(client):
    import jwt
    from datetime import datetime, timedelta
    from config import Config
    forged = jwt.encode({'sub': '1', 'role': 'SYSTEM_ADMIN', 'pwd': 0, 'exp': datetime.utcnow() + timedelta(hours=1)},
                        'wrong-key', algorithm='HS256')
    assert client.get('/api/auth/me', headers=auth(forged)).status_code == 401
    expired = jwt.encode({'sub': '1', 'role': 'SYSTEM_ADMIN', 'pwd': 0, 'exp': datetime.utcnow() - timedelta(seconds=5)},
                         Config.SECRET_KEY, algorithm='HS256')
    assert client.get('/api/auth/me', headers=auth(expired)).status_code == 401


def test_admin_login_and_me(client, admin_token):
    rv = client.get('/api/auth/me', headers=auth(admin_token))
    assert rv.status_code == 200
    assert rv.get_json()['user']['role'] == 'SYSTEM_ADMIN'
    assert 'password_hash' not in str(rv.get_json())


def test_new_user_forced_to_change_password(client, admin_token):
    rv = client.post('/api/admin/users', headers=auth(admin_token),
                     json={"email": "forced@example.test", "full_name": "Forced", "role": "READ_ONLY_ANALYST"})
    temp = rv.get_json()['temporary_password']
    tok = _login(client, 'forced@example.test', temp).get_json()['token']
    blocked = client.get('/api/geo/neighbourhoods', headers=auth(tok))
    assert blocked.status_code == 403 and blocked.get_json()['code'] == 'PASSWORD_CHANGE_REQUIRED'
    assert client.get('/api/auth/me', headers=auth(tok)).status_code == 200


def test_weak_password_rejected(client, admin_token):
    rv = client.post('/api/admin/users', headers=auth(admin_token),
                     json={"email": "weak@example.test", "full_name": "Weak", "role": "DATA_MANAGER"})
    temp = rv.get_json()['temporary_password']
    tok = _login(client, 'weak@example.test', temp).get_json()['token']
    rv = client.post('/api/auth/change-password', headers=auth(tok),
                     json={"current_password": temp, "new_password": "short1A!"})
    assert rv.status_code == 400


def test_readonly_analyst_can_analyse_but_not_change_state(client, make_user):
    _, _, tok = make_user('READ_ONLY_ANALYST')
    assert client.get('/api/geo/neighbourhoods', headers=auth(tok)).status_code == 200
    assert client.post('/api/scenarios/simulate', headers=auth(tok),
                       json={"rainfall_scenario": "HEAVY", "active_disruptions": []}).status_code == 200
    # state-changing endpoints
    assert client.post('/api/incidents', headers=auth(tok), json={}).status_code == 403
    assert client.post('/api/incidents/1/verify', headers=auth(tok), json={}).status_code == 403
    assert client.post('/api/rescue/teams/X/status', headers=auth(tok), json={}).status_code == 403
    # administration
    assert client.get('/api/admin/users', headers=auth(tok)).status_code == 403
    assert client.post('/api/admin/users', headers=auth(tok), json={}).status_code == 403


def test_operations_officer_can_change_state_but_not_administer(client, make_user):
    _, _, tok = make_user('OPERATIONS_OFFICER')
    # passes the permission gate (400/404 = reached the handler, not 403)
    assert client.post('/api/incidents/999999/verify', headers=auth(tok), json={"status": "VERIFIED"}).status_code != 403
    assert client.get('/api/admin/users', headers=auth(tok)).status_code == 403


def test_deactivated_user_loses_access_immediately(client, admin_token, make_user):
    email, _, tok = make_user('DATA_MANAGER')
    uid = [u for u in client.get('/api/admin/users', headers=auth(admin_token)).get_json()['users'] if u['email'] == email][0]['id']
    assert client.get('/api/auth/me', headers=auth(tok)).status_code == 200
    client.patch(f'/api/admin/users/{uid}', headers=auth(admin_token), json={"is_active": False})
    assert client.get('/api/auth/me', headers=auth(tok)).status_code == 401


def test_password_reset_invalidates_old_session(client, admin_token, make_user):
    email, _, tok = make_user('OPERATIONS_OFFICER')
    uid = [u for u in client.get('/api/admin/users', headers=auth(admin_token)).get_json()['users'] if u['email'] == email][0]['id']
    rv = client.post(f'/api/admin/users/{uid}/reset-password', headers=auth(admin_token))
    assert rv.status_code == 200 and rv.get_json()['temporary_password']
    assert client.get('/api/auth/me', headers=auth(tok)).status_code == 401


def test_lockout_after_repeated_failures(client, admin_token):
    client.post('/api/admin/users', headers=auth(admin_token),
                json={"email": "lock@example.test", "full_name": "Lock", "role": "READ_ONLY_ANALYST"})
    for _ in range(5):
        _login(client, 'lock@example.test', 'bad-password')
    assert _login(client, 'lock@example.test', 'bad-password').status_code == 429


def test_admin_cannot_demote_self(client, admin_token):
    me = client.get('/api/auth/me', headers=auth(admin_token)).get_json()['user']
    rv = client.patch(f"/api/admin/users/{me['id']}", headers=auth(admin_token), json={"role": "READ_ONLY_ANALYST"})
    assert rv.status_code == 400


def test_login_events_are_audited(client, admin_token):
    ev = client.get('/api/admin/audit', headers=auth(admin_token)).get_json()['events']
    kinds = {e['event'] for e in ev}
    assert {'LOGIN_SUCCESS', 'LOGIN_FAILED'} <= kinds
