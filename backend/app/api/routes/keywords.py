"""
키워드 그룹 관리 API.

키워드 그룹의 CRUD 및 제외어 설정을 제공합니다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.keyword import KeywordGroup
from app.schemas.keyword import (
    KeywordGroupCreate,
    KeywordGroupResponse,
    KeywordGroupUpdate,
)

router = APIRouter(prefix="/api/keywords", tags=["키워드"])


@router.get(
    "",
    summary="키워드 그룹 목록",
    response_model=list[KeywordGroupResponse],
)
async def list_keyword_groups(
    db: AsyncSession = Depends(get_db),
) -> list[KeywordGroupResponse]:
    """모든 키워드 그룹을 조회합니다."""
    stmt = select(KeywordGroup).order_by(KeywordGroup.created_at.desc())
    result = await db.execute(stmt)
    groups = result.scalars().all()
    return [KeywordGroupResponse.from_model(g) for g in groups]


@router.post(
    "",
    summary="키워드 그룹 생성",
    response_model=KeywordGroupResponse,
    status_code=201,
)
async def create_keyword_group(
    body: KeywordGroupCreate,
    db: AsyncSession = Depends(get_db),
) -> KeywordGroupResponse:
    """새 키워드 그룹을 생성합니다."""
    # 중복 이름 확인
    existing = await db.execute(
        select(KeywordGroup).where(KeywordGroup.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"'{body.name}' 이름의 그룹이 이미 존재합니다",
        )

    group = KeywordGroup(
        name=body.name,
        keywords=",".join(body.keywords),
        exclude_keywords=",".join(body.exclude_keywords) if body.exclude_keywords else None,
        threshold=body.threshold,
    )
    db.add(group)
    await db.flush()
    await db.refresh(group)

    return KeywordGroupResponse.from_model(group)


@router.put(
    "/{group_id}",
    summary="키워드 그룹 수정",
    response_model=KeywordGroupResponse,
)
async def update_keyword_group(
    group_id: int,
    body: KeywordGroupUpdate,
    db: AsyncSession = Depends(get_db),
) -> KeywordGroupResponse:
    """키워드 그룹을 수정합니다 (부분 업데이트)."""
    stmt = select(KeywordGroup).where(KeywordGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="키워드 그룹을 찾을 수 없습니다")

    if body.name is not None:
        group.name = body.name
    if body.keywords is not None:
        group.keywords = ",".join(body.keywords)
    if body.exclude_keywords is not None:
        group.exclude_keywords = ",".join(body.exclude_keywords)
    if body.threshold is not None:
        group.threshold = body.threshold
    if body.is_active is not None:
        group.is_active = body.is_active

    await db.flush()
    await db.refresh(group)

    return KeywordGroupResponse.from_model(group)


@router.delete(
    "/{group_id}",
    summary="키워드 그룹 삭제",
    status_code=204,
)
async def delete_keyword_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """키워드 그룹을 삭제합니다."""
    stmt = select(KeywordGroup).where(KeywordGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=404, detail="키워드 그룹을 찾을 수 없습니다")

    await db.delete(group)
