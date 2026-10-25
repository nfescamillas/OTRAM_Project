from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import Role, UserRecord


PASSWORD_ITERATIONS = 310_000
bearer_scheme = HTTPBearer(auto_error=False)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = PASSWORD_ITERATIONS) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, _ = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hash_password(password, salt=_b64decode(raw_salt), iterations=int(raw_iterations))
        return hmac.compare_digest(candidate, encoded)
    except (ValueError, TypeError):
        return False


class TokenService:
    def __init__(self, secret: bytes, ttl_seconds: int = 3600) -> None:
        if len(secret) < 32:
            raise ValueError("Token secret must be at least 32 bytes")
        self._secret = secret
        self.ttl_seconds = ttl_seconds

    def issue(self, user: UserRecord) -> str:
        payload = {"sub": user.id, "org": user.organizationId, "role": user.role.value,
                   "exp": int(time.time()) + self.ttl_seconds, "nonce": secrets.token_hex(8)}
        encoded = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signature = _b64encode(hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> dict[str, object]:
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64encode(hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise ValueError("invalid signature")
            payload = json.loads(_b64decode(encoded))
            if not isinstance(payload, dict) or int(payload["exp"]) <= int(time.time()):
                raise ValueError("expired token")
            return payload
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "The bearer token is invalid or expired."}, headers={"WWW-Authenticate": "Bearer"}) from exc


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> UserRecord:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "A bearer token is required."}, headers={"WWW-Authenticate": "Bearer"})
    payload = request.app.state.token_service.verify(credentials.credentials)
    user = request.app.state.store.user_by_id(str(payload["sub"]))
    if user is None or user.organizationId != payload.get("org") or user.role.value != payload.get("role"):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "The bearer token is no longer valid."}, headers={"WWW-Authenticate": "Bearer"})
    return user


def require_roles(*allowed: Role) -> Callable[..., UserRecord]:
    def dependency(request: Request, user: UserRecord = Depends(get_current_user)) -> UserRecord:
        if user.role not in allowed:
            request.app.state.metrics.authorization_denials.add(1, {
                "reason": "role",
                "role": user.role.value,
            })
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "You are not authorized to perform this operation."})
        return user
    return dependency
