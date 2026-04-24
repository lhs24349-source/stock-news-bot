"""
RSS 뉴스 수집 서비스.

네이버 금융, 구글 뉴스 RSS를 비동기로 수집하며,
3회 재시도 + exponential backoff + circuit breaker 패턴을 적용합니다.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from time import mktime
from typing import Optional

import feedparser
import httpx
import pybreaker

from app.config import get_settings
from app.core.exceptions import NewsSourceError
from app.core.logging import get_logger
from app.utils.encoding import detect_and_decode
from app.utils.timezone import KST, now_kst, to_kst

logger = get_logger(__name__)

# ── Circuit Breaker 설정 ─────────────────────────────────────
# 5번 연속 실패 시 30초간 차단 (fast-fail)
_naver_breaker = pybreaker.CircuitBreaker(
    fail_max=5, reset_timeout=30, name="naver_rss"
)
_google_breaker = pybreaker.CircuitBreaker(
    fail_max=5, reset_timeout=30, name="google_rss"
)


@dataclass
class RawNewsItem:
    """RSS에서 파싱된 원본 뉴스 아이템.

    아직 키워드 매칭이나 중복 체크가 적용되지 않은 상태입니다.
    """

    title: str
    url: str
    url_hash: str  # SHA-256 해시
    source: str  # naver, google, yahoo
    summary: str = ""
    published_at: Optional[datetime] = None
    raw_data: dict = field(default_factory=dict)  # 디버깅용 원본 데이터


def _compute_url_hash(url: str) -> str:
    """URL의 SHA-256 해시를 계산합니다 (중복 체크 Tier 1용)."""
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def _parse_published_date(entry: dict) -> Optional[datetime]:
    """feedparser 엔트리에서 발행 시각을 추출합니다.

    여러 필드를 순서대로 시도하여 가장 정확한 시각을 반환합니다.
    """
    for date_field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(date_field)
        if parsed:
            try:
                dt = datetime.fromtimestamp(mktime(parsed))
                return to_kst(dt)
            except (ValueError, OverflowError, OSError):
                continue

    # 문자열 형태로 시도
    for str_field in ("published", "updated"):
        date_str = entry.get(str_field, "")
        if date_str:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                return to_kst(dt)
            except (ValueError, TypeError):
                continue

    return None


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> bytes:
    """HTTP GET 요청을 exponential backoff으로 재시도합니다.

    Args:
        client: httpx 비동기 클라이언트
        url: 요청 URL
        max_retries: 최대 재시도 횟수 (기본 3)
        base_delay: 초기 대기 시간 (1s → 2s → 4s)

    Returns:
        응답 바이트 데이터

    Raises:
        NewsSourceError: 모든 재시도 실패 시
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            return response.content
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "HTTP 요청 실패, 재시도 예정",
                    url=url,
                    attempt=attempt,
                    max_retries=max_retries,
                    delay=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)

    raise NewsSourceError(
        source=url,
        detail=f"{max_retries}회 재시도 모두 실패: {last_error}",
    )


def _parse_feed(raw_content: bytes, source: str) -> list[RawNewsItem]:
    """feedparser로 RSS 피드를 파싱하여 RawNewsItem 리스트로 변환합니다.

    인코딩 감지를 자동으로 수행합니다.
    """
    # chardet으로 인코딩 감지 후 디코딩
    text = detect_and_decode(raw_content)

    feed = feedparser.parse(text)

    if feed.bozo and not feed.entries:
        logger.warning(
            "feedparser 파싱 경고",
            source=source,
            bozo_exception=str(feed.bozo_exception) if feed.bozo_exception else "unknown",
        )

    items: list[RawNewsItem] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        if not title or not link:
            continue

        # 요약 추출 (여러 필드 시도)
        summary = ""
        if entry.get("summary"):
            summary = entry["summary"]
        elif entry.get("description"):
            summary = entry["description"]

        # HTML 태그 간단 제거
        import re
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        # 200자로 제한
        if len(summary) > 200:
            summary = summary[:197] + "..."

        items.append(
            RawNewsItem(
                title=title,
                url=link,
                url_hash=_compute_url_hash(link),
                source=source,
                summary=summary,
                published_at=_parse_published_date(entry),
                raw_data={"title": title, "link": link},
            )
        )

    logger.info(
        "RSS 피드 파싱 완료",
        source=source,
        total_entries=len(feed.entries),
        parsed_items=len(items),
    )
    return items


