from __future__ import annotations
import argparse
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import json

# 서버와 동일한 로직을 사용하도록 import (server/app 을 PYTHONPATH에 추가해서 실행하는 방식)
# 간단히 이 파일은 독립 실행을 위해 같은 구현을 포함합니다.
import base64, hashlib, hmac

PREFIX = "LIC1"

def _b32e(b: bytes) -> str:
    return base64.b32encode(b).decode("ascii").rstrip("=")

def hmac_sha256(secret: str, msg: bytes) -> bytes:
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()

def encode_license(payload: dict, secret: str) -> str:
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac_sha256(secret, payload_bytes)
    return f"{PREFIX}.{_b32e(payload_bytes)}.{_b32e(sig)}"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--product", required=True, help="예: demo_paid")
    p.add_argument("--days", type=int, default=3650, help="만료까지 일수 (0이면 만료 없음)")
    p.add_argument("--secret", default=os.environ.get("LIC_SERVER_SECRET", ""), help="서버와 동일한 비밀키")
    p.add_argument("--count", type=int, default=1)
    args = p.parse_args()

    if not args.secret:
        raise SystemExit("ERROR: --secret 또는 환경변수 LIC_SERVER_SECRET 필요")

    codes = []
    for _ in range(args.count):
        payload = {"v": 1, "product": args.product, "nonce": secrets.token_hex(16)}
        if args.days and args.days > 0:
            exp = datetime.now(timezone.utc) + timedelta(days=args.days)
            payload["exp"] = exp.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        codes.append(encode_license(payload, args.secret))

    for c in codes:
        print(c)

if __name__ == "__main__":
    main()
