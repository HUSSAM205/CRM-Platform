import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()

TokenType = Literal["access", "refresh"]


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_token(subject: str, token_type: TokenType, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
        secret = settings.jwt_secret
    else:
        expire = now + timedelta(days=settings.refresh_token_expire_days)
        secret = settings.refresh_secret

    payload: dict[str, Any] = {"sub": subject, "type": token_type, "iat": now, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def hash_token(token: str) -> str:
    """SHA-256 digest used to store/look up refresh tokens without keeping the raw secret at rest.

    Unlike passwords, refresh tokens are already high-entropy random strings, so a fast
    cryptographic hash (rather than a slow, memory-hard KDF like Argon2) is sufficient and
    keeps refresh/logout lookups cheap.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_token(token: str, token_type: TokenType) -> dict[str, Any] | None:
    secret = settings.jwt_secret if token_type == "access" else settings.refresh_secret
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("type") != token_type:
        return None
    return payload
