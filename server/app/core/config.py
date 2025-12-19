from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIC_", env_file=".env", extra="ignore")

    # DB URL 예: sqlite:///./licensing.db  또는 postgresql+psycopg://user:pass@host:5432/db
    SERVER_DB_URL: str = "sqlite:///./licensing.db"

    # 라이선스 코드 서명 및 서버 토큰 해시 등에 쓰이는 비밀키 (운영에서 반드시 교체!)
    SERVER_SECRET: str = "CHANGE_ME__LONG_RANDOM_SECRET"

    # 세션 토큰 TTL (분)
    ACCESS_TOKEN_TTL_MIN: int = 60 * 24  # 24h

    # 동일 계정 동시 세션 허용 개수 (요구사항: 1)
    MAX_CONCURRENT_SESSIONS_PER_USER: int = 1

settings = Settings()
