## 시스템 개요 (요약)
- 클라이언트(파이썬 스크립트/pyinstaller exe)는 실행 시작 시:
  1) HWID 생성 후 SHA-256 해시
  2) 서버 로그인 → 세션 토큰 발급(동시 세션 정책 검사)
  3) 제품이 Paid이면: 라이선스 코드 redeem → validate
  4) 검증 실패 시 즉시 종료, 성공 시 앱 핵심 로직 실행
  5) 종료 시 logout 호출로 세션 해제

## 동시 세션 정책
- `sessions` 테이블에 활성 세션을 저장
- 로그인 시 동일 user_id로 is_active=True 세션이 있으면 거절
- TTL 경과 세션은 로그인 시/요청 시 만료 처리

## HWID 정책
- Windows에서 가능한 식별자(CPU/BIOS/DISK/MachineGuid/MAC)를 조합해 해시 생성
- 라이선스 redeem 시 최초 HWID에 bind
- 이후 validate 시 HWID 불일치면 무효(재인증 요구)
