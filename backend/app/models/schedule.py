"""
스케줄 설정 모델.

4가지 스케줄 모드(Backfill, Interval, Digest, Event)의
설정을 저장합니다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.timezone import now_kst


class ScheduleConfig(Base):
    """스케줄 설정 테이블.

    Attributes:
        id: 자동 증가 PK
        name: 스케줄 이름 (예: "반도체 30분 간격")
        schedule_type: 스케줄 종류 (backfill, interval, digest, event)
        config_json: 스케줄별 설정 JSON
            - backfill: {"hours": 24}
            - interval: {"minutes": 30}
            - digest: {"cron": "0 9,18 * * *"}
            - event: {"keywords": ["반도체"], "immediate": true}
        keyword_group_ids: 대상 키워드 그룹 ID 목록 (쉼표 구분)
        is_active: 활성화 여부
        last_run_at: 마지막 실행 시각
        next_run_at: 다음 실행 예정 시각
        created_at: 생성 시각
    """

    __tablename__ = "schedule_configs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    schedule_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="backfill | interval | digest | event"
    )
    config_json: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="스케줄별 설정 JSON"
    )
    keyword_group_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="쉼표 구분 키워드 그룹 ID 목록"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ScheduleConfig(id={self.id}, name='{self.name}', "
            f"type='{self.schedule_type}', active={self.is_active})>"
        )
