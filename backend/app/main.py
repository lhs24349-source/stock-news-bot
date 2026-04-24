"""
FastAPI 메인 엔트리포인트.

앱 생성, 라우터 등록, 미들웨어 설정, 라이프사이클 이벤트를 관리합니다.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리 (시작/종료)."""
    settings = get_settings()

    # ── 시작 시 초기화 ──
    setup_logging(
        log_level=settings.log_level,
        json_format=(settings.app_env != "development"),
    )
    logger = get_logger("main")
    logger.info(
        "앱 시작",
        app_name=settings.app_name,
        env=settings.app_env,
        debug=settings.debug,
    )

    # DB 테이블 자동 생성 (Alembic 미사용 시)
    await init_db()
    logger.info("데이터베이스 초기화 완료")

    # 스케줄러 시작
    from app.scheduler.engine import start_scheduler
    await start_scheduler()
    logger.info("스케줄러 시작 완료")

    # 설정된 알림 채널 정보 로그 (토큰은 마스킹)
    channels = []
    if settings.is_telegram_configured:
        channels.append("Telegram")
    if settings.is_discord_configured:
        channels.append("Discord")
    if settings.is_gmail_configured:
        channels.append("Gmail")
    logger.info(
        "알림 채널 상태",
        configured=channels if channels else ["없음 (API만 동작)"],
        redis="사용" if settings.is_redis_configured else "SQLite 폴백",
    )

    yield  # 앱 실행

    # ── 종료 시 정리 ──
    from app.scheduler.engine import shutdown_scheduler
    await shutdown_scheduler()
    await close_db()
    logger.info("앱 정상 종료")


def create_app() -> FastAPI:
    """FastAPI 앱 인스턴스를 생성합니다."""
    settings = get_settings()

    app = FastAPI(
        title="Stock News Bot API",
        description=(
            "주식 뉴스 수집 및 알림 서비스 API.\n\n"
            "키워드 기반 뉴스 수집, 매칭, 중복 제거, "
            "다채널 알림(Telegram/Discord/Gmail)을 제공합니다."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS 미들웨어 ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 라우터 등록 ──
    from app.api.routes.health import router as health_router
    from app.api.routes.news import router as news_router
    from app.api.routes.keywords import router as keywords_router
    from app.api.routes.channels import router as channels_router
    from app.api.routes.schedule import router as schedule_router
    from app.api.websocket import router as ws_router

    app.include_router(health_router)
    app.include_router(news_router)
    app.include_router(keywords_router)
    app.include_router(channels_router)
    app.include_router(schedule_router)
    app.include_router(ws_router)

    return app


# uvicorn이 이 인스턴스를 사용
app = create_app()
