import os
import secrets
import time
from typing import Optional

from fastapi import Request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from passlib.context import CryptContext

SESSION_SECRET = os.environ.get("SESSION_SECRET", "qilinhui-demo-secret-key-change-me")
_serializer = URLSafeTimedSerializer(SESSION_SECRET)

SESSION_MAX_AGE_DEFAULT = 60 * 60 * 24
SESSION_MAX_AGE_REMEMBER = 60 * 60 * 24 * 7

SESSION_STORE: dict[str, dict] = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except ValueError:
        return False


def create_session(username: str, remember: bool) -> tuple[str, int]:
    session_id = secrets.token_hex(32)
    max_age = SESSION_MAX_AGE_REMEMBER if remember else SESSION_MAX_AGE_DEFAULT
    SESSION_STORE[session_id] = {
        "username": username,
        "expires_at": time.time() + max_age,
    }
    return _serializer.dumps(session_id), max_age


def destroy_session(request: Request) -> None:
    token = request.cookies.get("session")
    if not token:
        return
    try:
        session_id = _serializer.loads(token)
    except BadSignature:
        return
    SESSION_STORE.pop(session_id, None)


def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        session_id = _serializer.loads(token)
    except BadSignature:
        return None
    session = SESSION_STORE.get(session_id)
    if session is None:
        return None
    if session["expires_at"] < time.time():
        SESSION_STORE.pop(session_id, None)
        return None
    return session["username"]