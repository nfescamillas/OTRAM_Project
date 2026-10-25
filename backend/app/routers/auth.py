from fastapi import APIRouter, HTTPException, Request

from ..auth import verify_password
from ..models import LoginRequest, PublicUser, TokenResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse, operation_id="createToken")
def create_token(payload: LoginRequest, request: Request) -> TokenResponse:
    user = request.app.state.store.user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.passwordHash):
        request.app.state.metrics.auth_attempts.add(1, {"result": "failure"})
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHENTICATED", "message": "The email or password is incorrect."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.app.state.metrics.auth_attempts.add(1, {"result": "success"})
    service = request.app.state.token_service
    return TokenResponse(
        accessToken=service.issue(user),
        expiresIn=service.ttl_seconds,
        user=PublicUser(id=user.id, email=user.email, displayName=user.displayName, role=user.role),
    )
