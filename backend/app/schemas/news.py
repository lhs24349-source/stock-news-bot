"""뉴스 관련 Pydantic 스키마 (요청/응답 DTO)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class NewsResponse(BaseModel):
    """뉴스 기사 응답 스키마."""

    id: int
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    keyword_group: Optional[str] = None
    matched_keyword: Optional[str] = None
    match_score: Optional[float] = None
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    """뉴스 목록 응답 스키마 (페이지네이션 포함)."""

    items: list[NewsResponse]
    total: int
    page: int = 1
    page_size: int = 20


class BackfillRequest(BaseModel):
    """백필 요청 스키마 (즉시 1회 실행)."""

    keywords: list[str] = Field(
        ...,
        description="검색할 키워드 목록",
        min_length=1,
        examples=[["반도체", "HBM"]],
    )
    hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="최근 N시간 이내 뉴스 수집 (1~168시간)",
    )
    sources: list[str] = Field(
        default=["naver", "google"],
        description="수집할 소스 목록",
    )
    send_notification: bool = Field(
        default=True,
        description="알림 발송 여부",
    )


class NewsFetchResult(BaseModel):
    """뉴스 수집 결과 스키마."""

    total_fetched: int = Field(description="총 수집된 뉴스 수")
    new_articles: int = Field(description="신규 기사 수 (중복 제외)")
    duplicates_skipped: int = Field(description="중복으로 건너뛴 수")
    notifications_sent: int = Field(description="발송된 알림 수")
    errors: list[str] = Field(default_factory=list, description="발생한 오류 목록")
