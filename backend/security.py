"""Authentication helpers, role policy and request guards."""
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config

ROLES = {
    'SYSTEM_ADMIN': 'System Administrator',
    'DISASTER_OFFICER': 'Disaster Management Officer',
    'OPERATIONS_OFFICER': 'Operations Officer',
    'DATA_MANAGER': 'Data Manager',
    'READ_ONLY_ANALYST': 'Read-only Analyst',
}

# State-changing endpoints (incident records, response-team status) require an operational role.
# Analysis endpoints (simulate, compare, assess, allocate, coordinate, route, sitrep) only compute from stored
# data and persist nothing, so every authenticated role may call them. User administration is SYSTEM_ADMIN only.
_OPERATIONAL = {'SYSTEM_ADMIN', 'DISASTER_OFFICER', 'OPERATIONS_OFFICER'}
WRITE_POLICY = {
    '/api/incidents': _OPERATIONAL,
    '/api/rescue/teams': _OPERATIONAL,
    '/api/admin': {'SYSTEM_ADMIN'},
    '/api/dataops': {'SYSTEM_ADMIN', 'DATA_MANAGER'},   # trigger ingestion
}
# Data Operations is restricted even for reading (backend internals, provider status, failed requests).
READ_POLICY = {
    '/api/dataops': {'SYSTEM_ADMIN', 'DATA_MANAGER', 'DISASTER_OFFICER'},
}
# POST endpoints that are computations, not mutations
COMPUTE_ENDPOINTS = {
    '/api/scenarios/simulate', '/api/scenarios/compare', '/api/flood/assess', '/api/facilities/accessibility',
    '/api/shelters/allocate', '/api/rescue/coordinate', '/api/roads/route',
    '/api/sitrep/generate', '/api/sitrep/export/markdown', '/api/ai/query',
}

PUBLIC_ENDPOINTS = {'/api/health', '/api/auth/login', '/api/monitor/health', '/api/monitor/events'}


def hash_password(password: str) -> str:
    return generate_password_hash(password, method='scrypt')


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def validate_password_strength(password: str, email: str = '') -> str | None:
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        return f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters."
    local = email.split('@')[0].lower()
    if len(local) >= 4 and local in password.lower():
        return "Password must not contain the email address."
    classes = sum([any(c.islower() for c in password), any(c.isupper() for c in password),
                   any(c.isdigit() for c in password), any(not c.isalnum() for c in password)])
    if classes < 3:
        return "Use at least three of: lowercase, uppercase, digits, symbols."
    return None


def issue_token(user) -> str:
    now = datetime.utcnow()
    payload = {
        'sub': str(user.id),
        'role': user.role,
        'pwd': user.password_changed_at.timestamp() if user.password_changed_at else 0,
        'iat': now,
        'exp': now + timedelta(hours=Config.SESSION_HOURS),
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')


def _authenticate_request():
    """Returns (user, error_response). Loads the user from DB on every call so that
    deactivation, role change and password change take effect immediately."""
    from database import SessionLocal
    from models import User

    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None, (jsonify({"success": False, "error": "Authentication required."}), 401)
    try:
        payload = jwt.decode(header[7:], Config.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"success": False, "error": "Session expired. Please sign in again."}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"success": False, "error": "Invalid session."}), 401)

    session = SessionLocal()
    try:
        user = session.get(User, int(payload['sub']))
        if not user or not user.is_active:
            return None, (jsonify({"success": False, "error": "Account is inactive."}), 401)
        pwd_ts = user.password_changed_at.timestamp() if user.password_changed_at else 0
        if abs(pwd_ts - payload.get('pwd', 0)) > 0.001:
            return None, (jsonify({"success": False, "error": "Session no longer valid. Please sign in again."}), 401)
        session.expunge(user)
        return user, None
    finally:
        session.close()


def enforce_request_policy():
    """Flask before_request hook: every /api route is protected unless listed as public."""
    path = request.path
    if request.method == 'OPTIONS' or not path.startswith('/api/'):
        return None
    if path in PUBLIC_ENDPOINTS:
        return None

    user, err = _authenticate_request()
    if err:
        return err
    g.current_user = user

    # A user who must set a new password may only change it or log out.
    if user.must_change_password and path not in ('/api/auth/change-password', '/api/auth/logout', '/api/auth/me'):
        return jsonify({"success": False, "error": "Password change required.", "code": "PASSWORD_CHANGE_REQUIRED"}), 403

    for prefix, allowed in READ_POLICY.items():
        if path.startswith(prefix) and user.role not in allowed:
            return jsonify({"success": False, "error": "You do not have permission for this action."}), 403

    if request.method not in ('GET', 'HEAD') and path not in COMPUTE_ENDPOINTS:
        for prefix, allowed in WRITE_POLICY.items():
            if path.startswith(prefix):
                if user.role not in allowed:
                    return jsonify({"success": False, "error": "You do not have permission for this action."}), 403
                break
    elif path.startswith('/api/admin') and user.role != 'SYSTEM_ADMIN':
        return jsonify({"success": False, "error": "You do not have permission for this action."}), 403
    return None


def client_ip() -> str:
    return (request.headers.get('X-Forwarded-For', request.remote_addr or '') or '').split(',')[0].strip()[:64]
