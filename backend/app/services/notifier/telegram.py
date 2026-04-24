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
    """MarkdownV2 특수문자를 이스케이프합니다.

    Telegram MarkdownV2에서 이스케이프가 필요한 문자:
    _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


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

    async def send(self, message: NotificationMessage) -> bool:
        """Telegram으로 뉴스 알림을 전송합니다."""
        try:
            from telegram import Bot

            bot = Bot(token=self._bot_token)
            text = self.format_news_list(message)
            chunks = _split_message(text)

            for chunk in chunks:
                await bot.send_message(
                    chat_id=self._chat_id,
                    text=chunk,
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
