"""
알림 채널 기반 클래스 (Strategy 패턴).

모든 알림 채널(Telegram, Discord, Gmail)은
이 BaseNotifier를 상속하여 구현합니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NotificationMessage:
    """알림 메시지 데이터.

    Attributes:
        keyword_group: 키워드 그룹명 (예: "반도체")
        articles: 뉴스 기사 리스트
        time_range: 수집 시간 범위 문자열
        total_count: 총 기사 수
        next_alert_time: 다음 알림 예정 시각
    """

    keyword_group: str
    articles: list[dict] = field(default_factory=list)
    time_range: str = ""
    total_count: int = 0
    next_alert_time: Optional[str] = None


class BaseNotifier(ABC):
    """알림 채널 기반 클래스.

    Strategy 패턴: 채널별 구현체를 교체 가능합니다.
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """채널 종류 (telegram, discord, gmail)."""
        ...

    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """알림을 전송합니다.

        Returns:
            성공 여부
        """
        ...

    @abstractmethod
    async def send_test(self, test_message: str) -> bool:
        """테스트 메시지를 전송합니다."""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """채널 상태를 확인합니다.

        Returns:
            {"status": "ok"|"error", "detail": "..."}
        """
        ...

    def format_news_list(self, message: NotificationMessage) -> str:
        """뉴스 목록을 기본 텍스트 포맷으로 변환합니다.

        각 채널에서 오버라이드하여 채널별 포맷을 적용할 수 있습니다.
        """
        lines = []
        emoji = "📢" if message.keyword_group else "📰"
        lines.append(
            f"{emoji} [{message.keyword_group}] 뉴스 "
            f"({message.time_range})"
        )

        for article in message.articles:
            title = article.get("title", "")
            time_str = article.get("time", "")
            url = article.get("url", "")
            lines.append(f"• {title} - {time_str}")
            if url:
                lines.append(f"  🔗 {url}")

        lines.append("")
        lines.append("━" * 20)
        count = message.total_count or len(message.articles)
        footer = f"📊 총 {count}건"
        if message.next_alert_time:
            footer += f" | 다음 알림: {message.next_alert_time}"
        lines.append(footer)

        return "\n".join(lines)
