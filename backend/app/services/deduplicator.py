"""
3-tier 중복 제거 로직.

Tier 1: URL 해시 일치 → 즉시 스킵
Tier 2: 제목 유사도 ≥ 85% AND 발행시간 차이 ≤ 30분
Tier 3: 24시간 내 동일 키워드 그룹 + URL → 재알림 방지

Redis 우선, 미설치 시 SQLite 폴백.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Protocol

from rapidfuzz import fuzz

from app.core.logging import get_logger
from app.services.news_fetcher import RawNewsItem
from app.utils.timezone import now_kst

logger = get_logger(__name__)

# 중복 판정 상수
TITLE_SIMILARITY_THRESHOLD = 85.0
TIME_DIFF_THRESHOLD_MINUTES = 30
CACHE_TTL_HOURS = 24


class CacheBackend(Protocol):
    """캐시 백엔드 프로토콜 (Redis / SQLite 구현)."""

    async def exists(self, key: str) -> bool: ...
    async def set(self, key: str, ttl_seconds: int) -> None: ...
    async def close(self) -> None: ...


class RedisCacheBackend:
    """Redis 기반 캐시 백엔드."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def set(self, key: str, ttl_seconds: int) -> None:
        await self._redis.setex(key, ttl_seconds, "1")

    async def close(self) -> None:
        await self._redis.close()


class SqliteCacheBackend:
    """SQLite 기반 캐시 백엔드 (Redis 폴백)."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def exists(self, key: str) -> bool:
        from sqlalchemy import select
        from app.models.news import SentNewsCache

        async with self._session_factory() as session:
            stmt = select(SentNewsCache).where(
                SentNewsCache.cache_key == key,
                SentNewsCache.expires_at > now_kst(),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def set(self, key: str, ttl_seconds: int) -> None:
        from app.models.news import SentNewsCache

        expires = now_kst() + timedelta(seconds=ttl_seconds)
        async with self._session_factory() as session:
            # upsert 패턴
            from sqlalchemy import select
            stmt = select(SentNewsCache).where(
                SentNewsCache.cache_key == key
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.expires_at = expires
            else:
                session.add(SentNewsCache(
                    cache_key=key, expires_at=expires
                ))
            await session.commit()

    async def close(self) -> None:
        pass  # SQLite 세션은 별도 정리 불필요


class Deduplicator:
    """3-tier 중복 제거 엔진.

    사용 예:
        dedup = Deduplicator(cache_backend)
        is_dup = await dedup.is_duplicate(news_item, keyword_group="반도체")
    """

    def __init__(self, cache: CacheBackend) -> None:
        self._cache = cache
        # 최근 뉴스 캐시 (Tier 2 제목 비교용, 메모리)
        self._recent_titles: list[tuple[str, datetime]] = []

    async def is_duplicate(
        self,
        item: RawNewsItem,
        keyword_group: str = "",
    ) -> bool:
        """뉴스 아이템의 중복 여부를 3-tier로 검사합니다.

        Returns:
            True면 중복 (스킵해야 함)
        """
        # ── Tier 1: URL 해시 일치 ────────────────────────────
        cache_key_url = f"dedup:url:{item.url_hash}"
        if await self._cache.exists(cache_key_url):
            logger.debug("Tier1 중복: URL 해시 일치", url=item.url[:60])
            return True

        # ── Tier 2: 제목 유사도 + 시간 근접 ──────────────────
        if self._is_title_duplicate(item):
            logger.debug("Tier2 중복: 제목 유사", title=item.title[:40])
            return True

        # ── Tier 3: 키워드 그룹 + URL 재알림 방지 ────────────
        if keyword_group:
            cache_key_group = f"dedup:group:{keyword_group}:{item.url_hash}"
            if await self._cache.exists(cache_key_group):
                logger.debug(
                    "Tier3 중복: 동일 그룹 재알림",
                    group=keyword_group,
                    url=item.url[:60],
                )
                return True

        return False

    async def mark_sent(
        self,
        item: RawNewsItem,
        keyword_group: str = "",
    ) -> None:
        """뉴스 아이템을 발송 완료로 캐시에 기록합니다."""
        ttl = CACHE_TTL_HOURS * 3600  # 24시간

        # Tier 1 캐시
        await self._cache.set(f"dedup:url:{item.url_hash}", ttl)

        # Tier 3 캐시
        if keyword_group:
            await self._cache.set(
                f"dedup:group:{keyword_group}:{item.url_hash}", ttl
            )

        # Tier 2 메모리 캐시 업데이트
        pub_time = item.published_at or now_kst()
        self._recent_titles.append((item.title, pub_time))
        self._cleanup_old_titles()

    def _is_title_duplicate(self, item: RawNewsItem) -> bool:
        """Tier 2: 제목 유사도 + 시간 근접성 검사."""
        if not item.published_at:
            return False

        for cached_title, cached_time in self._recent_titles:
            # 시간 차이 확인 (30분 이내)
            time_diff = abs(
                (item.published_at - cached_time).total_seconds()
            )
            if time_diff > TIME_DIFF_THRESHOLD_MINUTES * 60:
                continue

            # 제목 유사도 확인 (85% 이상)
            similarity = fuzz.ratio(item.title, cached_title)
            if similarity >= TITLE_SIMILARITY_THRESHOLD:
                return True

        return False

    def _cleanup_old_titles(self) -> None:
        """24시간 지난 제목 캐시를 정리합니다."""
        cutoff = now_kst() - timedelta(hours=CACHE_TTL_HOURS)
        self._recent_titles = [
            (t, dt) for t, dt in self._recent_titles if dt > cutoff
        ]


async def create_deduplicator() -> Deduplicator:
    """설정에 따라 적절한 캐시 백엔드로 Deduplicator를 생성합니다."""
    from app.config import get_settings
    settings = get_settings()

    if settings.is_redis_configured:
        try:
            backend = RedisCacheBackend(settings.redis_url)
            logger.info("Redis 캐시 백엔드 사용")
            return Deduplicator(backend)
        except Exception as e:
            logger.warning("Redis 연결 실패, SQLite 폴백", error=str(e))

    # SQLite 폴백
    from app.database import get_session_factory
    backend = SqliteCacheBackend(get_session_factory())
    logger.info("SQLite 캐시 백엔드 사용 (Redis 폴백)")
    return Deduplicator(backend)
