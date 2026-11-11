"""User administration. SYSTEM_ADMIN only (enforced centrally in security.enforce_request_policy)."""
import secrets
import string
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from database import SessionLocal
from models import User, LoginAudit
from security import hash_password, validate_password_strength, ROLES, client_ip

admin_bp = Blueprint('admin', __name__)


def _temp_password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
    while True:
        pw = ''.join(secrets.choice(alphabet) for _ in range(16))
        if validate_password_strength(pw) is None:
            return pw


def _audit(session, event, target, detail=None):
    session.add(LoginAudit(user_id=g.current_user.id, email=target.email, event=event,
                           ip_address=client_ip(), detail=detail))


@admin_bp.route('/users', methods=['GET'])
def list_users():
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        return jsonify({"success": True, "users": [u.to_dict() for u in users]})
    finally:
        session.close()


@admin_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    name = str(data.get('full_name', '')).strip()
    role = data.get('role')
    if '@' not in email or not name or role not in ROLES:
        return jsonify({"success": False, "error": "Valid email, full name and role are required."}), 400
    session = SessionLocal()
    try:
        if session.query(User).filter(User.email == email).first():
            return jsonify({"success": False, "error": "An account with this email already exists."}), 409
        temp = _temp_password()
        user = User(email=email, full_name=name, role=role, phone=data.get('phone'),
                    password_hash=hash_password(temp), must_change_password=True,
                    password_changed_at=datetime.utcnow())
        session.add(user)
        session.flush()
        _audit(session, 'USER_CREATED', user, role)
        session.commit()
        return jsonify({"success": True, "user": user.to_dict(), "temporary_password": temp}), 201
    finally:
        session.close()


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id: int):
    data = request.get_json(silent=True) or {}
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found."}), 404
        if user.id == g.current_user.id and (data.get('is_active') is False or data.get('role', user.role) != user.role):
            return jsonify({"success": False, "error": "You cannot deactivate or change the role of your own account."}), 400
        if 'role' in data:
            if data['role'] not in ROLES:
                return jsonify({"success": False, "error": "Unknown role."}), 400
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        _audit(session, 'USER_UPDATED', user, f"role={user.role} active={user.is_active}")
        session.commit()
        return jsonify({"success": True, "user": user.to_dict()})
    finally:
        session.close()


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id: int):
    """Password reset workflow: administrator issues a one-time temporary password;
    the user must replace it at next sign-in and all existing sessions are invalidated."""
    session = SessionLocal()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found."}), 404
        temp = _temp_password()
        user.password_hash = hash_password(temp)
        user.must_change_password = True
        user.password_changed_at = datetime.utcnow()
        _audit(session, 'PASSWORD_RESET', user)
        session.commit()
        return jsonify({"success": True, "temporary_password": temp})
    finally:
        session.close()


@admin_bp.route('/audit', methods=['GET'])
def audit_log():
    limit = min(int(request.args.get('limit', 100)), 500)
    session = SessionLocal()
    try:
        rows = session.query(LoginAudit).order_by(LoginAudit.created_at.desc()).limit(limit).all()
        return jsonify({"success": True, "events": [r.to_dict() for r in rows]})
    finally:
        session.close()
