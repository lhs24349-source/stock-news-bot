"""
Telegram 알림 채널.

MarkdownV2 포맷, 4096자 자동 분할을 지원합니다.
python-telegram-bot 라이브러리를 사용합니다.
"""

from __future__ import annotations

import re

from app.core.logging import get_logger
from app.services.notifier.base import BaseNotifier, NotificationMessage

logger = get_logger(__name__)

# Telegram 메시지 최대 길이
MAX_MESSAGE_LENGTH = 4096


def _escape_markdown_v2(text: str) -> str:
    """MarkdownV2 특수문자를 이스케이프합니다."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


def _escape_html(text: str) -> str:
    """HTML 특수문자를 이스케이프합니다."""
    import html
    return html.escape(text)


def _split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """긴 메시지를 최대 길이로 분할합니다.

    줄 단위로 분할하여 메시지가 잘리지 않도록 합니다.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks


class TelegramNotifier(BaseNotifier):
    """Telegram Bot API 알림 채널."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id

    @property
    def channel_type(self) -> str:
        return "telegram"

    def format_news_html(self, message: NotificationMessage, limit: int = 20) -> str:
        """뉴스 목록을 HTML로 포맷팅합니다. (링크 한 줄 축약)"""
        lines = []
        emoji = "📊" if "요약" in message.keyword_group else "📢"
        lines.append(f"<b>{emoji} [{_escape_html(message.keyword_group)}]</b>")
        
        if message.schedule_info:
            lines.append(f"⏱️ 스케줄: {_escape_html(message.schedule_info)}")
        if message.keywords_info:
            lines.append(f"🔑 키워드: {_escape_html(message.keywords_info)}")
        if message.time_range:
            lines.append(f"⏳ 시간: {_escape_html(message.time_range)}")
            
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━\n")
        
        articles = message.articles
        total_count = message.total_count or len(articles)
        
        for idx, article in enumerate(articles[:limit], 1):
            title = _escape_html(article.get("title", ""))
            time_str = _escape_html(article.get("time", ""))
            url = article.get("url", "")
            
            if url:
                lines.append(f"{idx}. {title} [{time_str}] <a href=\"{url}\">[🔗링크]</a>")
            else:
                lines.append(f"{idx}. {title} [{time_str}]")
            
        if total_count > limit:
            remaining = total_count - limit
            lines.append(f"\n...외 {remaining}건의 뉴스가 더 있습니다.")
            lines.append("전체 내역은 웹 페이지에서 스크롤하여 확인해주세요!")
            
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━")
        footer = f"📊 총 수집: {total_count}건"
        if message.next_alert_time:
            footer += f" | 다음 알림: {_escape_html(message.next_alert_time)}"
        lines.append(f"<i>{footer}</i>")

        return "\n".join(lines)

    async def send(self, message: NotificationMessage) -> bool:
        """Telegram으로 뉴스 알림을 전송합니다."""
        try:
            from telegram import Bot

            bot = Bot(token=self._bot_token)
            text = self.format_news_html(message)
            chunks = _split_message(text)

            for chunk in chunks:
                await bot.send_message(
                    chat_id=self._chat_id,
                    text=chunk,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

            logger.info(
                "Telegram 알림 전송 성공",
                group=message.keyword_group,
                chunks=len(chunks),
                articles=len(message.articles),
            )
            return True

        except Exception as e:
            logger.error("Telegram 알림 전송 실패", error=str(e))
            return False

    async def send_test(self, test_message: str) -> bool:
        """테스트 메시지를 Telegram으로 전송합니다."""
        try:
            from telegram import Bot

            bot = Bot(token=self._bot_token)
            await bot.send_message(
                chat_id=self._chat_id,
                text=test_message,
            )
            return True
        except Exception as e:
            logger.error("Telegram 테스트 전송 실패", error=str(e))
            return False

    async def health_check(self) -> dict:
        """Telegram 봇 연결 상태를 확인합니다."""
        try:
            from telegram import Bot

            bot = Bot(token=self._bot_token)
            me = await bot.get_me()
            return {
                "status": "ok",
                "detail": f"Bot: @{me.username}",
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}
