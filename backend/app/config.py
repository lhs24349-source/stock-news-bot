"""
Pydantic Settings 기반 환경 변수 설정.

모든 환경 변수를 타입 안전하게 관리하며,
누락된 필수 값에 대해 명시적 에러 메시지를 제공합니다.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """앱 전역 설정. .env 파일에서 자동 로딩됩니다."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 알 수 없는 환경 변수 무시
    )

    # ── 앱 기본 ──────────────────────────────────────────────
    app_name: str = "stock-news-bot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ── 데이터베이스 ─────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./stock_news.db"

    # ── Redis (선택) ─────────────────────────────────────────
    redis_url: Optional[str] = None

    # ── Telegram (선택) ──────────────────────────────────────
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # ── Discord (선택) ───────────────────────────────────────
    discord_webhook_url: Optional[str] = None

    # ── Gmail (선택) ─────────────────────────────────────────
    gmail_address: Optional[str] = None
    gmail_app_password: Optional[str] = None
    gmail_recipients: Optional[str] = None  # 쉼표 구분 이메일 목록

    # ── RSS ───────────────────────────────────────────────────
    naver_rss_url: str = (
        "https://finance.naver.com/rss/headline.naver?catId=101"
    )
    google_news_rss_url: str = (
        "https://news.google.com/rss/search?"
        "q={keyword}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    )

    # ── Alpha Vantage (선택) ─────────────────────────────────
    alpha_vantage_api_key: Optional[str] = None

    # ── 스케줄러 ─────────────────────────────────────────────
    scheduler_default_interval_minutes: int = 30
    scheduler_timezone: str = "Asia/Seoul"

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Sentry (선택) ────────────────────────────────────────
    sentry_dsn: Optional[str] = None

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """로그 레벨을 대문자로 정규화하고 유효성 검증."""
        v = v.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid_levels:
            raise ValueError(
                f"유효하지 않은 로그 레벨: {v}. "
                f"허용값: {', '.join(sorted(valid_levels))}"
            )
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS 오리진을 리스트로 반환."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def gmail_recipient_list(self) -> list[str]:
        """Gmail 수신자를 리스트로 반환."""
        if not self.gmail_recipients:
            return []
        return [
            r.strip() for r in self.gmail_recipients.split(",") if r.strip()
        ]

    @property
    def is_telegram_configured(self) -> bool:
        """Telegram 알림이 설정되었는지 확인."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def is_discord_configured(self) -> bool:
        """Discord 알림이 설정되었는지 확인."""
        return bool(self.discord_webhook_url)

    @property
    def is_gmail_configured(self) -> bool:
        """Gmail 알림이 설정되었는지 확인."""
        return bool(
            self.gmail_address
            and self.gmail_app_password
            and self.gmail_recipients
        )

    @property
    def is_redis_configured(self) -> bool:
        """Redis가 설정되었는지 확인."""
        return bool(self.redis_url)

    def mask_secret(self, value: Optional[str]) -> str:
        """비밀 값을 마스킹 처리하여 로그 안전하게 표시.

        예: "123456789:ABCdef" → "1234****def"
        """
        if not value:
            return "(미설정)"
        if len(value) <= 8:
            return "****"
        return f"{value[:4]}****{value[-3:]}"


# 싱글턴 인스턴스 (앱 전체에서 공유)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 싱글턴을 반환합니다.

    최초 호출 시 .env 파일을 읽어 Settings 인스턴스를 생성합니다.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
