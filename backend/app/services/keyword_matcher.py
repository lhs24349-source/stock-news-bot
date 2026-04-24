"""
rapidfuzz 기반 키워드 매칭 엔진.

뉴스 제목/본문에서 키워드 그룹을 퍼지 매칭하며,
제외어가 포함된 기사를 자동으로 필터링합니다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from rapidfuzz import fuzz

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MatchResult:
    """키워드 매칭 결과."""

    group_name: str
    matched_keyword: str
    score: float
    matched_text: str


def normalize_text(text: str) -> str:
    """텍스트를 정규화합니다.
    1. 유니코드 정규화
    2. 소문자 변환
    3. 특수문자 제거
    4. 연속 공백 단일 공백 처리
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_exclude_keyword(
    text: str,
    exclude_keywords: list[str],
    threshold: float = 85.0,
) -> Optional[str]:
    """텍스트에 제외어가 포함되어 있는지 확인합니다."""
    normalized = normalize_text(text)

    for excl in exclude_keywords:
        excl_norm = normalize_text(excl)
        if not excl_norm:
            continue

        if excl_norm in normalized:
            return excl

        score = fuzz.partial_ratio(excl_norm, normalized)
        if score >= threshold:
            return excl

    return None


class KeywordMatcher:
    """키워드 매칭 엔진."""

    def match(
        self,
        text: str,
        keyword_groups: list[dict],
    ) -> list[MatchResult]:
        if not text or not keyword_groups:
            return []

        normalized = normalize_text(text)
        if not normalized:
            return []

        results: list[MatchResult] = []

        for group in keyword_groups:
            group_name = group.get("name", "")
            keywords = group.get("keywords", [])
            excludes = group.get("exclude_keywords", [])
            threshold = group.get("threshold", 85.0)

            excluded_by = _contains_exclude_keyword(text, excludes, threshold=threshold)
            if excluded_by:
                continue

            best_match = self._find_best_match(normalized, keywords, threshold)
            if best_match:
                results.append(
                    MatchResult(
                        group_name=group_name,
                        matched_keyword=best_match[0],
                        score=best_match[1],
                        matched_text=normalized,
                    )
                )

        return results

    def match_single(
        self,
        text: str,
        keywords: list[str],
        threshold: float = 85.0,
    ) -> Optional[MatchResult]:
        normalized = normalize_text(text)
        if not normalized:
            return None

        best_match = self._find_best_match(normalized, keywords, threshold)
        if best_match:
            return MatchResult(
                group_name="",
                matched_keyword=best_match[0],
                score=best_match[1],
                matched_text=normalized,
            )
        return None

    @staticmethod
    def _find_best_match(
        normalized_text: str,
        keywords: list[str],
        threshold: float,
    ) -> Optional[tuple[str, float]]:
        if not keywords:
            return None

        keyword_map = {}
        for kw in keywords:
            norm_kw = normalize_text(kw)
            if norm_kw:
                keyword_map[norm_kw] = kw

        if not keyword_map:
            return None

        for norm_kw, original_kw in keyword_map.items():
            if norm_kw in normalized_text:
                return (original_kw, 100.0)

        best_score = 0.0
        best_keyword = ""

        for norm_kw, original_kw in keyword_map.items():
            score = fuzz.partial_ratio(norm_kw, normalized_text)
            if score > best_score:
                best_score = score
                best_keyword = original_kw

        if best_score >= threshold:
            return (best_keyword, best_score)

        return None
