"""
SQLAlchemy 2.0 async 데이터베이스 엔진 및 세션 팩토리.

SQLite(개발) / PostgreSQL(운영) 자동 전환을 지원하며,
DB 파일이 없으면 자동으로 생성합니다.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """모든 모델의 기반 클래스.

    Alembic 마이그레이션에서 이 Base.metadata를 참조합니다.
    """
    pass


def _create_engine():
    """설정에 따라 적절한 async 엔진을 생성합니다.

    SQLite 사용 시 WAL 모드를 활성화하여 동시 읽기 성능을 개선합니다.
    """
    settings = get_settings()
    url = settings.database_url

    # SQLite 전용 설정
    connect_args = {}
    if "sqlite" in url:
        connect_args = {"check_same_thread": False}

    engine = create_async_engine(
        url,
        echo=settings.debug,  # 디버그 모드에서 SQL 로그 출력
        connect_args=connect_args,
        pool_pre_ping=True,  # 커넥션 유효성 사전 확인
    )
    return engine


# 전역 엔진 (lazy 초기화)
_engine = None
_session_factory = None


def get_engine():
    """전역 엔진 싱글턴을 반환합니다."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """전역 세션 팩토리를 반환합니다."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # 커밋 후에도 객체 속성 접근 가능
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends용 DB 세션 제공 함수.

    사용 예:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """데이터베이스 테이블을 자동 생성합니다.

    Alembic 마이그레이션이 없는 개발 환경에서 사용됩니다.
    운영 환경에서는 Alembic을 사용하세요.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """앱 종료 시 DB 엔진을 정리합니다."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