class NewsFetcher:
    """뉴스 수집 서비스.

    여러 RSS 소스에서 비동기로 뉴스를 수집합니다.
    소스별 최소 10초 간격 rate limiting을 적용합니다.

    사용 예:
        fetcher = NewsFetcher()
        items = await fetcher.fetch_all(keywords=["반도체", "HBM"])
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        # 소스별 마지막 요청 시각 (rate limiting용)
        self._last_fetch: dict[str, datetime] = {}
        # 소스별 최소 간격 (초)
        self._min_interval = 10.0

    async def _rate_limit(self, source: str) -> None:
        """소스별 rate limiting을 적용합니다 (최소 10초 간격)."""
        now = now_kst()
        last = self._last_fetch.get(source)
        if last:
            elapsed = (now - last).total_seconds()
            if elapsed < self._min_interval:
                wait = self._min_interval - elapsed
                logger.debug(
                    "Rate limit 대기",
                    source=source,
                    wait_seconds=round(wait, 1),
                )
                await asyncio.sleep(wait)
        self._last_fetch[source] = now_kst()

    @_naver_breaker
    async def fetch_naver(
        self,
        client: httpx.AsyncClient,
    ) -> list[RawNewsItem]:
        """네이버 금융 RSS에서 뉴스를 수집합니다.

        EUC-KR 인코딩을 자동 처리합니다.
        """
        await self._rate_limit("naver")
        url = self._settings.naver_rss_url

        logger.info("네이버 RSS 수집 시작", url=url)
        raw = await _fetch_with_retry(client, url)
        return _parse_feed(raw, source="naver")

    @_google_breaker
    async def fetch_google(
        self,
        client: httpx.AsyncClient,
        keyword: str,
    ) -> list[RawNewsItem]:
        """구글 뉴스 RSS에서 키워드 기반 뉴스를 수집합니다."""
        await self._rate_limit("google")
        url = self._settings.google_news_rss_url.format(keyword=keyword)

        logger.info("구글 뉴스 RSS 수집 시작", keyword=keyword, url=url)
        raw = await _fetch_with_retry(client, url)
        return _parse_feed(raw, source="google")

    async def fetch_all(
        self,
        keywords: list[str] | None = None,
        sources: list[str] | None = None,
        hours: int = 24,
    ) -> list[RawNewsItem]:
        """모든 설정된 소스에서 뉴스를 수집합니다.

        Args:
            keywords: 검색 키워드 목록 (구글 뉴스에서 사용)
            sources: 수집할 소스 목록 (기본: naver, google)
            hours: 최근 N시간 이내 뉴스만 수집

        Returns:
            수집된 뉴스 아이템 리스트 (중복 체크 전)
        """
        if sources is None:
            sources = ["naver", "google"]
        if keywords is None:
            keywords = []

        cutoff_time = now_kst() - timedelta(hours=hours)
        all_items: list[RawNewsItem] = []
        errors: list[str] = []

        async with httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "StockNewsBot/1.0"
                ),
            },
            follow_redirects=True,
        ) as client:
            # 네이버 RSS 수집
            if "naver" in sources:
                try:
                    items = await self.fetch_naver(client)
                    all_items.extend(items)
                except (NewsSourceError, pybreaker.CircuitBreakerError) as e:
                    logger.error("네이버 RSS 수집 실패", error=str(e))
                    errors.append(f"naver: {e}")

            # 구글 뉴스 RSS 수집 (키워드별)
            if "google" in sources and keywords:
                for kw in keywords:
                    try:
                        items = await self.fetch_google(client, kw)
                        all_items.extend(items)
                    except (
                        NewsSourceError,
                        pybreaker.CircuitBreakerError,
                    ) as e:
                        logger.error(
                            "구글 뉴스 수집 실패",
                            keyword=kw,
                            error=str(e),
                        )
                        errors.append(f"google({kw}): {e}")

        # 시간 필터링: cutoff_time 이후 기사만 유지
        filtered = []
        for item in all_items:
            if item.published_at and item.published_at < cutoff_time:
                continue
            filtered.append(item)

        logger.info(
            "전체 뉴스 수집 완료",
            total_raw=len(all_items),
            after_time_filter=len(filtered),
            errors_count=len(errors),
        )

        return filtered
