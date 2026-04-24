"""
스케줄 작업 정의.

실제로 스케줄러가 실행하는 비즈니스 로직을 담당합니다.
뉴스 수집 → 키워드 매칭 → 중복 체크 → 알림 전송 파이프라인.
"""

from __future__ import annotations

from datetime import timedelta

from app.core.logging import get_logger
from app.database import get_session_factory
from app.services.deduplicator import create_deduplicator
from app.services.keyword_matcher import KeywordMatcher
from app.services.news_fetcher import NewsFetcher
from app.services.notifier.base import NotificationMessage
from app.utils.timezone import format_kst, now_kst

logger = get_logger(__name__)


async def run_news_pipeline(
    keyword_groups: list[dict] | None = None,
    hours: int = 24,
    send_notification: bool = True,
) -> dict:
    """뉴스 수집 → 매칭 → 중복체크 → 알림 전체 파이프라인을 실행합니다.

    Args:
        keyword_groups: 키워드 그룹 설정 리스트
        hours: 수집 범위 (최근 N시간)
        send_notification: 알림 발송 여부

    Returns:
        실행 결과 딕셔너리
    """
    from sqlalchemy import select
    from app.models.keyword import KeywordGroup as KGModel
    from app.models.news import News

    result = {
        "total_fetched": 0,
        "new_articles": 0,
        "duplicates_skipped": 0,
        "notifications_sent": 0,
        "errors": [],
    }

    try:
        # 1. 키워드 그룹 로드 (파라미터 없으면 DB에서)
        if not keyword_groups:
            keyword_groups = await _load_keyword_groups()

        if not keyword_groups:
            logger.warning("활성화된 키워드 그룹이 없습니다")
            return result

        # 모든 키워드를 평탄화하여 RSS 검색에 사용
        all_keywords = []
        for group in keyword_groups:
            all_keywords.extend(group.get("keywords", []))

        # 2. 뉴스 수집
        fetcher = NewsFetcher()
        raw_items = await fetcher.fetch_all(
            keywords=all_keywords,
            hours=hours,
        )
        result["total_fetched"] = len(raw_items)

        if not raw_items:
            logger.info("수집된 뉴스가 없습니다")
            return result

        # 3. 중복 체크 + 키워드 매칭
        dedup = await create_deduplicator()
        matcher = KeywordMatcher()
        matched_news: dict[str, list] = {}  # group_name → articles

        for item in raw_items:
            # 키워드 매칭
            matches = matcher.match(
                text=f"{item.title} {item.summary}",
                keyword_groups=keyword_groups,
            )

            if not matches:
                continue

            for match in matches:
                # 중복 체크
                is_dup = await dedup.is_duplicate(
                    item, keyword_group=match.group_name
                )
                if is_dup:
                    result["duplicates_skipped"] += 1
                    continue

                # 신규 기사 DB 저장
                await _save_news(item, match)
                await dedup.mark_sent(item, keyword_group=match.group_name)

                result["new_articles"] += 1

                # 그룹별로 모아두기
                if match.group_name not in matched_news:
                    matched_news[match.group_name] = []
                matched_news[match.group_name].append({
                    "title": item.title,
                    "url": item.url,
                    "time": format_kst(item.published_at) if item.published_at else "",
                })

        # 4. 알림 전송 (그룹별)
        if send_notification and matched_news:
            now = now_kst()
            start_time = now - timedelta(hours=hours)
            time_range = f"{format_kst(start_time)}~{format_kst(now)}"

            for group_name, articles in matched_news.items():
                msg = NotificationMessage(
                    keyword_group=group_name,
                    articles=articles,
                    time_range=time_range,
                    total_count=len(articles),
                )
                sent = await _send_to_all_channels(msg)
                result["notifications_sent"] += sent

        logger.info("뉴스 파이프라인 완료", **result)

    except Exception as e:
        logger.error("뉴스 파이프라인 오류", error=str(e))
        result["errors"].append(str(e))

    return result


