from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db import models
from app.core.security import sha256_hex, utcnow, expires_at_from_now
from app.core.config import settings

bearer = HTTPBearer(auto_error=False)

def _session_is_expired(s: models.Session) -> bool:
    # last_seen 기준 TTL
    ttl = settings.ACCESS_TOKEN_TTL_MIN
    return (utcnow() - s.last_seen_at).total_seconds() > ttl * 60

def get_current_session(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.Session:
    if creds is None or not creds.scheme.lower().startswith("bearer"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = creds.credentials.strip()
    token_hash = sha256_hex(token.encode("utf-8"))

    s = db.query(models.Session).filter(models.Session.token_hash == token_hash).first()
    if not s or not s.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    if _session_is_expired(s):
        s.is_active = False
        s.revoked_at = utcnow()
        s.revoke_reason = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    # last_seen 갱신
    s.last_seen_at = utcnow()
    db.commit()
    db.refresh(s)
    return s

def get_current_user(
    sess: models.Session = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> models.User:
    u = db.query(models.User).filter(models.User.id == sess.user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return u
