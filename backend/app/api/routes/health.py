"""
헬스 체크 API.

DB, Redis, 알림 채널 상태를 한 번에 확인합니다.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["시스템"])


@router.get(
    "/health",
    summary="헬스 체크",
    description="DB, Redis, 알림 채널의 상태를 확인합니다.",
    response_model=dict,
)
async def health_check() -> dict:
    """시스템 전체 헬스 체크를 수행합니다."""
    settings = get_settings()
    status = {
        "status": "ok",
        "db": "unknown",
        "redis": "not_configured",
        "channels": {},
    }

    # DB 체크
    try:
        from app.database import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        status["db"] = "ok"
    except Exception as e:
        status["db"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    # Redis 체크
    if settings.is_redis_configured:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.close()
            status["redis"] = "ok"
        except Exception as e:
            status["redis"] = f"error: {str(e)[:100]}"

    # 알림 채널 상태
    if settings.is_telegram_configured:
        status["channels"]["telegram"] = "configured"
    if settings.is_discord_configured:
        status["channels"]["discord"] = "configured"
    if settings.is_gmail_configured:
        status["channels"]["gmail"] = "configured"

    if not status["channels"]:
        status["channels"]["_info"] = "알림 채널 미설정 (API는 정상 동작)"

    return status


@router.get(
    "/metrics",
    summary="메트릭",
    description="간단한 시스템 메트릭을 반환합니다.",
)
async def metrics() -> dict:
    """간단한 시스템 메트릭을 반환합니다."""
    from app.database import get_session_factory
    from sqlalchemy import func, select
    from app.models.news import News
    from app.models.keyword import KeywordGroup

    factory = get_session_factory()
    async with factory() as session:
        # 전체 뉴스 수
        news_count = await session.scalar(select(func.count(News.id)))
        # 발송된 뉴스 수
        sent_count = await session.scalar(
            select(func.count(News.id)).where(News.is_sent.is_(True))
        )
        # 키워드 그룹 수
        group_count = await session.scalar(
            select(func.count(KeywordGroup.id))
        )

    return {
        "total_news": news_count or 0,
        "sent_notifications": sent_count or 0,
        "keyword_groups": group_count or 0,
    }
