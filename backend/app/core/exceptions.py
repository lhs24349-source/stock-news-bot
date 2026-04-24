"""
커스텀 예외 클래스 정의.

모든 비즈니스 로직 예외를 구조화하여 FastAPI 에러 핸들러에서
일관된 응답을 반환할 수 있도록 합니다.
"""

from __future__ import annotations


class StockNewsBotError(Exception):
    """앱 최상위 예외 클래스."""

    def __init__(self, message: str = "알 수 없는 오류가 발생했습니다."):
        self.message = message
        super().__init__(self.message)


class NewsSourceError(StockNewsBotError):
    """뉴스 소스 접근/파싱 실패 시 발생하는 예외.

    예: RSS 서버 다운, XML 파싱 실패 등
    """

    def __init__(self, source: str, detail: str):
        self.source = source
        self.detail = detail
        super().__init__(f"[{source}] 뉴스 소스 오류: {detail}")


class KeywordMatchError(StockNewsBotError):
    """키워드 매칭 로직에서 발생하는 예외."""
    pass


class NotificationError(StockNewsBotError):
    """알림 전송 실패 시 발생하는 예외.

    한 채널의 실패가 다른 채널에 영향을 주지 않도록
    개별적으로 처리됩니다.
    """

    def __init__(self, channel: str, detail: str):
        self.channel = channel
        self.detail = detail
        super().__init__(f"[{channel}] 알림 전송 실패: {detail}")


class SchedulerError(StockNewsBotError):
    """스케줄러 작업 등록/실행 실패 시 발생하는 예외."""
    pass


class DeduplicationError(StockNewsBotError):
    """중복 제거 로직에서 발생하는 예외."""
    pass


class ConfigurationError(StockNewsBotError):
    """설정 누락 또는 잘못된 설정 시 발생하는 예외.

    명시적 설정 가이드를 포함합니다.
    """

    def __init__(self, config_key: str, guide: str):
        self.config_key = config_key
        self.guide = guide
        super().__init__(
            f"설정 오류 [{config_key}]: {guide}\n"
            f"→ .env.example 파일을 참고하여 .env에 값을 설정하세요."
        )
