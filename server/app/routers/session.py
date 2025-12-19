from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.deps import get_current_user, get_current_session

router = APIRouter(prefix="/session", tags=["session"])

@router.get("/me")
def me(user: models.User = Depends(get_current_user), sess: models.Session = Depends(get_current_session)):
    return {
        "email": user.email,
        "hwid_hash": sess.hwid_hash,
        "created_at": sess.created_at,
        "last_seen_at": sess.last_seen_at,
        "is_active": sess.is_active,
    }
