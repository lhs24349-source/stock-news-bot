"""
알림 채널 관리 API.

채널 CRUD + 연결 테스트 기능을 제공합니다.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.channel import NotificationChannel
from app.schemas.channel import (
    ChannelCreate,
    ChannelResponse,
    ChannelTestRequest,
    ChannelTestResponse,
    ChannelUpdate,
)

router = APIRouter(prefix="/api/channels", tags=["알림 채널"])


@router.get("", summary="채널 목록", response_model=list[ChannelResponse])
async def list_channels(
    db: AsyncSession = Depends(get_db),
) -> list[ChannelResponse]:
    """모든 알림 채널을 조회합니다."""
    stmt = select(NotificationChannel).order_by(
        NotificationChannel.created_at.desc()
    )
    result = await db.execute(stmt)
    return [
        ChannelResponse.model_validate(ch)
        for ch in result.scalars().all()
    ]


@router.post(
    "", summary="채널 생성", response_model=ChannelResponse, status_code=201
)
async def create_channel(
    body: ChannelCreate,
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    """새 알림 채널을 생성합니다."""
    channel = NotificationChannel(
        channel_type=body.channel_type,
        name=body.name,
        config_json=json.dumps(body.config, ensure_ascii=False),
    )
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return ChannelResponse.model_validate(channel)


@router.put("/{channel_id}", summary="채널 수정", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    body: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    """채널 설정을 수정합니다."""
    stmt = select(NotificationChannel).where(
        NotificationChannel.id == channel_id
    )
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    if body.name is not None:
        channel.name = body.name
    if body.config is not None:
        channel.config_json = json.dumps(body.config, ensure_ascii=False)
    if body.is_active is not None:
        channel.is_active = body.is_active

    await db.flush()
    await db.refresh(channel)
    return ChannelResponse.model_validate(channel)


@router.delete("/{channel_id}", summary="채널 삭제", status_code=204)
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """채널을 삭제합니다."""
    stmt = select(NotificationChannel).where(
        NotificationChannel.id == channel_id
    )
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    await db.delete(channel)


@router.post(
    "/test",
    summary="채널 연결 테스트",
    response_model=ChannelTestResponse,
)
async def test_channel(
    body: ChannelTestRequest,
    db: AsyncSession = Depends(get_db),
) -> ChannelTestResponse:
    """채널 연결 테스트 메시지를 전송합니다."""
    stmt = select(NotificationChannel).where(
        NotificationChannel.id == body.channel_id
    )
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    config = json.loads(channel.config_json)

    try:
        if channel.channel_type == "telegram":
            from app.services.notifier.telegram import TelegramNotifier
            notifier = TelegramNotifier(
                config["bot_token"], config["chat_id"]
            )
        elif channel.channel_type == "discord":
            from app.services.notifier.discord import DiscordNotifier
            notifier = DiscordNotifier(config["webhook_url"])
        elif channel.channel_type == "gmail":
            from app.services.notifier.gmail import GmailNotifier
            notifier = GmailNotifier(
                config["address"],
                config["app_password"],
                config.get("recipients", []),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 채널: {channel.channel_type}",
            )

        success = await notifier.send_test(body.test_message)
        return ChannelTestResponse(
            success=success,
            channel_type=channel.channel_type,
            message="테스트 전송 성공" if success else "테스트 전송 실패",
        )

    except HTTPException:
        raise
    except Exception as e:
        return ChannelTestResponse(
            success=False,
            channel_type=channel.channel_type,
            message=f"오류: {str(e)}",
        )
