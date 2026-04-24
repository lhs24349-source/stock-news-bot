"""
structlog 기반 구조화된 로깅 설정.

JSON 포맷으로 출력하며 Prometheus/ELK 연동에 적합합니다.
토큰 등 민감 정보는 자동으로 마스킹 처리됩니다.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


# 마스킹 대상 필드 목록 (로그에 노출되면 안 되는 값)
_SENSITIVE_KEYS = frozenset({
    "token",
    "password",
    "secret",
    "api_key",
    "bot_token",
    "app_password",
    "webhook_url",
    "authorization",
    "dsn",
})


def _mask_sensitive_data(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """로그 이벤트에서 민감한 데이터를 자동 마스킹합니다.

    _SENSITIVE_KEYS에 포함된 키의 값을 '****'로 대체합니다.
    """
    for key in event_dict:
        if any(s in key.lower() for s in _SENSITIVE_KEYS):
            value = event_dict[key]
            if isinstance(value, str) and len(value) > 8:
                event_dict[key] = f"{value[:4]}****{value[-3:]}"
            elif isinstance(value, str):
                event_dict[key] = "****"
    return event_dict


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """structlog 로깅을 초기화합니다.

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: True면 JSON 포맷, False면 개발자 친화적 포맷
    """
    # 공통 프로세서 (모든 출력 형식에 적용)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,      # 컨텍스트 변수 병합
        structlog.stdlib.add_log_level,               # 로그 레벨 추가
        structlog.stdlib.add_logger_name,             # 로거 이름 추가
        structlog.processors.TimeStamper(             # 타임스탬프 (ISO 8601)
            fmt="iso", utc=False
        ),
        structlog.processors.StackInfoRenderer(),     # 스택 정보
        _mask_sensitive_data,                         # 민감 정보 마스킹
    ]

    if json_format:
        # 운영 환경: JSON 포맷 (ELK/Grafana 연동)
        renderer = structlog.processors.JSONRenderer(
            ensure_ascii=False  # 한국어 유니코드 그대로 출력
        )
    else:
        # 개발 환경: 컬러 콘솔 출력
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 표준 라이브러리 logging과 연동
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 외부 라이브러리 로그 레벨 조정 (너무 시끄러운 것 억제)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """명명된 structlog 로거를 반환합니다.

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    사용 예:
        logger = get_logger(__name__)
        logger.info("뉴스 수집 시작", source="naver", keyword_count=5)
    """
    return structlog.get_logger(name)
