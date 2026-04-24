"""
인코딩 자동 감지 유틸리티.

네이버 RSS 등 EUC-KR 인코딩 응답을 자동으로 감지하여
UTF-8로 변환합니다. chardet 라이브러리를 사용합니다.
"""

from __future__ import annotations

import chardet

from app.core.logging import get_logger

logger = get_logger(__name__)


def detect_and_decode(raw_bytes: bytes, fallback: str = "utf-8") -> str:
    """바이트 데이터의 인코딩을 자동 감지하여 문자열로 디코딩합니다.

    Args:
        raw_bytes: 디코딩할 원본 바이트 데이터
        fallback: 감지 실패 시 사용할 기본 인코딩

    Returns:
        디코딩된 문자열

    동작 과정:
        1. chardet로 인코딩 자동 감지
        2. 신뢰도 50% 이상이면 감지된 인코딩 사용
        3. 신뢰도 낮으면 fallback 인코딩으로 시도
        4. 모두 실패하면 errors='replace'로 강제 디코딩
    """
    if not raw_bytes:
        return ""

    # chardet으로 인코딩 자동 감지
    detected = chardet.detect(raw_bytes)
    encoding = detected.get("encoding", fallback)
    confidence = detected.get("confidence", 0.0)

    logger.debug(
        "인코딩 감지 완료",
        detected_encoding=encoding,
        confidence=f"{confidence:.2%}",
        data_size=len(raw_bytes),
    )

    # 신뢰도가 충분히 높으면 감지된 인코딩 사용
    if encoding and confidence >= 0.5:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            logger.warning(
                "감지된 인코딩으로 디코딩 실패, 폴백 시도",
                encoding=encoding,
                fallback=fallback,
            )

    # 폴백 인코딩으로 시도
    try:
        return raw_bytes.decode(fallback)
    except UnicodeDecodeError:
        logger.warning(
            "폴백 인코딩 실패, 강제 디코딩 (일부 문자 손실 가능)",
            fallback=fallback,
        )
        return raw_bytes.decode(fallback, errors="replace")
