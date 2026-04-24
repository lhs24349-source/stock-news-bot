"""
Discord Webhook 알림 채널.

Rich Embed (키워드 그룹별 컬러)를 지원하며,
429 Rate Limit 시 Retry-After 헤더를 준수합니다.
"""

from __future__ import annotations

import asyncio

import httpx

from app.core.logging import get_logger
from app.services.notifier.base import BaseNotifier, NotificationMessage

logger = get_logger(__name__)

# 키워드 그룹별 Embed 컬러 팔레트 (Discord decimal color)
_GROUP_COLORS = [
    0x5865F2,  # 블루 (Discord Blurple)
    0xED4245,  # 레드
    0xFEE75C,  # 옐로우
    0x57F287,  # 그린
    0xEB459E,  # 핑크
    0xF47B67,  # 오렌지
    0x9B59B6,  # 퍼플
]


class DiscordNotifier(BaseNotifier):
    """Discord Webhook 알림 채널."""

    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    @property
    def channel_type(self) -> str:
        return "discord"

    async def send(self, message: NotificationMessage) -> bool:
        """Discord로 Rich Embed 알림을 전송합니다."""
        try:
            # 키워드 그룹명 해시로 일관된 컬러 선택
            color_idx = hash(message.keyword_group) % len(_GROUP_COLORS)
            color = _GROUP_COLORS[color_idx]

            # Embed 필드 구성
            fields = []
            for article in message.articles[:25]:  # Discord 필드 최대 25개
                title = article.get("title", "")[:256]
                time_str = article.get("time", "")
                url = article.get("url", "")
                value = f"🕐 {time_str}"
                if url:
                    value += f"\n🔗 [링크]({url})"
                fields.append({
                    "name": title,
                    "value": value,
                    "inline": False,
                })

            embed = {
                "title": f"📢 [{message.keyword_group}] 뉴스 알림",
                "description": f"수집 기간: {message.time_range}",
                "color": color,
                "fields": fields,
                "footer": {
                    "text": (
                        f"📊 총 {message.total_count}건"
                        + (f" | 다음 알림: {message.next_alert_time}"
                           if message.next_alert_time else "")
                    ),
                },
            }

            payload = {"embeds": [embed]}
            success = await self._send_webhook(payload)

            if success:
                logger.info(
                    "Discord 알림 전송 성공",
                    group=message.keyword_group,
                    articles=len(message.articles),
                )
            return success

        except Exception as e:
            logger.error("Discord 알림 전송 실패", error=str(e))
            return False

    async def send_test(self, test_message: str) -> bool:
        """테스트 메시지를 Discord로 전송합니다."""
        payload = {
            "content": test_message,
            "username": "Stock News Bot",
        }
        return await self._send_webhook(payload)

    async def health_check(self) -> dict:
        """Discord 웹훅 URL 유효성을 확인합니다."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self._webhook_url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": "ok",
                        "detail": f"Webhook: {data.get('name', 'unknown')}",
                    }
                return {
                    "status": "error",
                    "detail": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    async def _send_webhook(
        self, payload: dict, max_retries: int = 3
    ) -> bool:
        """Discord 웹훅으로 페이로드를 전송합니다.

        429 Rate Limit 시 Retry-After 헤더를 준수합니다.
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(1, max_retries + 1):
                try:
                    resp = await client.post(
                        self._webhook_url,
                        json=payload,
                        timeout=15.0,
                    )
                    if resp.status_code in (200, 204):
                        return True

                    # Rate limit 처리
                    if resp.status_code == 429:
                        retry_after = float(
                            resp.headers.get("Retry-After", "5")
                        )
                        logger.warning(
                            "Discord rate limit, 대기 중",
                            retry_after=retry_after,
                            attempt=attempt,
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    logger.error(
                        "Discord 웹훅 응답 오류",
                        status=resp.status_code,
                        body=resp.text[:200],
                    )
                    return False

                except httpx.RequestError as e:
                    logger.error(
                        "Discord 웹훅 요청 실패",
                        error=str(e),
                        attempt=attempt,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt)

        return False
