from __future__ import annotations
import base64, json
from datetime import datetime
from typing import Any, Optional, Tuple
from app.core.security import hmac_sha256, constant_time_equal
from app.core.config import settings

# 라이선스 코드 포맷:
#   LIC1.<b32(payload_json)>. <b32(sig)>
# payload 예:
#   {"v":1,"product":"demo_paid","exp":"2030-01-01T00:00:00Z","nonce":"..."}  # exp는 선택
#
# - 위변조 방지: sig = HMAC-SHA256(secret, payload_bytes)
# - DB에 코드를 저장해 redeem 상태/바인딩/정지(revoke) 관리

PREFIX = "LIC1"

def _b32e(b: bytes) -> str:
    return base64.b32encode(b).decode("ascii").rstrip("=")

def _b32d(s: str) -> bytes:
    pad = "=" * ((8 - (len(s) % 8)) % 8)
    return base64.b32decode((s + pad).encode("ascii"))

def encode_license(payload: dict[str, Any], secret: str | None = None) -> str:
    if secret is None:
        secret = settings.SERVER_SECRET
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac_sha256(secret, payload_bytes)
    return f"{PREFIX}.{_b32e(payload_bytes)}.{_b32e(sig)}"

def decode_and_verify(code: str, secret: str | None = None) -> Tuple[dict[str, Any], Optional[str]]:
    """return (payload, error). error is None if OK."""
    if secret is None:
        secret = settings.SERVER_SECRET
    parts = code.strip().split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        return {}, "INVALID_FORMAT"
    try:
        payload_bytes = _b32d(parts[1])
        sig = _b32d(parts[2])
    except Exception:
        return {}, "INVALID_BASE32"

    expected = hmac_sha256(secret, payload_bytes)
    if not constant_time_equal(expected, sig):
        return {}, "INVALID_SIGNATURE"

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return {}, "INVALID_PAYLOAD"

    # 기본 필드 확인
    if payload.get("v") != 1 or "product" not in payload or "nonce" not in payload:
        return {}, "INVALID_FIELDS"

    # exp 확인(옵션)
    exp = payload.get("exp")
    if exp:
        try:
            # exp는 ISO8601 Z
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return {}, "INVALID_EXP"
        if datetime.utcnow() > exp_dt:
            return {}, "EXPIRED"
    return payload, None

def payload_exp_datetime(payload: dict[str, Any]) -> Optional[datetime]:
    exp = payload.get("exp")
    if not exp:
        return None
    return datetime.fromisoformat(exp.replace("Z", "+00:00")).replace(tzinfo=None)
