from typing import Literal

from fastapi import HTTPException, Security, WebSocket
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.common.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

Role = Literal["admin", "user"]


def get_api_role(api_key: str | None = Security(api_key_header)) -> Role:
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if api_key == settings.admin_api_key:
        return "admin"

    if api_key == settings.user_api_key:
        return "user"

    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )


def require_user_or_admin(role: Role = Security(get_api_role)) -> Role:
    return role


def require_admin(role: Role = Security(get_api_role)) -> Role:
    if role != "admin":
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return role

