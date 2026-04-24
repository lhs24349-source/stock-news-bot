"""스케줄 관련 Pydantic 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """스케줄 생성 요청 스키마."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="스케줄 이름",
        examples=["반도체 30분 간격"],
    )
    schedule_type: str = Field(
        ...,
        pattern="^(backfill|interval|digest|event)$",
        description="스케줄 종류: backfill | interval | digest | event",
    )
    config: dict = Field(
        ...,
        description=(
            "스케줄별 설정. "
            "backfill: {hours: 24}, "
            "interval: {minutes: 30}, "
            "digest: {cron: '0 9,18 * * *'}, "
            "event: {keywords: ['반도체'], immediate: true}"
        ),
    )
    keyword_group_ids: list[int] = Field(
        default_factory=list,
        description="대상 키워드 그룹 ID 목록",
    )


class ScheduleUpdate(BaseModel):
    """스케줄 수정 요청 스키마."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    config: Optional[dict] = None
    keyword_group_ids: Optional[list[int]] = None
    is_active: Optional[bool] = None


class ScheduleResponse(BaseModel):
    """스케줄 응답 스키마."""

    id: int
    name: str
    schedule_type: str
    config: dict
    keyword_group_ids: list[int]
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
