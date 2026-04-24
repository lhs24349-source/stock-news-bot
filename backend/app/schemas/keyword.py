"""키워드 그룹 관련 Pydantic 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KeywordGroupCreate(BaseModel):
    """키워드 그룹 생성 요청 스키마."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="그룹명 (예: 반도체)",
        examples=["반도체"],
    )
    keywords: list[str] = Field(
        ...,
        min_length=1,
        description="키워드 목록 (OR 로직)",
        examples=[["HBM", "메모리", "DRAM"]],
    )
    exclude_keywords: list[str] = Field(
        default_factory=list,
        description="제외어 목록",
        examples=[["광고", "프로모션"]],
    )
    threshold: float = Field(
        default=85.0,
        ge=0,
        le=100,
        description="rapidfuzz 매칭 임계값 (0~100)",
    )


class KeywordGroupUpdate(BaseModel):
    """키워드 그룹 수정 요청 스키마 (부분 업데이트)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    keywords: Optional[list[str]] = Field(None, min_length=1)
    exclude_keywords: Optional[list[str]] = None
    threshold: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class KeywordGroupResponse(BaseModel):
    """키워드 그룹 응답 스키마."""

    id: int
    name: str
    keywords: list[str]
    exclude_keywords: list[str]
    threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, model) -> "KeywordGroupResponse":
        """ORM 모델에서 응답 스키마로 변환.

        쉼표 구분 문자열을 리스트로 변환합니다.
        """
        return cls(
            id=model.id,
            name=model.name,
            keywords=model.keyword_list,
            exclude_keywords=model.exclude_keyword_list,
            threshold=model.threshold,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
