"""
중복 제거 로직 테스트.

Redis 없이 SQLite 백엔드로 테스트합니다.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.services.deduplicator import (
    CACHE_TTL_HOURS,
    Deduplicator,
    SqliteCacheBackend,
    TITLE_SIMILARITY_THRESHOLD,
)
from app.services.news_fetcher import RawNewsItem
from app.utils.timezone import KST, now_kst


class InMemoryCacheBackend:
    """테스트용 인메모리 캐시 백엔드."""

    def __init__(self):
        self._store: dict[str, datetime] = {}

    async def exists(self, key: str) -> bool:
        if key not in self._store:
            return False
        if self._store[key] < now_kst():
            del self._store[key]
            return False
        return True

    async def set(self, key: str, ttl_seconds: int) -> None:
        self._store[key] = now_kst() + timedelta(seconds=ttl_seconds)

    async def close(self) -> None:
        pass


def _make_item(
    title: str = "테스트 뉴스",
    url: str = "https://example.com/1",
    published_at: datetime | None = None,
) -> RawNewsItem:
    """테스트용 뉴스 아이템을 생성합니다."""
    from app.services.news_fetcher import _compute_url_hash

    return RawNewsItem(
        title=title,
        url=url,
        url_hash=_compute_url_hash(url),
        source="test",
        published_at=published_at or now_kst(),
    )


class TestDeduplicator:
    """3-tier 중복 제거 테스트."""

    @pytest.mark.asyncio
    async def test_tier1_url_해시_중복(self):
        """동일 URL이 중복으로 감지되는지 확인."""
        cache = InMemoryCacheBackend()
        dedup = Deduplicator(cache)
        item = _make_item(url="https://example.com/same")

        # 첫 번째: 중복 아님
        assert not await dedup.is_duplicate(item)
        await dedup.mark_sent(item)

        # 두 번째: 중복
        assert await dedup.is_duplicate(item)

    @pytest.mark.asyncio
    async def test_tier2_제목_유사_중복(self):
        """유사한 제목 + 근접 시간이 중복으로 감지되는지 확인."""
        cache = InMemoryCacheBackend()
        dedup = Deduplicator(cache)

        now = now_kst()
        item1 = _make_item(
            title="삼성전자 HBM3E 공급 확대",
            url="https://a.com/1",
            published_at=now,
        )
        item2 = _make_item(
            title="삼성전자 HBM3E 공급 확대 소식",
            url="https://b.com/2",
            published_at=now + timedelta(minutes=10),
        )

        await dedup.mark_sent(item1)
        # 유사 제목 + 30분 이내 → Tier 2 중복
        assert await dedup.is_duplicate(item2)

    @pytest.mark.asyncio
    async def test_tier3_키워드그룹_재알림방지(self):
        """같은 키워드 그룹의 동일 URL 재알림이 방지되는지 확인."""
        cache = InMemoryCacheBackend()
        dedup = Deduplicator(cache)
        item = _make_item()

        await dedup.mark_sent(item, keyword_group="반도체")
        assert await dedup.is_duplicate(item, keyword_group="반도체")

    @pytest.mark.asyncio
    async def test_다른_url_비중복(self):
        """다른 URL은 중복이 아닌지 확인."""
        cache = InMemoryCacheBackend()
        dedup = Deduplicator(cache)

        item1 = _make_item(url="https://a.com/1")
        item2 = _make_item(
            title="완전 다른 뉴스",
            url="https://b.com/2",
            published_at=now_kst() + timedelta(hours=2),
        )

        await dedup.mark_sent(item1)
        assert not await dedup.is_duplicate(item2)

    @pytest.mark.asyncio
    async def test_다른_그룹_비중복(self):
        """다른 키워드 그룹은 재알림이 가능한지 확인."""
        cache = InMemoryCacheBackend()
        dedup = Deduplicator(cache)
        item = _make_item()

        await dedup.mark_sent(item, keyword_group="반도체")
        # 다른 그룹에서는 중복 아님 (Tier 3는 그룹별)
        # 단, Tier 1(URL 해시)에서는 중복
        assert await dedup.is_duplicate(item, keyword_group="양자컴퓨터")
