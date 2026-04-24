"""
알림 채널 모델.

Telegram, Discord, Gmail 채널의 연결 정보를 저장합니다.
각 채널은 독립적으로 동작하며, 하나가 실패해도 나머지에 영향 없습니다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.timezone import now_kst


class NotificationChannel(Base):
    """알림 채널 설정 테이블.

    Attributes:
        id: 자동 증가 PK
        channel_type: 채널 종류 (telegram, discord, gmail)
        name: 사용자 지정 채널 이름 (예: "개인 텔레그램")
        config_json: 채널별 설정 JSON (토큰, 웹훅 URL 등)
        is_active: 활성화 여부
        last_success_at: 마지막 성공 전송 시각
        last_error: 마지막 에러 메시지
        created_at: 생성 시각
    """

    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    channel_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="telegram | discord | gmail"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    config_json: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="채널별 설정 JSON (토큰, 웹훅 URL 등)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationChannel(id={self.id}, type='{self.channel_type}', "
            f"name='{self.name}', active={self.is_active})>"
        )
