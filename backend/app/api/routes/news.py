"""
뉴스 API 라우트.

뉴스 조회, 백필 실행, 수동 수집 등의 엔드포인트를 제공합니다.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.news import News
from app.schemas.news import (
    BackfillRequest,
    NewsFetchResult,
    NewsListResponse,
    NewsResponse,
)

router = APIRouter(prefix="/api/news", tags=["뉴스"])


@router.get(
    "",
    summary="뉴스 목록 조회",
    response_model=NewsListResponse,
)
async def get_news(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    keyword_group: Optional[str] = Query(None, description="키워드 그룹 필터"),
    source: Optional[str] = Query(None, description="소스 필터"),
    search: Optional[str] = Query(None, description="제목 검색어"),
    sort: Optional[str] = Query("time_desc", description="정렬 방식 (time_desc, time_asc, title_asc, keyword_asc)"),
    db: AsyncSession = Depends(get_db),
) -> NewsListResponse:
    """수집된 뉴스 목록을 페이지네이션으로 조회합니다."""
    stmt = select(News)

    if keyword_group:
        stmt = stmt.where(News.keyword_group == keyword_group)
    if source:
        stmt = stmt.where(News.source == source)
    if search:
        stmt = stmt.where(News.title.contains(search))

    # 총 개수
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    # 페이지네이션
    if sort == "time_asc":
        stmt = stmt.order_by(News.published_at.asc().nulls_last(), News.created_at.asc())
    elif sort == "title_asc":
        stmt = stmt.order_by(News.title.asc())
    elif sort == "keyword_asc":
        stmt = stmt.order_by(News.keyword_group.asc(), News.published_at.desc().nulls_last(), News.created_at.desc())
    else:
        stmt = stmt.order_by(News.published_at.desc().nulls_last(), News.created_at.desc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    items = result.scalars().all()

    return NewsListResponse(
        items=[NewsResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/backfill",
    summary="즉시 백필 실행",
    description="최근 N시간 뉴스를 즉시 수집하고 알림을 전송합니다.",
    response_model=NewsFetchResult,
)
async def backfill(request: BackfillRequest) -> NewsFetchResult:
    """백필 작업을 즉시 실행합니다."""
    from app.scheduler.jobs import run_news_pipeline

    # 요청 키워드를 임시 그룹으로 구성
    keyword_groups = [{
        "name": "백필",
        "keywords": request.keywords,
        "exclude_keywords": [],
        "threshold": 85.0,
    }]

    result = await run_news_pipeline(
        keyword_groups=keyword_groups,
        hours=request.hours,
        send_notification=request.send_notification,
    )

    return NewsFetchResult(**result)


@router.get(
    "/{news_id}",
    summary="뉴스 상세 조회",
    response_model=NewsResponse,
)
async def get_news_detail(
    news_id: int,
    db: AsyncSession = Depends(get_db),
) -> NewsResponse:
    """특정 뉴스 기사의 상세 정보를 조회합니다."""
    from fastapi import HTTPException

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다")

    return NewsResponse.model_validate(news)
