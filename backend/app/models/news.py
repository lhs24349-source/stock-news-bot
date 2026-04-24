"""
뉴스 데이터 모델.

수집된 뉴스 기사와 알림 발송 이력을 저장합니다.
3-tier 중복 제거의 핵심 데이터 소스입니다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.timezone import now_kst


class News(Base):
    """수집된 뉴스 기사 테이블.

    Attributes:
        id: 자동 증가 PK
        title: 기사 제목
        url: 기사 URL (유니크)
        url_hash: URL의 SHA-256 해시 (중복 체크 Tier 1용)
        source: 뉴스 소스 (naver, google, yahoo 등)
        summary: 기사 요약/본문 일부
        published_at: 기사 발행 시각
        keyword_group: 매칭된 키워드 그룹명
        matched_keyword: 실제 매칭된 키워드
        match_score: rapidfuzz 매칭 점수 (0~100)
        is_sent: 알림 발송 여부
        sent_at: 알림 발송 시각
        created_at: 레코드 생성 시각
    """

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    url_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    keyword_group: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    matched_keyword: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    match_score: Mapped[float | None] = mapped_column(nullable=True)
    is_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, nullable=False
    )

    # 복합 인덱스: 키워드 그룹 + 발행시간 기반 조회 최적화
    __table_args__ = (
        Index("ix_news_keyword_published", "keyword_group", "published_at"),
        Index("ix_news_source_created", "source", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<News(id={self.id}, title='{self.title[:30]}...', source='{self.source}')>"


class SentNewsCache(Base):
    """알림 발송 캐시 테이블 (Redis 폴백용).

    Redis 미설치 환경에서 중복 알림 방지를 위한 SQLite 기반 캐시입니다.
    TTL은 24시간이며, 주기적으로 만료된 레코드를 정리합니다.
    """

    __tablename__ = "sent_news_cache"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    # 캐시 키: url_hash 또는 keyword_group:url_hash
    cache_key: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )
    # 만료 시각 (KST 기준)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, nullable=False
    )

    def __repr__(self) -> str:
        return f"<SentNewsCache(key='{self.cache_key}', expires='{self.expires_at}')>"
