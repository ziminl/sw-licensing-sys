from __future__ import annotations
from passlib.context import CryptContext
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hmac_sha256(secret: str, msg: bytes) -> bytes:
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()

def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def expires_at_from_now(minutes: int) -> datetime:
    return utcnow() + timedelta(minutes=minutes)
