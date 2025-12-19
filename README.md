# HWID 기반 하드웨어 락(Hardware Lock) 라이선싱 예제 (FastAPI + Python Client)

> 목적: 합법적인 상용 라이선싱/로그인/세션 제어/하드웨어 락(HWID) 바인딩의 **동작 가능한 최소 레퍼런스 구현**입니다.
> - Free 제품: 로그인만 하면 사용 가능
> - Paid 제품: 라이선스 코드 redeem + validate 통과해야 사용 가능
> - 동일 계정 동시 세션: **1개만 허용(1 PC 1 세션)**

## 1) 구성
- `server/` : FastAPI 라이선스 서버 (SQLite 기본)
- `client/` : 실제 실행 가능한 클라이언트(스크립트/pyinstaller exe용 엔트리)
- `admin_tools/` : 라이선스 코드 생성 CLI (서버 비밀키 사용)

## 2) 빠른 실행 (로컬 개발)
### 서버
```bash
cd server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# (Windows PowerShell) 환경변수 설정 예:
$env:LIC_SERVER_DB_URL="sqlite:///./licensing.db"
$env:LIC_SERVER_SECRET="CHANGE_ME__LONG_RANDOM_SECRET"
$env:LIC_ACCESS_TOKEN_TTL_MIN="1440"

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

서버가 올라오면 자동으로 기본 제품이 2개 생성됩니다.
- `demo_free` (Free)
- `demo_paid` (Paid)

### 클라이언트
```bash
cd client
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 제품 선택 (FREE/PAID 테스트)
# config.py 의 PRODUCT_CODE 를 demo_free 또는 demo_paid 로 바꿔서 실행하세요.
python main.py
```

## 3) PyInstaller 빌드 (Windows exe)
클라이언트 폴더에서:
```bash
pip install pyinstaller
pyinstaller --onefile --name DemoApp main.py
```
- 생성된 `dist/DemoApp.exe` 실행 시, 로그인/라이선스 검증 실패하면 즉시 종료합니다.
- exe 내부에 “서버 비밀키”를 넣지 않습니다. 검증은 서버가 합니다.

## 4) 운영 배포 참고
- HTTPS(TLS)는 리버스 프록시(Nginx/Caddy) 또는 uvicorn SSL로 구성하세요.
- `LIC_SERVER_SECRET` 는 안전한 비밀 관리(환경변수/Secret Manager)에 보관하세요.
- SQLite는 데모용이며, 운영은 PostgreSQL 권장 (DB URL만 변경).

## 5) 보안/한계
- HWID는 “기계 고유성”을 근사합니다. 부품 교체/가상화/권한 제한 등으로 변할 수 있습니다.
- 상용 제품 수준에서는:
  - 재인증/이전(transfer) 정책
  - 디바이스 목록/관리자 승인
  - 주기적 재검증(heartbeat)
  - 코드 난독화/안티탬퍼(합법 범위 내)
  등을 추가하세요.
