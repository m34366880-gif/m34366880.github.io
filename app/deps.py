import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal


http_basic = HTTPBasic()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_client_ip(request: Request) -> str:
    # Prefer X-Forwarded-For if present (first IP), else fall back to client.host
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    client_ip = request.client.host if request.client else ""
    return client_ip


def admin_ip_check(request: Request):
    client_ip = _extract_client_ip(request)
    if client_ip != settings.admin_allowed_ip:
        # Hide details about IP policy to avoid information leakage
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def admin_basic_auth(credentials: HTTPBasicCredentials = Depends(http_basic)):
    valid_user = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


def admin_guard(
    _: None = Depends(admin_ip_check),
    __: None = Depends(admin_basic_auth),
):
    # If both dependencies pass, request is authorized
    return None
