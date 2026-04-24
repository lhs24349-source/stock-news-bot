"""
시간대 유틸리티.

앱 전체에서 Asia/Seoul 시간대를 일관되게 사용하도록 보장합니다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# 서울 시간대 (앱 전체에서 이 상수를 사용)
KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """현재 한국 시간(KST)을 반환합니다."""
    return datetime.now(tz=KST)


def to_kst(dt: datetime) -> datetime:
    """주어진 datetime을 KST로 변환합니다.

    timezone-naive인 경우 UTC로 가정합니다.
    """
    if dt.tzinfo is None:
        # timezone-naive → UTC로 가정 후 KST 변환
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)


def format_kst(dt: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """datetime을 KST 기준 포맷된 문자열로 반환합니다."""
    return to_kst(dt).strftime(fmt)
