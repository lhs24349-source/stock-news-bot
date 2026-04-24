"""
알림 채널 테스트 (Mock 기반).

실제 외부 API 호출 없이 알림 로직을 검증합니다.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notifier.base import NotificationMessage
from app.services.notifier.telegram import (
    TelegramNotifier,
    _escape_markdown_v2,
    _split_message,
)


class TestTelegramUtils:
    """Telegram 유틸리티 함수 테스트."""

    def test_MarkdownV2_이스케이프(self):
        """특수문자가 올바르게 이스케이프되는지 확인."""
        result = _escape_markdown_v2("test_value [link](url)")
        assert "\\_" in result
        assert "\\[" in result

    def test_메시지_분할_짧은메시지(self):
        """짧은 메시지는 분할되지 않는지 확인."""
        chunks = _split_message("짧은 메시지", max_length=4096)
        assert len(chunks) == 1

    def test_메시지_분할_긴메시지(self):
        """긴 메시지가 올바르게 분할되는지 확인."""
        long_text = "\n".join([f"뉴스 {i}" for i in range(1000)])
        chunks = _split_message(long_text, max_length=100)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100


class TestNotificationMessage:
    """알림 메시지 포맷 테스트."""

    def test_뉴스_목록_포맷(self):
        """뉴스 목록이 올바른 포맷으로 변환되는지 확인."""
        from app.services.notifier.telegram import TelegramNotifier

        msg = NotificationMessage(
            keyword_group="반도체",
            articles=[
                {"title": "HBM3E 공급 확대", "time": "14:32", "url": "https://ex.com/1"},
                {"title": "TSMC 2나노", "time": "11:15", "url": "https://ex.com/2"},
            ],
            time_range="09:00~18:00",
            total_count=2,
            next_alert_time="18:00",
        )

        notifier = TelegramNotifier("fake_token", "fake_id")
        text = notifier.format_news_list(msg)

        assert "반도체" in text
        assert "HBM3E" in text
        assert "총 2건" in text
        assert "18:00" in text


class TestTelegramNotifier:
    """Telegram 알림 채널 테스트 (Mock)."""

    @pytest.mark.asyncio
    async def test_send_test_성공(self):
        """테스트 메시지 전송이 성공하는지 확인 (Mock)."""
        notifier = TelegramNotifier("fake_token", "fake_chat_id")

        mock_bot = AsyncMock()
        with patch("telegram.Bot", return_value=mock_bot):
            mock_bot.send_message = AsyncMock()
            result = await notifier.send_test("테스트 메시지")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_test_실패(self):
        """전송 실패 시 False를 반환하는지 확인."""
        notifier = TelegramNotifier("bad_token", "bad_id")

        with patch(
            "telegram.Bot",
            side_effect=Exception("Invalid token"),
        ):
            result = await notifier.send_test("테스트")
            assert result is False


class TestDiscordNotifier:
    """Discord 알림 채널 테스트 (Mock)."""

    @pytest.mark.asyncio
    async def test_send_test_성공(self):
        from app.services.notifier.discord import DiscordNotifier
        notifier = DiscordNotifier("fake_url")
        with patch("httpx.AsyncClient.post", return_value=MagicMock(status_code=204)):
            result = await notifier.send_test("test")
            assert result is True


class TestGmailNotifier:
    """Gmail 알림 채널 테스트 (Mock)."""

    @pytest.mark.asyncio
    async def test_send_test_성공(self):
        from app.services.notifier.gmail import GmailNotifier
        notifier = GmailNotifier("a@a.com", "pass", ["b@b.com"])
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await notifier.send_test("test")
            assert result is True
            mock_send.assert_called_once()
