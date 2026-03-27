import hashlib
import hmac
import os
import secrets

from database import (
    create_user,
    create_user_session,
    delete_user_session,
    get_user_by_email,
    get_user_by_session_token,
)


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password, stored_value):
    try:
        salt_hex, hash_hex = stored_value.split(":", 1)
    except ValueError:
        return False

    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        100000,
    ).hex()
    return hmac.compare_digest(new_hash, hash_hex)


def register_user(full_name, email, password, role="student"):
    if len(full_name.strip()) < 2:
        return False, "Please enter a valid full name."
    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if get_user_by_email(email):
        return False, "An account with this email already exists."

    password_hash = hash_password(password)
    create_user(full_name.strip(), email.strip(), password_hash, role=role)
    return True, "Account created successfully."


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return dict(user)


def ensure_admin_user():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@interviewsimulator.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")
    admin_name = os.getenv("ADMIN_NAME", "Project Admin")

    if not get_user_by_email(admin_email):
        create_user(admin_name, admin_email, hash_password(admin_password), role="admin")

    return {
        "email": admin_email,
        "password": admin_password,
    }


def create_persistent_session(user_id):
    session_token = secrets.token_urlsafe(32)
    create_user_session(user_id, session_token)
    return session_token


def authenticate_session_token(session_token):
    if not session_token:
        return None
    user = get_user_by_session_token(session_token)
    return dict(user) if user else None


def logout_session_token(session_token):
    if session_token:
        delete_user_session(session_token)
