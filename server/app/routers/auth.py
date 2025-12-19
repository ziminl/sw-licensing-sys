from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db.database import get_db
from app.db import models
from app.core.schemas import RegisterRequest, LoginRequest, TokenResponse, LogoutResponse
from app.core.security import hash_password, verify_password, sha256_hex, utcnow, expires_at_from_now
from app.core.config import settings
from app.core.deps import get_current_session

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    u = models.User(email=req.email, password_hash=hash_password(req.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"ok": True, "email": u.email}

def _active_sessions_for_user(db: Session, user_id: int):
    return (
        db.query(models.Session)
          .filter(models.Session.user_id == user_id, models.Session.is_active == True)  # noqa: E712
          .all()
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.email == req.email).first()
    if not u or not verify_password(req.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 동시 세션 차단: 이미 활성 세션이 있으면 로그인 차단
    active = _active_sessions_for_user(db, u.id)
    # TTL 만료된 세션은 정리
    cleaned = []
    for s in active:
        ttl_sec = settings.ACCESS_TOKEN_TTL_MIN * 60
        if (utcnow() - s.last_seen_at).total_seconds() > ttl_sec:
            s.is_active = False
            s.revoked_at = utcnow()
            s.revoke_reason = "EXPIRED"
            cleaned.append(s)
    if cleaned:
        db.commit()

    active = _active_sessions_for_user(db, u.id)
    if len(active) >= settings.MAX_CONCURRENT_SESSIONS_PER_USER:
        # 요구사항: 동일 계정으로 2대 이상 로그인 불가. 활성 세션 존재 시 로그인 차단.
        raise HTTPException(status_code=403, detail="Active session exists. Logout first.")

    # 새 세션 발급
    raw_token = str(uuid4()) + str(uuid4())  # 길게
    token_hash = sha256_hex(raw_token.encode("utf-8"))
    s = models.Session(
        user_id=u.id,
        token_hash=token_hash,
        hwid_hash=req.hwid_hash,
        created_at=utcnow(),
        last_seen_at=utcnow(),
        is_active=True,
    )
    db.add(s)
    db.commit()

    return TokenResponse(
        access_token=raw_token,
        user_email=u.email,
        session_expires_at=expires_at_from_now(settings.ACCESS_TOKEN_TTL_MIN),
    )

@router.post("/logout", response_model=LogoutResponse)
def logout(sess = Depends(get_current_session), db: Session = Depends(get_db)):
    sess.is_active = False
    sess.revoked_at = utcnow()
    sess.revoke_reason = "LOGOUT"
    db.commit()
    return LogoutResponse(ok=True)
