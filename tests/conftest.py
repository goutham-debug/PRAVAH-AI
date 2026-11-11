import os
import sys
import tempfile
from pathlib import Path

# Environment must be set before the backend modules are imported.
_tmp = tempfile.mkdtemp(prefix='pravah_test_')
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only-0123456789abcdef'
os.environ['DATABASE_URL'] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ['BOOTSTRAP_ADMIN_EMAIL'] = 'admin@example.test'
os.environ['BOOTSTRAP_ADMIN_PASSWORD'] = 'Bootstrap-Pass-2026!'
os.environ['LOAD_PILOT_DATASET'] = 'true'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))

import pytest  # noqa: E402


@pytest.fixture(scope='session')
def app():
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, email, password):
    return client.post('/api/auth/login', json={"email": email, "password": password})


@pytest.fixture(scope='session')
def admin_token(app):
    """Bootstrap admin signs in, sets a permanent password, returns a fresh token."""
    c = app.test_client()
    tok = _login(c, 'admin@example.test', 'Bootstrap-Pass-2026!').get_json()['token']
    rv = c.post('/api/auth/change-password', headers={'Authorization': f'Bearer {tok}'},
                json={"current_password": 'Bootstrap-Pass-2026!', "new_password": 'Permanent-Pass-2026#x'})
    return rv.get_json()['token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


import uuid

@pytest.fixture()
def make_user(client, admin_token):
    """Creates a user with a role via the admin API and returns (email, token) after password change."""
    counter = {'n': 0}

    def _make(role):
        counter['n'] += 1
        uid = uuid.uuid4().hex[:6]
        email = f"{role.lower()}{counter['n']}_{uid}@example.test"
        rv = client.post('/api/admin/users', headers=auth(admin_token),
                         json={"email": email, "full_name": "Test User", "role": role})
        assert rv.status_code == 201, rv.get_json()
        temp = rv.get_json()['temporary_password']
        tok = _login(client, email, temp).get_json()['token']
        new = 'Changed-Pass-2026$' + str(counter['n'])
        rv = client.post('/api/auth/change-password', headers=auth(tok),
                         json={"current_password": temp, "new_password": new})
        return email, new, rv.get_json()['token']
    return _make
