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


@router.get(
    "/dashboard",
    summary="대시보드 요약",
    description="키워드 그룹, 스케줄, 최근 뉴스 통계를 한 번에 반환합니다.",
)
async def dashboard_summary() -> dict:
    """프론트엔드 대시보드에 표시할 전체 현황 요약 데이터를 반환합니다."""
    import json
    from datetime import timedelta

    from sqlalchemy import func, select

    from app.database import get_session_factory
    from app.models.keyword import KeywordGroup
    from app.models.news import News
    from app.models.schedule import ScheduleConfig
    from app.utils.timezone import now_kst

    factory = get_session_factory()
    now = now_kst()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with factory() as session:
        # ── 키워드 그룹 요약 ──
        kg_result = await session.execute(
            select(KeywordGroup).where(KeywordGroup.is_active.is_(True))
        )
        keyword_groups_raw = kg_result.scalars().all()
        keyword_groups = []
        for kg in keyword_groups_raw:
            keyword_groups.append({
                "id": kg.id,
                "name": kg.name,
                "keywords": kg.keyword_list,
                "exclude_keywords": kg.exclude_keyword_list,
            })

        # ── 스케줄 요약 ──
        sc_result = await session.execute(
            select(ScheduleConfig).order_by(ScheduleConfig.created_at.desc())
        )
        schedules_raw = sc_result.scalars().all()
        schedules = []
        for sc in schedules_raw:
            schedules.append({
                "id": sc.id,
                "name": sc.name,
                "schedule_type": sc.schedule_type,
                "config": json.loads(sc.config_json),
                "is_active": sc.is_active,
                "last_run_at": str(sc.last_run_at) if sc.last_run_at else None,
            })

        # ── 뉴스 통계 ──
        total_news = await session.scalar(select(func.count(News.id))) or 0
        today_news = await session.scalar(
            select(func.count(News.id)).where(News.created_at >= today_start)
        ) or 0
        recent_24h = await session.scalar(
            select(func.count(News.id)).where(
                News.created_at >= now - timedelta(hours=24)
            )
        ) or 0

    settings = get_settings()
    channels_configured = []
    if settings.is_telegram_configured:
        channels_configured.append("Telegram")
    if settings.is_discord_configured:
        channels_configured.append("Discord")
    if settings.is_gmail_configured:
        channels_configured.append("Gmail")

    return {
        "keyword_groups": keyword_groups,
        "keyword_groups_count": len(keyword_groups),
        "schedules": schedules,
        "schedules_count": len(schedules),
        "news_stats": {
            "total": total_news,
            "today": today_news,
            "recent_24h": recent_24h,
        },
        "channels_configured": channels_configured,
    }
