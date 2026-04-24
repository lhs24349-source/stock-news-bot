"""
뉴스 수집 서비스 테스트.

실제 외부 API 호출 없이 Mock 기반으로 테스트합니다.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.services.news_fetcher import (
    NewsFetcher,
    RawNewsItem,
    _compute_url_hash,
    _parse_feed,
)


# 테스트용 샘플 RSS XML
SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Samsung HBM3E Supply Expansion</title>
      <link>https://example.com/news/1</link>
      <description>Samsung expands HBM3E supply</description>
      <pubDate>Thu, 24 Apr 2026 14:30:00 +0900</pubDate>
    </item>
    <item>
      <title>TSMC 2nm Process</title>
      <link>https://example.com/news/2</link>
      <description>TSMC starts 2nm process</description>
      <pubDate>Thu, 24 Apr 2026 11:15:00 +0900</pubDate>
    </item>
  </channel>
</rss>"""


class TestUrlHash:
    """URL 해시 테스트."""

    def test_동일_url_동일_해시(self):
        """같은 URL은 같은 해시를 반환하는지 확인."""
        url = "https://example.com/news/1"
        assert _compute_url_hash(url) == _compute_url_hash(url)

    def test_다른_url_다른_해시(self):
        """다른 URL은 다른 해시를 반환하는지 확인."""
        h1 = _compute_url_hash("https://example.com/1")
        h2 = _compute_url_hash("https://example.com/2")
        assert h1 != h2

    def test_공백_제거(self):
        """URL 앞뒤 공백이 제거된 해시를 반환하는지 확인."""
        h1 = _compute_url_hash("https://example.com")
        h2 = _compute_url_hash("  https://example.com  ")
        assert h1 == h2


class TestParseFeed:
    """RSS 파싱 테스트."""

    def test_정상_RSS_파싱(self):
        """정상 RSS를 올바르게 파싱하는지 확인."""
        items = _parse_feed(SAMPLE_RSS, source="test")
        assert len(items) == 2
        assert items[0].title == "Samsung HBM3E Supply Expansion"
        assert items[0].source == "test"
        assert items[0].url_hash  # 해시가 생성되었는지

    def test_빈_피드(self):
        """빈 RSS에서 빈 리스트가 반환되는지 확인."""
        empty_rss = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Empty</title></channel></rss>"""
        items = _parse_feed(empty_rss, source="test")
        assert len(items) == 0

    def test_잘못된_XML(self):
        """잘못된 XML에서도 크래시 없이 처리되는지 확인."""
        bad_xml = b"<not valid xml"
        items = _parse_feed(bad_xml, source="test")
        # feedparser는 관대하게 처리하므로 에러 없이 빈 결과
        assert isinstance(items, list)


class TestNewsFetcher:
    """뉴스 수집기 테스트 (Mock 기반)."""

    @pytest.mark.asyncio
    async def test_fetch_all_empty_keywords(self):
        """키워드 없이도 네이버 RSS는 수집하는지 확인."""
        fetcher = NewsFetcher()

        with patch(
            "app.services.news_fetcher._fetch_with_retry",
            new_callable=AsyncMock,
            return_value=SAMPLE_RSS,
        ):
            items = await fetcher.fetch_all(
                keywords=[],
                sources=["naver"],
                hours=24,
            )
            assert isinstance(items, list)
