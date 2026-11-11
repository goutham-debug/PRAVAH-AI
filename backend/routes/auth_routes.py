from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g

from config import Config
from database import SessionLocal
from models import User, LoginAudit
from security import (hash_password, verify_password, validate_password_strength, issue_token,
                      client_ip, ROLES)

auth_bp = Blueprint('auth', __name__)

# Constant-cost dummy hash so unknown emails take as long as wrong passwords.
_DUMMY_HASH = hash_password("not-a-real-password-0Aa!")


def _audit(session, event, email, user_id=None, detail=None):
    session.add(LoginAudit(
        user_id=user_id, email=email[:254], event=event, ip_address=client_ip(),
        user_agent=(request.headers.get('User-Agent') or '')[:255], detail=detail,
    ))


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    if not email or not password:
        return jsonify({"success": False, "error": "Enter your email and password."}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        now = datetime.utcnow()

        if user and user.locked_until and user.locked_until > now:
            _audit(session, 'LOGIN_LOCKED', email, user.id)
            session.commit()
            return jsonify({"success": False, "error": "Account temporarily locked after repeated failed attempts. Try again later."}), 429

        ok = verify_password(user.password_hash if user else _DUMMY_HASH, password)
        if not user or not ok or not user.is_active:
            if user:
                user.failed_logins = (user.failed_logins or 0) + 1
                if user.failed_logins >= Config.MAX_FAILED_LOGINS:
                    user.locked_until = now + timedelta(minutes=Config.LOCKOUT_MINUTES)
                    user.failed_logins = 0
            _audit(session, 'LOGIN_FAILED', email, user.id if user else None,
                   'inactive' if user and ok and not user.is_active else None)
            session.commit()
            return jsonify({"success": False, "error": "Incorrect email or password."}), 401

        user.failed_logins = 0
        user.locked_until = None
        user.last_login_at = now
        _audit(session, 'LOGIN_SUCCESS', email, user.id)
        session.commit()
        return jsonify({"success": True, "token": issue_token(user), "user": user.to_dict(),
                        "session_hours": Config.SESSION_HOURS})
    finally:
        session.close()


@auth_bp.route('/me', methods=['GET'])
def me():
    return jsonify({"success": True, "user": g.current_user.to_dict()})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session = SessionLocal()
    try:
        _audit(session, 'LOGOUT', g.current_user.email, g.current_user.id)
        session.commit()
    finally:
        session.close()
    return jsonify({"success": True})


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json(silent=True) or {}
    current, new = str(data.get('current_password', '')), str(data.get('new_password', ''))
    session = SessionLocal()
    try:
        user = session.get(User, g.current_user.id)
        if not verify_password(user.password_hash, current):
            return jsonify({"success": False, "error": "Current password is incorrect."}), 400
        problem = validate_password_strength(new, user.email)
        if problem:
            return jsonify({"success": False, "error": problem}), 400
        if verify_password(user.password_hash, new):
            return jsonify({"success": False, "error": "New password must differ from the current one."}), 400
        user.password_hash = hash_password(new)
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = False
        _audit(session, 'PASSWORD_CHANGED', user.email, user.id)
        session.commit()
        # Issue a fresh token: older sessions are invalidated by the password timestamp.
        return jsonify({"success": True, "token": issue_token(user), "user": user.to_dict()})
    finally:
        session.close()


@auth_bp.route('/roles', methods=['GET'])
def roles():
    return jsonify({"success": True, "roles": [{"id": k, "label": v} for k, v in ROLES.items()]})
