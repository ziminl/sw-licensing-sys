from __future__ import annotations
import os
from pathlib import Path

# 클라이언트 설정
SERVER_BASE_URL = "http://127.0.0.1:8000"  # 운영에서는 https:// 로
PRODUCT_CODE = "demo_paid"  # demo_free 또는 demo_paid

APP_NAME = "DemoApp"

def get_state_path() -> str:
    """PyInstaller(onefile)에서도 항상 쓰기 가능한 위치를 사용."""
    # Windows: %APPDATA%\DemoApp\license_state.json
    base = os.getenv("APPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return str(p / "license_state.json")
