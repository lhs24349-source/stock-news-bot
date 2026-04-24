"""
키워드 그룹 모델.

키워드 그룹(예: "반도체")과 소속 키워드(예: ["HBM", "메모리", "DRAM"]),
제외어(예: ["광고", "프로모션"])를 관리합니다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.timezone import now_kst


class KeywordGroup(Base):
    """키워드 그룹 테이블.

    하나의 그룹에 여러 키워드를 쉼표로 구분하여 저장합니다.
    OR 로직: 그룹 내 키워드 중 하나라도 매칭되면 해당 그룹의 뉴스로 분류됩니다.

    Attributes:
        id: 자동 증가 PK
        name: 그룹명 (예: "반도체", "양자컴퓨터")
        keywords: 쉼표 구분 키워드 목록 (예: "HBM,메모리,DRAM")
        exclude_keywords: 제외어 목록 (예: "광고,프로모션")
        threshold: rapidfuzz 매칭 임계값 (기본 85.0)
        is_active: 활성화 여부
        created_at: 생성 시각
        updated_at: 수정 시각
    """

    __tablename__ = "keyword_groups"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    keywords: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="쉼표 구분 키워드 목록 (예: HBM,메모리,DRAM)"
    )
    exclude_keywords: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="쉼표 구분 제외어 목록 (예: 광고,프로모션)"
    )
    threshold: Mapped[float] = mapped_column(
        Float, default=85.0, nullable=False,
        comment="rapidfuzz 매칭 임계값 (0~100)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_kst, onupdate=now_kst,
        nullable=False,
    )

    @property
    def keyword_list(self) -> list[str]:
        """쉼표 구분 키워드를 리스트로 반환."""
        return [k.strip() for k in self.keywords.split(",") if k.strip()]

    @property
    def exclude_keyword_list(self) -> list[str]:
        """쉼표 구분 제외어를 리스트로 반환."""
        if not self.exclude_keywords:
            return []
        return [
            k.strip()
            for k in self.exclude_keywords.split(",")
            if k.strip()
        ]

    def __repr__(self) -> str:
        return f"<KeywordGroup(id={self.id}, name='{self.name}', keywords='{self.keywords}')>"