async def run_digest_pipeline(
    hours: int = 24,
) -> dict:
    """DB에 저장된 최근 N시간의 뉴스를 읽어와 요약 알림을 발송합니다."""
    from sqlalchemy import select
    from datetime import timedelta
    from app.models.news import News
    from app.database import get_session_factory
    
    result = {"total_summarized": 0, "notifications_sent": 0}
    now = now_kst()
    start_time = now - timedelta(hours=hours)
    
    factory = get_session_factory()
    async with factory() as session:
        stmt = select(News).where(News.published_at >= start_time).order_by(News.published_at.desc())
        news_result = await session.execute(stmt)
        recent_news = news_result.scalars().all()

    if not recent_news:
        logger.info("요약할 뉴스가 없습니다")
        return result

    # 키워드 그룹별로 분류
    matched_news: dict[str, list] = {}
    for item in recent_news:
        if not item.keyword_group:
            continue
        if item.keyword_group not in matched_news:
            matched_news[item.keyword_group] = []
        
        matched_news[item.keyword_group].append({
            "title": item.title,
            "url": item.url,
            "time": format_kst(item.published_at) if item.published_at else "",
        })

    # 알림 발송
    time_range = f"{format_kst(start_time)}~{format_kst(now)} 요약"
    for group_name, articles in matched_news.items():
        msg = NotificationMessage(
            keyword_group=f"📊 {group_name} (일일 요약)",
            articles=articles,
            time_range=time_range,
            total_count=len(articles),
        )
        sent = await _send_to_all_channels(msg)
        result["notifications_sent"] += sent
        result["total_summarized"] += len(articles)

    logger.info("요약 알림 파이프라인 완료", **result)
    return result


async def _load_keyword_groups() -> list[dict]:
    """DB에서 활성화된 키워드 그룹을 로드합니다."""
    from sqlalchemy import select
    from app.models.keyword import KeywordGroup

    factory = get_session_factory()
    async with factory() as session:
        stmt = select(KeywordGroup).where(KeywordGroup.is_active.is_(True))
        result = await session.execute(stmt)
        groups = result.scalars().all()

        return [
            {
                "name": g.name,
                "keywords": g.keyword_list,
                "exclude_keywords": g.exclude_keyword_list,
                "threshold": g.threshold,
            }
            for g in groups
        ]


async def _save_news(item, match) -> None:
    """뉴스 아이템을 DB에 저장합니다."""
    from app.models.news import News

    factory = get_session_factory()
    async with factory() as session:
        news = News(
            title=item.title,
            url=item.url,
            url_hash=item.url_hash,
            source=item.source,
            summary=item.summary,
            published_at=item.published_at,
            keyword_group=match.group_name,
            matched_keyword=match.matched_keyword,
            match_score=match.score,
        )
        session.add(news)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            # URL 해시 유니크 위반은 중복이므로 무시
            pass


async def _send_to_all_channels(message: NotificationMessage) -> int:
    """모든 활성 채널로 알림을 전송합니다 (실패 격리)."""
    from app.config import get_settings

    settings = get_settings()
    sent_count = 0

    # Telegram
    if settings.is_telegram_configured:
        try:
            from app.services.notifier.telegram import TelegramNotifier
            notifier = TelegramNotifier(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
            )
            if await notifier.send(message):
                sent_count += 1
        except Exception as e:
            logger.error("Telegram 전송 실패 (격리됨)", error=str(e))

    # Discord
    if settings.is_discord_configured:
        try:
            from app.services.notifier.discord import DiscordNotifier
            notifier = DiscordNotifier(settings.discord_webhook_url)
            if await notifier.send(message):
                sent_count += 1
        except Exception as e:
            logger.error("Discord 전송 실패 (격리됨)", error=str(e))

    # Gmail
    if settings.is_gmail_configured:
        try:
            from app.services.notifier.gmail import GmailNotifier
            notifier = GmailNotifier(
                settings.gmail_address,
                settings.gmail_app_password,
                settings.gmail_recipient_list,
            )
            if await notifier.send(message):
                sent_count += 1
        except Exception as e:
            logger.error("Gmail 전송 실패 (격리됨)", error=str(e))

    return sent_count
