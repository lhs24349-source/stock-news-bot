"""알림 채널 관련 Pydantic 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    """알림 채널 생성 요청 스키마."""

    channel_type: str = Field(
        ...,
        pattern="^(telegram|discord|gmail)$",
        description="채널 종류: telegram | discord | gmail",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="채널 이름 (사용자 지정)",
        examples=["개인 텔레그램"],
    )
    config: dict = Field(
        ...,
        description=(
            "채널별 설정. "
            "telegram: {bot_token, chat_id}, "
            "discord: {webhook_url}, "
            "gmail: {address, app_password, recipients[]}"
        ),
    )


class ChannelUpdate(BaseModel):
    """알림 채널 수정 요청 스키마."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class ChannelResponse(BaseModel):
    """알림 채널 응답 스키마.

    보안: config에서 토큰/비밀번호는 마스킹 처리됩니다.
    """

    id: int
    channel_type: str
    name: str
    is_active: bool
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelTestRequest(BaseModel):
    """채널 연결 테스트 요청 스키마."""

    channel_id: int = Field(..., description="테스트할 채널 ID")
    test_message: str = Field(
        default="🔔 테스트 알림입니다. Stock News Bot이 정상 연결되었습니다!",
        description="테스트 메시지 내용",
    )


class ChannelTestResponse(BaseModel):
    """채널 연결 테스트 응답 스키마."""

    success: bool
    channel_type: str
    message: str
