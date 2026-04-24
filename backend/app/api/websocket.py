"""
WebSocket 엔드포인트.

실시간 알림 전달을 위한 WebSocket 서버입니다.
"""

from __future__ import annotations

import asyncio
import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# 연결된 WebSocket 클라이언트 관리
_connected_clients: Set[WebSocket] = set()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket) -> None:
    """실시간 알림 WebSocket 엔드포인트.

    클라이언트가 연결하면 새 뉴스 알림을 실시간으로 수신합니다.
    """
    await websocket.accept()
    _connected_clients.add(websocket)

    logger.info(
        "WebSocket 클라이언트 연결",
        total_clients=len(_connected_clients),
    )

    try:
        while True:
            # 클라이언트로부터 ping 대기 (연결 유지)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _connected_clients.discard(websocket)
        logger.info(
            "WebSocket 클라이언트 연결 해제",
            total_clients=len(_connected_clients),
        )


async def broadcast_notification(data: dict) -> int:
    """모든 연결된 WebSocket 클라이언트에 알림을 브로드캐스트합니다.

    Args:
        data: 전송할 JSON 데이터

    Returns:
        성공적으로 전송된 클라이언트 수
    """
    if not _connected_clients:
        return 0

    message = json.dumps(data, ensure_ascii=False)
    sent = 0
    disconnected = set()

    for client in _connected_clients:
        try:
            await client.send_text(message)
            sent += 1
        except Exception:
            disconnected.add(client)

    # 끊어진 클라이언트 정리
    _connected_clients.difference_update(disconnected)

    return sent
