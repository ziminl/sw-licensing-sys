from __future__ import annotations
import getpass
import sys
import traceback
from api import LicensingApi, ApiError
from hwid import hwid_hash_sha256
from state import load_state, save_state
import config

def _fatal(msg: str, code: int = 1) -> None:
    print(f"[FATAL] {msg}")
    sys.exit(code)

def _prompt_email_password():
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ").strip()
    return email, password

def _prompt_license():
    return input("License Code: ").strip()

def run_business_logic():
    # 실제 앱의 핵심 로직/기능은 여기에 들어갑니다.
    # 이 예제에서는 간단히 메시지만 출력합니다.
    print("\n✅ 인증 성공! 이제 유료/무료 소프트웨어 기능을 실행합니다...\n")
    print("... (여기에 실제 프로그램 기능 구현) ...")
    input("\n엔터를 누르면 종료합니다...")

def main():
    hwid = hwid_hash_sha256()
    api = LicensingApi(config.SERVER_BASE_URL)
    state_path = config.get_state_path()
    state = load_state(state_path)

    try:
        # 제품 정보 조회 (Free/Paid 분기)
        product = api.get_product(config.PRODUCT_CODE)
        is_paid = bool(product["is_paid"])
        print(f"Product: {product['name']} ({product['code']}) / paid={is_paid}")
        print(f"HWID hash: {hwid}")
        print(f"State file: {state_path}")

        # 로그인 (동시 세션 정책: 이미 활성 세션 있으면 서버가 거절)
        email = state.get("email") or ""
        if email:
            use_saved = input(f"Use saved email '{email}'? (Y/n): ").strip().lower() != "n"
        else:
            use_saved = False

        if not use_saved:
            email, password = _prompt_email_password()
        else:
            # 비밀번호는 로컬에 저장하지 않는 것을 권장. (샘플에서는 매번 입력)
            password = getpass.getpass("Password: ").strip()

        token_resp = api.login(email, password, hwid)
        token = token_resp["access_token"]
        print("✅ Login OK. Session token issued.")
        state["email"] = email
        save_state(state_path, state)

        try:
            # Paid이면 라이선스 등록/검증 필수
            if is_paid:
                license_code = state.get("license_code")
                if not license_code:
                    print("\n유료 제품입니다. 라이선스 코드 등록이 필요합니다.")
                    license_code = _prompt_license()
                    redeem = api.redeem_license(token, config.PRODUCT_CODE, license_code, hwid)
                    print("✅ License redeemed:", redeem)
                    state["license_code"] = license_code
                    save_state(state_path, state)

                # 라이선스 검증
                v = api.validate_license(token, config.PRODUCT_CODE, hwid)
                if not v.get("valid"):
                    _fatal(f"License validation failed: {v}")
                print("✅ License validation OK.", v)
            else:
                # Free면 로그인만으로 OK (서버 validate도 true)
                v = api.validate_license(token, config.PRODUCT_CODE, hwid)
                if not v.get("valid"):
                    _fatal(f"Validation failed: {v}")
                print("✅ Free product validation OK.")

            # 여기까지 통과해야 앱 실행
            run_business_logic()

        finally:
            # 로그아웃(세션 해제) - 실패해도 앱 종료는 진행
            try:
                api.logout(token)
                print("✅ Logout OK.")
            except Exception as e:
                print(f"[WARN] logout failed: {e}")

    except ApiError as e:
        _fatal(str(e))
    except KeyboardInterrupt:
        _fatal("Interrupted.", 130)
    except Exception as e:
        traceback.print_exc()
        _fatal(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
