"""
키워드 매칭 엔진 테스트.

실제 외부 API 호출 없이 순수 로직만 테스트합니다.
"""

from __future__ import annotations

import pytest

from app.services.keyword_matcher import (
    KeywordMatcher,
    MatchResult,
    normalize_text,
)


class TestNormalizeText:
    """텍스트 정규화 테스트."""

    def test_한글_영문_정규화(self):
        """한글/영문 혼합 텍스트가 올바르게 정규화되는지 확인."""
        result = normalize_text("삼성전자  HBM3E !!")
        assert result == "삼성전자 hbm3e"

    def test_특수문자_제거(self):
        """특수문자가 제거되는지 확인."""
        result = normalize_text("[속보] 주가 급등!! #투자")
        assert "속보" in result
        assert "주가" in result
        assert "급등" in result

    def test_빈_문자열(self):
        """빈 문자열 처리를 확인."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_연속_공백_처리(self):
        """연속 공백이 단일 공백으로 변환되는지 확인."""
        result = normalize_text("삼성    전자    HBM")
        assert "  " not in result


class TestKeywordMatcher:
    """키워드 매칭 엔진 테스트."""

    def setup_method(self):
        """각 테스트 전 매처 인스턴스를 생성합니다."""
        self.matcher = KeywordMatcher()
        self.keyword_groups = [
            {
                "name": "반도체",
                "keywords": ["HBM", "메모리", "DRAM", "반도체"],
                "exclude_keywords": ["광고", "프로모션"],
                "threshold": 85.0,
            },
            {
                "name": "양자컴퓨터",
                "keywords": ["양자", "큐비트", "quantum"],
                "exclude_keywords": [],
                "threshold": 85.0,
            },
        ]

    def test_정확한_키워드_매칭(self):
        """정확한 키워드가 포함된 텍스트가 매칭되는지 확인."""
        results = self.matcher.match(
            "삼성전자 HBM3E 공급 확대 소식",
            self.keyword_groups,
        )
        assert len(results) >= 1
        assert any(r.group_name == "반도체" for r in results)

    def test_제외어_필터링(self):
        """제외어가 포함된 텍스트가 필터링되는지 확인."""
        results = self.matcher.match(
            "반도체 관련 광고 프로모션 안내",
            self.keyword_groups,
        )
        # 반도체 그룹은 제외어 때문에 매칭 안 됨
        assert not any(r.group_name == "반도체" for r in results)

    def test_OR_로직_매칭(self):
        """그룹 내 키워드 하나라도 매칭되면 포함되는지 확인."""
        results = self.matcher.match(
            "DRAM 가격 상승세 지속",
            self.keyword_groups,
        )
        assert len(results) >= 1
        assert results[0].group_name == "반도체"

    def test_매칭_없음(self):
        """관련 없는 텍스트에서 매칭이 없는지 확인."""
        results = self.matcher.match(
            "오늘의 날씨는 맑음입니다",
            self.keyword_groups,
        )
        assert len(results) == 0

    def test_빈_입력(self):
        """빈 텍스트/그룹에서 빈 결과가 나오는지 확인."""
        assert self.matcher.match("", self.keyword_groups) == []
        assert self.matcher.match("테스트", []) == []

    def test_다중_그룹_매칭(self):
        """하나의 텍스트가 여러 그룹에 매칭되는지 확인."""
        results = self.matcher.match(
            "양자컴퓨터 기반 반도체 설계 혁신",
            self.keyword_groups,
        )
        group_names = {r.group_name for r in results}
        assert "반도체" in group_names
        assert "양자컴퓨터" in group_names

    def test_match_single(self):
        """단일 키워드 매칭이 올바르게 동작하는지 확인."""
        result = self.matcher.match_single(
            "HBM 메모리 공급 부족",
            ["HBM", "DRAM"],
            threshold=85.0,
        )
        assert result is not None
        assert result.score >= 85.0

    def test_유사도_임계값(self):
        """임계값 미만의 매칭이 무시되는지 확인."""
        result = self.matcher.match_single(
            "완전 다른 텍스트",
            ["HBM"],
            threshold=85.0,
        )
        assert result is None
