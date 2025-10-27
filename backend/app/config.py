from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trading Matchmaking Platform"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg2://postgres:Jwhfdls9@has4b9s5ce-proxy.north-cn-hangzhou.mysql.polardb.rds.aliyuncs.com:5432/postgres"
    )
    test_database_url: Optional[str] = None
    jwt_secret_key: str = "supersecretkey"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    sms_code_expire_minutes: int = 5
    sms_attempt_lock_minutes: int = 60
    sms_max_attempts: int = 3
    invite_reward_inviter: int = 10
    invite_reward_invitee: int = 30
    registration_bonus: int = 100
    post_publish_cost: int = 10
    contact_view_cost: int = 1
    post_default_view_quota: int = 10
    post_valid_hours: int = 72
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
